# Telemetry & Privacy — Setup & Usage Guide

> **Module**: `src/telemetry.py`  
> **Status**: Implemented — opt-in, no data collected until user consents  
> **Last updated**: March 2026

---

## Overview

Nimbus Adaptive Controller includes an **opt-in** telemetry system for anonymous usage analytics and crash reporting. No data is collected unless the user explicitly enables it.

### Design Principles

1. **Opt-in only** — first-run prompt, clearly described, never assumed
2. **No PII** — no names, emails, IP addresses in events (IP stripped at ingestion)
3. **Local-first** — events buffered locally, batch-uploaded every 5 minutes
4. **Transparent** — in-app "What we collect" page shows the exact event schema
5. **Deletable** — user can disable at any time; data purged from account settings

---

## Enabling Telemetry

### First-Run Prompt

On first launch (after onboarding), the user sees:

> *"Help improve Nimbus Adaptive Controller? We'd like to collect anonymous usage data — which features are used, which games people play with, and crash reports. No personal information, no controller inputs. You can change this anytime in Settings → Privacy."*
>
> **[Yes, share analytics]** &nbsp;&nbsp; **[No thanks]**

### Settings → Privacy

Users can toggle telemetry at any time:

1. Open **File → Settings → Privacy**
2. Toggle **"Send crash reports"** — on/off
3. Toggle **"Send usage analytics"** — on/off
4. Expand **"What we collect"** to see the exact event schema
5. Expand **"What we NEVER collect"** for peace of mind

---

## What We Collect

### Session Events

Recorded once when the app starts:

| Field | Example | Purpose |
|-------|---------|---------|
| `app_version` | `"1.5.0"` | Know which versions are in use |
| `os_version` | `"Windows 11 23H2"` | OS compatibility tracking |
| `output_mode` | `"vigem"` | vJoy vs ViGEm usage split |
| `vjoy_available` | `true` | Driver install success rate |
| `vigem_available` | `true` | Driver install success rate |

### Profile Events

Recorded when the user switches profiles:

| Field | Example | Purpose |
|-------|---------|---------|
| `profile_id_hash` | `"a1b2c3d4e5f6..."` | SHA-256 hash — no profile names |
| `layout_type` | `"custom"` | Which layout types are popular |
| `widget_count` | `8` | Average layout complexity |
| `output_mode` | `"vigem"` | Output mode per profile |

### Widget Events

Recorded when a widget is added to the canvas:

| Field | Example | Purpose |
|-------|---------|---------|
| `widget_type` | `"joystick"` | Which widgets are most used |
| `output_mode` | `"vigem"` | Widget usage by output mode |

### Game Mode Events

Recorded when Game Mode or Borderless Gaming activates:

| Field | Example | Purpose |
|-------|---------|---------|
| `method` | `"vigem_controller_mode"` | Which game integration method |
| `game_detected` | `true` | Auto-detection success rate |
| `game_title_hash` | `"f7e8d9c0..."` | SHA-256 hash — no plaintext titles |

### Crash Events

Recorded when an unhandled exception occurs:

| Field | Example | Purpose |
|-------|---------|---------|
| `exception_type` | `"AttributeError"` | Bug categorisation |
| `module` | `"src.bridge"` | Where the bug is |
| `function` | `"switchProfile"` | Specific function |
| `line` | `829` | Exact location |
| `stack_hash` | `"b3c4d5e6..."` | Deduplication |
| `app_version` | `"1.5.0"` | Version-specific bugs |

### Common Fields (on every event)

| Field | Example | Purpose |
|-------|---------|---------|
| `ts` | `"2026-03-29T14:30:00Z"` | Event timestamp (UTC) |
| `session_id` | `"uuid-v4"` | Random per session, not linked to identity |
| `user_id` | `"uuid-v4"` | Stable anonymous ID — no PII |

---

## What We NEVER Collect

- Button IDs, axis values, or any actual controller input
- Profile names or descriptions
- Window titles in plaintext (SHA-256 hash only)
- Any file system paths
- Any content of macros or custom key bindings
- Email addresses, names, or IP addresses

---

## How It Works (Technical)

### Architecture

```
┌────────────────────────┐
│  TelemetryClient       │
│  (src/telemetry.py)    │
│                        │
│  .track("event", {})   │──► In-memory buffer
│  .capture_exception()  │         │
│                        │    Every 5 min
│  QTimer flush cycle    │◄────────┘
│         │              │
│    ┌────▼────┐         │
│    │  httpx  │         │
│    │  POST   │─────────┼──► https://api.nimbus.app/v1/events
│    └────┬────┘         │
│         │ (on failure) │
│    ┌────▼────────┐     │
│    │ Local JSON  │     │    %APPDATA%/ProjectNimbus/telemetry/
│    │ fallback    │     │    pending_events.json
│    └─────────────┘     │
└────────────────────────┘
```

### Event Flow

1. Code calls `telemetry.track("event_name", {"key": "value"})`
2. If analytics is disabled → no-op (returns immediately)
3. Event is appended to in-memory buffer with timestamp and session ID
4. Every 5 minutes, the buffer is flushed via HTTP POST to the API
5. On flush failure (no network), events are persisted to a local JSON file
6. On next successful flush, offline events are retried and sent
7. Local file capped at 500 events to prevent unbounded disk usage

### Crash Reporting

Two layers:

1. **Built-in**: `telemetry.capture_exception(exc)` records crash metadata in the same event buffer
2. **Sentry SDK** (optional): If `sentry-sdk` is installed and `NIMBUS_SENTRY_DSN` is set, crashes are also forwarded to Sentry for structured reporting with the `_scrub_sentry_event` callback stripping PII

---

## Configuration

Telemetry settings are stored in `controller_config.json`:

```json
{
    "telemetry": {
        "analytics_enabled": false,
        "crash_reports_enabled": false,
        "user_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
}
```

- `analytics_enabled` — user opted in to usage analytics
- `crash_reports_enabled` — user opted in to crash reports
- `user_id` — stable anonymous UUID, auto-generated on first run (not linked to any account)

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `NIMBUS_TELEMETRY_URL` | Override telemetry API endpoint | `https://api.nimbus.app/v1/events` |
| `NIMBUS_SENTRY_DSN` | Sentry DSN for crash reporting | (empty — Sentry disabled) |
| `NIMBUS_ENV` | Environment tag for Sentry | `production` |

---

## For Developers

### Adding a New Telemetry Event

1. Define the event in `src/telemetry.py`:
   - Add a convenience method (e.g. `track_my_event()`) for type safety
   - Document the fields in the `event_schema()` static method

2. Call it from the appropriate location:
   ```python
   telemetry.track("my_event", {
       "field_hash": _hash(sensitive_value),  # always hash identifiers
       "numeric_field": 42,
   })
   ```

3. Update the QML schema display in `SettingsPrivacyDialog.qml`

4. Update this document's "What We Collect" section

### Testing Telemetry Locally

```powershell
# Set a local endpoint for testing
$env:NIMBUS_TELEMETRY_URL = "http://localhost:8000/v1/events"

# Run the app
python run.py

# Events will be POSTed to localhost:8000 instead of production
```

---

## Related Files

| File | Purpose |
|------|---------|
| `src/telemetry.py` | Telemetry client implementation |
| `qml/components/SettingsPrivacyDialog.qml` | Privacy settings UI |
| `docs/vision/TELEMETRY_AND_ACCOUNTS.md` | Full architecture proposal |
| `docs/vision/RESEARCH_PLATFORM.md` | IRB-appropriate telemetry for research |

---

## Privacy Compliance Notes

- **GDPR / CCPA**: Data is fully anonymous (no PII). Users can disable at any time.
- **COPPA**: No accounts required for telemetry; anonymous UUID is not linked to identity.
- **Data retention**: Crash reports 90 days, analytics 1 year aggregated, raw events 30 days.
- **Right to erasure**: Users can disable telemetry and request data deletion via account settings.
