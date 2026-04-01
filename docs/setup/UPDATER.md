# Auto-Updater — Setup & Usage Guide

> **Module**: `src/updater.py`  
> **Status**: Implemented — lightweight version check with non-intrusive notification  
> **Last updated**: March 2026

---

## Overview

Nimbus Adaptive Controller includes a lightweight auto-update checker that notifies users when a new version is available. It does **not** download or install anything automatically — the user is always in control.

### How It Works

1. **10 seconds after startup**, the app fetches a small JSON manifest from `https://nimbus.app/version.json`
2. The manifest contains the latest version number, download URL, and release notes
3. If a newer version is available, a **non-intrusive ribbon** appears at the top of the window
4. The user can click **"Download"** to open the release page, or **"✕"** to dismiss
5. The check repeats every **6 hours** while the app is running

### Design Goals

- **Lightweight** — single HTTP GET, no background downloads, no elevated privileges
- **Non-intrusive** — ribbon notification, never a modal dialog or forced restart
- **User-controlled** — dismiss hides until next version; can disable entirely in Settings
- **Channel support** — stable, beta, and dev update channels

---

## User Guide

### Update Notification Ribbon

When an update is available, a blue ribbon appears at the top of the window:

```
┌─────────────────────────────────────────────────────────┐
│ ⬆ Update available — v1.6.0    Bug fixes...  [Download] [✕] │
└─────────────────────────────────────────────────────────┘
```

- **Download** — opens the GitHub Releases page (or nimbus.app) in your browser
- **✕** — dismisses the ribbon; won't show again for this version

### Force Update (Rare)

If your version is below the minimum supported version, a **yellow warning ribbon** appears that cannot be dismissed:

```
┌──────────────────────────────────────────────────────────────┐
│ ⚠ Your version is no longer supported. Please update.  [Download] │
└──────────────────────────────────────────────────────────────┘
```

This only happens when a critical security fix or breaking API change requires all users to update.

### Update Channels

| Channel | Audience | What You Get |
|---------|----------|--------------|
| **stable** (default) | All users | Major/minor releases, fully tested |
| **beta** | Opt-in testers | Feature previews, release candidates |
| **dev** | Contributors | Every merge to `main` |

To change your channel:
1. Open **File → Settings → Updates**
2. Select your preferred channel
3. The next check will use the new channel

---

## Version Manifest Format

The updater fetches a JSON manifest from a configurable URL:

```json
{
    "latest": "1.6.0",
    "min_supported": "1.4.0",
    "download_url": "https://github.com/owenpkent/Nimbus-Adaptive-Controller/releases/latest",
    "release_notes": "Bug fixes and performance improvements.",
    "release_date": "2026-04-01",
    "channels": {
        "stable": "1.6.0",
        "beta": "1.6.1-beta.1",
        "dev": "1.7.0-dev.42"
    }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `latest` | Yes | Latest stable version string |
| `min_supported` | No | Minimum version that can still run (triggers force update if below) |
| `download_url` | No | URL to open when user clicks "Download" |
| `release_notes` | No | Short description shown in the ribbon |
| `release_date` | No | ISO date of the release |
| `channels` | No | Per-channel version overrides |

---

## Configuration

Settings are stored in `controller_config.json`:

```json
{
    "updater": {
        "channel": "stable",
        "auto_check": true,
        "dismissed_version": ""
    }
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `channel` | string | `"stable"` | Update channel |
| `auto_check` | bool | `true` | Check for updates on startup |
| `dismissed_version` | string | `""` | Version the user dismissed (won't re-notify) |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `NIMBUS_VERSION_URL` | Override version manifest URL | `https://nimbus.app/version.json` |

---

## Technical Details

### Version Parsing

The updater supports semantic versioning with optional pre-release tags:

```
1.5.0              → (1, 5, 0, 99, 0)   — stable
1.6.0-beta.2       → (1, 6, 0, 2, 2)    — beta pre-release
2.0.0-rc.1         → (2, 0, 0, 3, 1)    — release candidate
1.7.0-dev.42       → (1, 7, 0, 0, 42)   — dev build
```

Pre-release ordering: `dev` < `alpha` < `beta` < `rc` < stable

### Non-Blocking Fetch

The version manifest is fetched in a **background QThread** so it never blocks the UI:

```
Main Thread                    Background Thread
    │                               │
    ├── QTimer.singleShot(10s) ────►│
    │                               ├── httpx.get(version.json)
    │                               │
    │◄── finished.emit(manifest) ───┤
    │                               │
    ├── _on_manifest_received()     │
    │   └── emit updateAvailable()  │
    │       └── QML ribbon shown    │
```

### Periodic Re-Check

After the initial check, the updater re-checks every 6 hours via a `QTimer`. This ensures long-running sessions see new releases without restarting.

---

## Hosting the Version Manifest

### Option A: GitHub Pages (Simplest)

1. Create a `version.json` file in a `gh-pages` branch or `/docs` folder
2. Enable GitHub Pages in repository settings
3. File will be available at `https://owenpkent.github.io/Nimbus-Adaptive-Controller/version.json`
4. Update `DEFAULT_VERSION_URL` in `src/updater.py` or set `NIMBUS_VERSION_URL`

### Option B: nimbus.app Website

Host the manifest at `https://nimbus.app/version.json` as a static file on your web server.

### Option C: GitHub Releases API

Instead of a static manifest, you could fetch the latest release from:
```
https://api.github.com/repos/owenpkent/Nimbus-Adaptive-Controller/releases/latest
```
This requires adapting `_FetchWorker` to parse the GitHub API response format.

---

## For Developers

### Testing the Updater Locally

```powershell
# Serve a local version manifest
echo '{"latest": "99.0.0", "download_url": "https://example.com"}' > version.json
python -m http.server 8080

# Point the updater at it
$env:NIMBUS_VERSION_URL = "http://localhost:8080/version.json"
python run.py
# → Update ribbon should appear after 10 seconds
```

### Updating the Manifest on Release

Add this to your release checklist:

1. Update `version.json` with the new version number and release notes
2. Deploy to your hosting (GitHub Pages / nimbus.app)
3. Verify with `curl https://nimbus.app/version.json`

---

## Related Files

| File | Purpose |
|------|---------|
| `src/updater.py` | Update checker implementation |
| `qml/components/UpdateNotification.qml` | Update ribbon UI |
| `docs/vision/TELEMETRY_AND_ACCOUNTS.md` | Distribution strategy (Section 5) |
| `docs/NEXT_STEPS.md` | Phase 4 — Distribution Expansion |
