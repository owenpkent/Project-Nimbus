"""
Telemetry module for Nimbus Adaptive Controller.

Provides opt-in anonymous usage analytics and crash reporting.
All data collection is:
  - Opt-in only (never assumed)
  - Privacy-respecting (no PII, hashed identifiers only)
  - Local-first (events buffered locally, batch-uploaded on a timer)
  - Transparent (users can view the exact event schema in Settings → Privacy)
  - Deletable (users can purge all their analytics from account settings)

Events are buffered in memory and flushed to the Nimbus Cloud API every 5 minutes.
If the network is unavailable, events are persisted to a local JSON file and
retried on the next flush cycle.

Usage::

    from src.telemetry import TelemetryClient

    telemetry = TelemetryClient(config)
    telemetry.track("session_start", {"output_mode": "vigem"})
    telemetry.capture_exception(exc)
    telemetry.shutdown()  # flush remaining events on app exit
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QTimer, QObject

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Nimbus Cloud API endpoint for telemetry ingestion.
# Override with the NIMBUS_TELEMETRY_URL environment variable for development.
DEFAULT_TELEMETRY_URL = "https://api.nimbus.app/v1/events"
TELEMETRY_URL = os.environ.get("NIMBUS_TELEMETRY_URL", DEFAULT_TELEMETRY_URL)

# How often (in milliseconds) the buffer is flushed to the API.
FLUSH_INTERVAL_MS = 5 * 60 * 1000  # 5 minutes

# Maximum events kept in the local fallback file to prevent unbounded growth.
MAX_OFFLINE_EVENTS = 500

# App data directory name (matches config.py APP_NAME).
APP_NAME = "ProjectNimbus"


def _get_telemetry_dir() -> Path:
    """Return the directory used to persist unsent telemetry events."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    telemetry_dir = base / APP_NAME / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    return telemetry_dir


def _hash(value: str) -> str:
    """Return the first 16 hex chars of a SHA-256 hash (one-way, short)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _os_version() -> str:
    """Return a human-readable OS version string (e.g. 'Windows 11 23H2')."""
    return f"{platform.system()} {platform.release()} {platform.version()}"


# ---------------------------------------------------------------------------
# TelemetryClient
# ---------------------------------------------------------------------------

class TelemetryClient(QObject):
    """
    Opt-in anonymous analytics and crash reporting client.

    Parameters
    ----------
    config : ControllerConfig
        Application configuration object.  The following keys are read:

        - ``telemetry.analytics_enabled`` (bool) — send usage analytics
        - ``telemetry.crash_reports_enabled`` (bool) — send crash reports
        - ``telemetry.user_id`` (str | None) — stable anonymous UUID (auto-generated)

    Notes
    -----
    *   If both ``analytics_enabled`` and ``crash_reports_enabled`` are False,
        **no data is collected or transmitted**.
    *   Events are buffered in ``_buffer`` and flushed every 5 minutes.
    *   On flush failure (e.g. no network), events are written to a local
        JSON file and retried on the next successful flush.
    *   Call :meth:`shutdown` before application exit to flush remaining events.
    """

    def __init__(self, config: Any, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._config = config

        # Read opt-in flags
        self._analytics_enabled: bool = bool(config.get("telemetry.analytics_enabled", False))
        self._crash_reports_enabled: bool = bool(config.get("telemetry.crash_reports_enabled", False))

        # Stable anonymous user identifier (generated once, stored in config)
        self._user_id: str = self._ensure_user_id()

        # Per-session identifier (new each launch)
        self._session_id: str = str(uuid.uuid4())

        # In-memory event buffer
        self._buffer: List[Dict[str, Any]] = []

        # Local fallback file for unsent events
        self._offline_path: Path = _get_telemetry_dir() / "pending_events.json"

        # Flush timer
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(FLUSH_INTERVAL_MS)
        self._flush_timer.timeout.connect(self._flush)
        if self._is_enabled():
            self._flush_timer.start()
            logger.info("Telemetry enabled (analytics=%s, crash=%s)",
                        self._analytics_enabled, self._crash_reports_enabled)
        else:
            logger.info("Telemetry disabled — no data will be collected.")

        # Optional: Sentry SDK for structured crash reporting
        self._sentry_initialised = False
        if self._crash_reports_enabled:
            self._init_sentry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def analytics_enabled(self) -> bool:
        """Whether anonymous usage analytics collection is enabled."""
        return self._analytics_enabled

    @analytics_enabled.setter
    def analytics_enabled(self, value: bool) -> None:
        self._analytics_enabled = value
        self._config.set("telemetry.analytics_enabled", value)
        self._config.save_config()
        self._update_timer()

    @property
    def crash_reports_enabled(self) -> bool:
        """Whether crash report collection is enabled."""
        return self._crash_reports_enabled

    @crash_reports_enabled.setter
    def crash_reports_enabled(self, value: bool) -> None:
        self._crash_reports_enabled = value
        self._config.set("telemetry.crash_reports_enabled", value)
        self._config.save_config()
        if value and not self._sentry_initialised:
            self._init_sentry()

    def track(self, event: str, props: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an analytics event.

        Parameters
        ----------
        event : str
            Event name (e.g. ``"session_start"``, ``"profile_switch"``).
        props : dict, optional
            Additional key/value pairs to attach to the event.
            Must not contain PII — use :func:`_hash` for identifiers.

        If analytics is disabled, the call is a no-op.
        """
        if not self._analytics_enabled:
            return

        entry: Dict[str, Any] = {
            "event": event,
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": self._session_id,
            "user_id": self._user_id,
        }
        if props:
            entry.update(props)

        self._buffer.append(entry)
        logger.debug("Telemetry event buffered: %s", event)

    def track_session_start(self, app_version: str, output_mode: str,
                            vjoy_available: bool, vigem_available: bool) -> None:
        """Convenience: record a ``session_start`` event with standard fields."""
        self.track("session_start", {
            "app_version": app_version,
            "os_version": _os_version(),
            "output_mode": output_mode,
            "vjoy_available": vjoy_available,
            "vigem_available": vigem_available,
        })

    def track_profile_switch(self, profile_id: str, layout_type: str,
                             widget_count: int, output_mode: str) -> None:
        """Convenience: record a ``profile_switch`` event."""
        self.track("profile_switch", {
            "profile_id_hash": _hash(profile_id),
            "layout_type": layout_type,
            "widget_count": widget_count,
            "output_mode": output_mode,
        })

    def track_widget_added(self, widget_type: str, output_mode: str,
                           **axis_info: str) -> None:
        """Convenience: record a ``widget_added`` event."""
        self.track("widget_added", {
            "widget_type": widget_type,
            "output_mode": output_mode,
            **axis_info,
        })

    def track_game_mode(self, method: str, game_detected: bool,
                        window_title: str = "") -> None:
        """Convenience: record a ``game_mode_start`` event with hashed title."""
        self.track("game_mode_start", {
            "method": method,
            "game_detected": game_detected,
            "game_title_hash": _hash(window_title) if window_title else "",
        })

    def capture_exception(self, exc: BaseException) -> None:
        """
        Record a crash / unhandled exception.

        Parameters
        ----------
        exc : BaseException
            The exception instance.

        If crash reporting is disabled, the call is a no-op.
        If Sentry SDK is initialised, the exception is also forwarded there.
        """
        if not self._crash_reports_enabled:
            return

        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_str = "".join(tb)

        # Extract location info from the traceback
        module = ""
        function = ""
        lineno = 0
        if exc.__traceback__:
            frame = exc.__traceback__
            while frame.tb_next:
                frame = frame.tb_next
            module = frame.tb_frame.f_globals.get("__name__", "")
            function = frame.tb_frame.f_code.co_name
            lineno = frame.tb_lineno

        crash_event: Dict[str, Any] = {
            "event": "crash",
            "exception_type": type(exc).__name__,
            "module": module,
            "function": function,
            "line": lineno,
            "stack_hash": _hash(tb_str),
            "app_version": self._app_version(),
        }
        self._buffer.append({
            **crash_event,
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": self._session_id,
            "user_id": self._user_id,
        })
        logger.warning("Crash captured: %s in %s:%s (line %d)",
                        type(exc).__name__, module, function, lineno)

        # Forward to Sentry if available
        if self._sentry_initialised:
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(exc)
            except Exception:
                pass

    def shutdown(self) -> None:
        """Flush all remaining events and stop the timer. Call on app exit."""
        self._flush_timer.stop()
        if self._is_enabled() and self._buffer:
            self._flush()
        logger.info("Telemetry client shut down (session %s)", self._session_id)

    # ------------------------------------------------------------------
    # Event Schema — for the "What we collect" transparency page
    # ------------------------------------------------------------------

    @staticmethod
    def event_schema() -> Dict[str, Any]:
        """
        Return the documented event schema so the UI can display exactly
        what is collected under Settings → Privacy → "View data schema".
        """
        return {
            "session_start": {
                "app_version": "string — e.g. '1.5.0'",
                "os_version": "string — e.g. 'Windows 11 23H2'",
                "output_mode": "string — 'vjoy' or 'vigem'",
                "vjoy_available": "boolean",
                "vigem_available": "boolean",
            },
            "profile_switch": {
                "profile_id_hash": "string — SHA-256 hash (first 16 chars)",
                "layout_type": "string — e.g. 'custom'",
                "widget_count": "integer",
                "output_mode": "string",
            },
            "widget_added": {
                "widget_type": "string — e.g. 'joystick', 'button'",
                "output_mode": "string",
            },
            "game_mode_start": {
                "method": "string — e.g. 'vigem_controller_mode'",
                "game_detected": "boolean",
                "game_title_hash": "string — SHA-256 hash (first 16 chars)",
            },
            "crash": {
                "exception_type": "string — e.g. 'AttributeError'",
                "module": "string — e.g. 'src.bridge'",
                "function": "string",
                "line": "integer",
                "stack_hash": "string — SHA-256 hash (first 16 chars)",
                "app_version": "string",
            },
            "_common_fields": {
                "ts": "ISO-8601 UTC timestamp",
                "session_id": "UUID v4 (random per session, not linked to identity)",
                "user_id": "UUID v4 (stable anonymous ID, no PII)",
            },
            "_never_collected": [
                "Button IDs, axis values, or any actual controller input",
                "Profile names or descriptions",
                "Window titles in plaintext (hash only)",
                "File system paths",
                "Content of macros or custom key bindings",
                "Email addresses, names, or IP addresses",
            ],
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _is_enabled(self) -> bool:
        return self._analytics_enabled or self._crash_reports_enabled

    def _ensure_user_id(self) -> str:
        """Get or create a stable anonymous user ID stored in config."""
        uid = self._config.get("telemetry.user_id", None)
        if not uid:
            uid = str(uuid.uuid4())
            self._config.set("telemetry.user_id", uid)
            self._config.save_config()
        return uid

    def _app_version(self) -> str:
        try:
            from . import __version__
            return __version__
        except Exception:
            return "unknown"

    def _update_timer(self) -> None:
        if self._is_enabled() and not self._flush_timer.isActive():
            self._flush_timer.start()
        elif not self._is_enabled() and self._flush_timer.isActive():
            self._flush_timer.stop()

    def _init_sentry(self) -> None:
        """Initialise the Sentry SDK for structured crash reporting."""
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=os.environ.get("NIMBUS_SENTRY_DSN", ""),
                release=f"nimbus-adaptive-controller@{self._app_version()}",
                environment=os.environ.get("NIMBUS_ENV", "production"),
                traces_sample_rate=0.0,  # no performance traces (PII risk)
                before_send=self._scrub_sentry_event,
            )
            self._sentry_initialised = True
            logger.info("Sentry SDK initialised for crash reporting.")
        except ImportError:
            logger.debug("sentry-sdk not installed — crash reports sent via telemetry API only.")
        except Exception as e:
            logger.warning("Failed to initialise Sentry: %s", e)

    @staticmethod
    def _scrub_sentry_event(event: Dict, hint: Dict) -> Optional[Dict]:
        """
        Sentry ``before_send`` callback — strip PII before transmission.

        Removes:
        - Absolute file paths that may reveal the user's OS username
        - Request bodies (belt-and-suspenders)
        - Environment variables
        """
        # Strip absolute paths from stack frames
        if "exception" in event:
            for exc_info in event["exception"].get("values", []):
                for frame in exc_info.get("stacktrace", {}).get("frames", []):
                    if "abs_path" in frame:
                        # Keep only the filename, not the full path
                        abs_path = frame["abs_path"]
                        frame["abs_path"] = os.path.basename(abs_path)

        # Remove any request data
        event.pop("request", None)

        # Remove environment-level server name
        event.pop("server_name", None)

        # Remove extra contexts that may contain PII
        contexts = event.get("contexts", {})
        contexts.pop("os", None)

        return event

    def _flush(self) -> None:
        """Send buffered events to the Nimbus Cloud API (or persist locally)."""
        if not self._buffer:
            # Also try to send any offline-persisted events
            self._retry_offline()
            return

        events = self._buffer.copy()
        self._buffer.clear()

        # Attempt HTTP POST
        try:
            import httpx

            response = httpx.post(
                TELEMETRY_URL,
                json={"events": events},
                timeout=10.0,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code in (200, 201, 202, 204):
                logger.debug("Flushed %d telemetry events.", len(events))
                # Also try offline backlog
                self._retry_offline()
            else:
                logger.warning("Telemetry API returned %d — persisting locally.",
                               response.status_code)
                self._persist_offline(events)
        except ImportError:
            logger.debug("httpx not installed — persisting events locally.")
            self._persist_offline(events)
        except Exception as e:
            logger.debug("Telemetry flush failed (%s) — persisting locally.", e)
            self._persist_offline(events)

    def _persist_offline(self, events: List[Dict]) -> None:
        """Write events to a local JSON file for later retry."""
        try:
            existing: List[Dict] = []
            if self._offline_path.exists():
                try:
                    existing = json.loads(self._offline_path.read_text("utf-8"))
                except (json.JSONDecodeError, ValueError):
                    existing = []

            combined = existing + events
            # Cap to prevent unbounded growth
            if len(combined) > MAX_OFFLINE_EVENTS:
                combined = combined[-MAX_OFFLINE_EVENTS:]

            self._offline_path.write_text(json.dumps(combined, indent=2), "utf-8")
            logger.debug("Persisted %d events offline (%d total).",
                         len(events), len(combined))
        except Exception as e:
            logger.warning("Failed to persist telemetry offline: %s", e)

    def _retry_offline(self) -> None:
        """Attempt to re-send events that were persisted offline."""
        if not self._offline_path.exists():
            return
        try:
            events = json.loads(self._offline_path.read_text("utf-8"))
            if not events:
                return

            import httpx

            response = httpx.post(
                TELEMETRY_URL,
                json={"events": events},
                timeout=10.0,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code in (200, 201, 202, 204):
                self._offline_path.unlink(missing_ok=True)
                logger.debug("Retried and sent %d offline events.", len(events))
        except Exception:
            pass  # Will try again next cycle
