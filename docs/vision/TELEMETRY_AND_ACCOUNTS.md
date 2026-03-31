# Nimbus Adaptive Controller — Telemetry, Analytics & User Accounts

> **Status**: Proposal — not yet implemented  
> **Last updated**: March 29, 2026  
> **Priority**: High — prerequisite for distribution scale and research platform

---

## Overview

As Nimbus Adaptive Controller grows beyond a single-developer tool into a distributed accessibility platform, three capabilities become necessary together:

1. **User accounts** — identity, cloud sync, licensing, and support
2. **Usage analytics** — understand what people actually use and with which games
3. **Crash reporting** — find and fix production bugs that never appear in dev

These are deliberately designed around the accessibility-first mission: fully opt-in, privacy-respecting, and useful to users (not just to us). Every data point collected should either improve the product or directly benefit the research community.

---

## 1. User Accounts

### Why We Need Them

- **Cloud profile sync** — profiles stored in `%APPDATA%` today are lost on reinstall, not portable across machines
- **Licensing** — premium tier (voice commands, AI copilot, advanced macros) needs identity to enforce entitlements
- **Support** — "send us your session ID" is far better than "attach your log file"
- **Research** — opt-in longitudinal studies require user consent records tied to a stable identity
- **Community** — profile sharing marketplace ("share my Xbox layout for No Man's Sky") requires accounts

### Architecture

```
┌─────────────────────────┐        ┌──────────────────────────────┐
│   Nimbus Adaptive Controller (local)│  HTTPS │   Nimbus Cloud API           │
│                         │◄──────►│   (Supabase or Firebase)     │
│  src/cloud_client.py    │        │                              │
│  - login / logout       │        │  auth.users                  │
│  - sync profiles        │        │  profiles (per-user)         │
│  - report telemetry     │        │  sessions                    │
│  - check entitlements   │        │  crash_reports               │
└─────────────────────────┘        └──────────────────────────────┘
```

**Recommended backend**: [Supabase](https://supabase.com) — open-source, Postgres-backed, has auth + storage + realtime built in. Can self-host later.

### Account Tiers

| Tier | Price | What it unlocks |
|------|-------|-----------------|
| **Free** | $0 forever | All layouts, vJoy/ViGEm, profiles, custom builder, borderless gaming, game mode |
| **Nimbus+** | $5–8/month | Cloud profile sync, voice commands, advanced macros, AI copilot access |
| **Research** | Free (application) | Opt-in session logging for IRB-approved studies, researcher dashboard |
| **Institutional** | Custom | Hospital/rehab/VA bulk licenses, admin console, usage reports |

### Authentication Flow (Local App)

```
1. User opens File → Account → Sign In
2. App opens system browser to https://nimbus.app/auth
3. User signs in (email/password OR magic link OR Google/GitHub OAuth)
4. Browser redirects to nimbus://auth?token=... (custom URL scheme)
5. App receives token, stores in OS credential vault (keyring)
6. All subsequent API calls use bearer token
7. Token refreshed silently in background
```

**Implementation**:
- `src/cloud_client.py` — thin wrapper around `httpx` async client
- Custom URL scheme registered in installer (`nimbus://`)
- `keyring` library for OS-native credential storage (no plaintext tokens on disk)
- Offline-first: all local features work with no network; cloud features degrade gracefully

### Profile Cloud Sync

Profiles synced as JSON blobs keyed by `user_id + profile_id`:

```python
# On save
cloud_client.upsert_profile(profile_id, profile_data)

# On startup (Nimbus+)
remote_profiles = cloud_client.list_profiles()
# Merge strategy: last-write-wins per profile_id, conflict shown in UI
```

---

## 2. Usage Analytics

### Principles

- **Opt-in only** — first-run prompt, clearly described, never assumed
- **No PII** — no names, emails, IP addresses in events (IP stripped at ingestion)
- **Local-first** — events buffered locally, batch-uploaded on a timer (not real-time)
- **Transparent** — in-app "What we collect" page shows the exact event schema
- **Deletable** — user can purge all their analytics from account settings

### What to Collect

#### Session Events
```json
{
  "event": "session_start",
  "app_version": "1.5.0",
  "os_version": "Windows 11 23H2",
  "output_mode": "vigem",
  "vjoy_available": true,
  "vigem_available": true,
  "session_id": "uuid-v4-random"
}
```

#### Profile Events
```json
{
  "event": "profile_switch",
  "profile_id_hash": "sha256(profile_id)",
  "layout_type": "custom",
  "widget_count": 8,
  "output_mode": "vigem"
}
```

#### Widget Usage
```json
{
  "event": "widget_added",
  "widget_type": "joystick",
  "output_mode": "vigem",
  "axis_x": "x",
  "axis_y": "y"
}
```

#### Game Mode Events
```json
{
  "event": "game_mode_start",
  "method": "vigem_controller_mode",
  "game_detected": true,
  "game_title_hash": "sha256(window_title)"
}
```

Note: `game_title_hash` is a one-way hash. We know *how many* users used Nimbus with a particular game without storing the game name in plaintext. We can build a reverse lookup table from the known game list in `src/borderless.py` to decode common values.

#### Crash / Error Events
```json
{
  "event": "crash",
  "exception_type": "AttributeError",
  "module": "src.bridge",
  "function": "switchProfile",
  "line": 829,
  "app_version": "1.5.0",
  "stack_hash": "sha256(traceback)"
}
```

Stack traces are hashed for deduplication; full trace only sent if user checks "Include full error details".

### What NOT to Collect

- Button IDs, axis values, or any actual controller input
- Profile names or descriptions
- Window titles in plaintext (hash only)
- Any file system paths
- Any content of macros or custom key bindings

### Implementation

**`src/telemetry.py`** — new module:

```python
class TelemetryClient:
    """Opt-in analytics and crash reporting."""

    def __init__(self, config: ControllerConfig):
        self._enabled = config.get("telemetry.enabled", False)
        self._buffer: list[dict] = []
        self._flush_timer = QTimer()
        self._flush_timer.setInterval(5 * 60 * 1000)  # flush every 5 min
        self._flush_timer.timeout.connect(self._flush)

    def track(self, event: str, props: dict = None) -> None:
        if not self._enabled:
            return
        self._buffer.append({
            "event": event,
            "ts": datetime.utcnow().isoformat(),
            "session_id": self._session_id,
            **(props or {})
        })

    def capture_exception(self, exc: Exception) -> None:
        if not self._enabled:
            return
        tb = traceback.format_exc()
        self.track("crash", {
            "exception_type": type(exc).__name__,
            "stack_hash": hashlib.sha256(tb.encode()).hexdigest()[:16],
            "module": ...,
        })

    def _flush(self) -> None:
        # POST batch to https://api.nimbus.app/v1/events
        ...
```

**Opt-in prompt** (first run, after onboarding):

> *"Help improve Nimbus Adaptive Controller? We'd like to collect anonymous usage data — which features are used, which games people play with, and crash reports. No personal information, no controller inputs. You can change this anytime in Settings → Privacy."*
>
> **[Yes, share analytics]** &nbsp;&nbsp; **[No thanks]**

---

## 3. Game Detection

### Goal

Know which games users are playing Nimbus with — without storing game names in plaintext and without requiring any manual input from the user.

### Approach A — Active Window Detection (Easiest, Already Partially Built)

`src/borderless.py` already enumerates windows and matches against `GAME_COMPATIBILITY`. We can extend this:

1. When Game Mode starts, record `sha256(window_title)` as the game identifier
2. Cross-reference against the known compatibility database to decode the hash
3. Unknown hashes flagged as "potential new game" — use volume (many users hashing the same unknown title) as signal to add it to the database

**Benefit**: Zero friction — game is detected automatically when Game Mode activates.

### Approach B — Foreground App Polling (Background)

Poll `GetForegroundWindow()` every 30 seconds during a session. Track which titles were active while Nimbus was running. This gives us "used with X game" data even when Game Mode isn't explicitly started.

**Privacy note**: Only hashes are transmitted. Polling stops when Nimbus loses focus entirely (user closed app).

### Approach C — User-Reported Game Tags (Highest Quality)

Optional field in the "New Profile" dialog:

> *"Which game is this profile for? (optional)"*  
> `[_________________________]` with autocomplete from the compatibility database

This gives us clean, labeled data and also improves the compatibility database (user is essentially crowd-sourcing game support entries).

### Recommended: Combine A + C

- A gives passive coverage for all Game Mode sessions
- C gives explicit, high-quality profile-to-game associations when the user wants to provide it

---

## 4. Crash Reporting

### Current State

Crashes are silently swallowed or print to console — no visibility into production errors.

### Proposed Stack

**Option A (self-hosted, free)**: [GlitchTip](https://glitchtip.com) — open-source Sentry-compatible crash reporting. Self-host on a $5 VPS or use GlitchTip cloud (free tier: 1k events/month).

**Option B (managed)**: [Sentry](https://sentry.io) — industry standard. Free tier: 5k errors/month. Python SDK is one import.

**Recommended**: Sentry for speed of integration; migrate to self-hosted GlitchTip if volume or cost becomes an issue.

### Integration

```python
# src/qt_qml_app.py — top of main()
import sentry_sdk
if config.get("telemetry.enabled", False):
    sentry_sdk.init(
        dsn="https://...@sentry.io/...",
        release=f"nimbus-adaptive-controller@{VERSION}",
        environment="production",
        traces_sample_rate=0.0,   # no performance traces (PII risk)
        before_send=_scrub_event, # strip any path/filename info
    )
```

**`_scrub_event`** removes:
- Any `abs_path` that reveals the user's username or file system layout
- Request bodies (none expected, but belt-and-suspenders)
- Environment variables

### Crash Opt-In UI

In Settings → Privacy:

```
[ ] Send crash reports to the Nimbus team
    Helps fix bugs faster. Includes: exception type, stack trace,
    app version, OS version. Never includes controller inputs or
    personal information.

[ ] Send usage analytics
    Helps us understand which features and games are most used.
    Fully anonymous. See exactly what we collect: [View data schema]
```

---

## 5. Distribution Strategy Update

### Current Distribution

- GitHub Releases (exe + NSIS installer, manually uploaded)
- EV code-signed
- No update mechanism

### Proposed Distribution Layers

#### Layer 1 — Direct Download (Current, Improved)

- GitHub Releases remains the canonical source
- Add **auto-update** via `pyupdater` or a simple JSON version manifest check at startup:
  ```python
  # Check https://nimbus.app/version.json on startup
  {"latest": "1.5.1", "min_supported": "1.4.0", "download_url": "..."}
  ```
  If `latest > current`, show a non-intrusive ribbon: *"Update available — v1.5.1"*

#### Layer 2 — Microsoft Store (MSIX)

- MSIX packaging enables Store distribution with no SmartScreen warnings
- Auto-updates via Store
- Sandboxed install (no admin required)
- **Blocker**: ViGEmBus driver install cannot run from MSIX sandbox — must use `winget install nefarius.vigembus` prompt at first run

#### Layer 3 — winget (Developer Audience)

```powershell
winget install OwenKent.NimbusAdaptiveController
```

Submit to `microsoft/winget-pkgs` repo. Reaches developers who are likely to recommend it to others.

#### Layer 4 — Nimbus.app Website

- Landing page with download button, screenshots, feature list
- Account management portal (sign up, billing, profile sync)
- Public profile gallery ("Community Layouts")
- Blog / changelog feed

### Update Channels

| Channel | Audience | Cadence |
|---------|----------|---------|
| `stable` | All users | Major/minor releases, fully tested |
| `beta` | Opt-in | Feature previews, release candidates |
| `dev` | Contributors | Every merge to `main` |

---

## 6. Implementation Roadmap

### Phase 1 — Crash Reporting (1 session, no accounts needed)

1. Add Sentry SDK to `requirements.txt`
2. Opt-in prompt on first run (single checkbox, Privacy section of Settings)
3. Initialize Sentry in `qt_qml_app.py` conditioned on opt-in
4. Scrub PII from events before send
5. Test: trigger a known exception, verify it appears in Sentry dashboard

**Delivers**: Immediate production visibility with minimal engineering.

### Phase 2 — Anonymous Analytics (1–2 sessions)

1. Implement `src/telemetry.py` with local buffer + batch flush
2. Set up ingestion endpoint (can be a simple Supabase edge function or Plausible)
3. Track: `session_start`, `profile_switch`, `widget_added`, `game_mode_start`
4. Add opt-in to Privacy settings alongside crash reporting

**Delivers**: Usage data to prioritize feature work and game compatibility.

### Phase 3 — User Accounts (3–5 sessions)

1. Set up Supabase project (auth, `profiles` table, `sessions` table)
2. Implement `src/cloud_client.py` with login/logout/token refresh
3. Register `nimbus://` custom URL scheme in NSIS installer
4. Add File → Account → Sign In / Sign Out menu items
5. Profile sync: push on save, pull on startup (Nimbus+ only)
6. Add account status to status ribbon

**Delivers**: Cloud sync, prerequisite for premium tier billing.

### Phase 4 — Premium Billing (2–3 sessions)

1. Stripe integration for Nimbus+ subscriptions
2. Entitlement check in `cloud_client.py` (JWT claims or Supabase row)
3. Feature gates in QML: voice, AI copilot, advanced macros show upsell if not Nimbus+
4. Institutional license flow (email-based, manual initially)

**Delivers**: Revenue to sustain development.

---

## 7. Privacy & Compliance Notes

- **GDPR / CCPA**: Since we collect any data from EU/CA users, we need a Privacy Policy and cookie/consent flow on the website. Supabase is GDPR-compliant. Sentry has EU data residency option.
- **COPPA**: If any users are under 13 (possible for accessibility users), we need age gate or parental consent. Recommend 13+ minimum for accounts; anonymous use remains unrestricted.
- **IRB**: Any research involving human subjects data (Research tier) requires IRB approval before data collection begins. Partner institutions (AbleGamers, CMU HCII) typically have their own IRBs; we act as a data processor under their protocol.
- **Data retention**: Crash reports: 90 days. Analytics events: 1 year aggregated, raw events 30 days. User profiles: retained until account deletion request.

---

## Related Documents

- [`docs/vision/RESEARCH_PLATFORM.md`](RESEARCH_PLATFORM.md) — IRB-appropriate telemetry for disability gaming research
- [`docs/NEXT_STEPS.md`](../NEXT_STEPS.md) — implementation priority queue
- [`docs/distribution/BUSINESS_MODEL.md`](../distribution/BUSINESS_MODEL.md) — freemium model and sustainability
