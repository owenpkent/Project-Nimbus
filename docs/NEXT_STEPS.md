# Project Nimbus — Next Steps

> **Current state**: v1.3.2 ready for build and release  
> **Branch**: `feature/borderless-mouse-integration`  
> **Last updated**: March 8, 2026

---

## Immediate (Before Releasing v1.3.2)

### 1. Build the v1.3.2 Executable

```powershell
# From project root
venv\Scripts\pyinstaller.exe build_tools\Project-Nimbus.spec --noconfirm
```

**Output**: `dist\Project-Nimbus-1.3.2.exe` (~174MB)

The previous unsigned build is `1.3.1` — you need a fresh `1.3.2` build with the new borderless gaming module and updated version strings.

### 2. Test Borderless Gaming on Real Games

**Critical test cases**:
- Launch Minecraft (Java Edition) in windowed mode
- Open Project Nimbus → **View → Borderless Gaming...**
- Click **"Scan for Games"** — verify Minecraft is auto-detected
- Select Minecraft, click **"Apply Borderless + Free Cursor"** (green button)
- Verify:
  - Game window fills screen without borders
  - Cursor can freely move between game and Nimbus
  - Cursor release polling is active (check status indicator)
- Click **"Restore Window & Stop"** — verify game returns to normal

**Other games to test**:
- Stardew Valley
- Terraria
- Skyrim (set to windowed first)

**What to watch for**:
- `start_cursor_release` background thread stability
- ClipCursor polling doesn't cause performance issues
- Window restoration works correctly
- Auto-detect matches the right window

### 3. Build the Installer

```powershell
# Requires NSIS installed
& "C:\Program Files (x86)\NSIS\makensis.exe" build_tools\installer.nsi
```

**Output**: `dist\Project-Nimbus-Setup-1.3.2.exe`

### 4. Sign Both Files (EV Certificate)

```powershell
cmd /c build_tools\sign_exe.bat
```

**Requires**: Hardware token with EV certificate

**What it does**:
- Signs `Project-Nimbus-1.3.2.exe` with SHA-256 + DigiCert timestamp
- Signs `Project-Nimbus-Setup-1.3.2.exe` with SHA-256 + DigiCert timestamp
- Verifies both signatures

**Why this matters**: `UIAccess=true` in the manifest only activates when the exe is EV-signed AND installed in a trusted location (`%LOCALAPPDATA%\Programs\`). Without signing, the borderless gaming features work, but the app won't have on-screen-keyboard parity for full accessibility.

### 5. Merge the Branch

```powershell
git checkout main
git merge feature/borderless-mouse-integration
git push origin main
```

**Only after** testing passes and the build is verified.

### 6. Tag and Release

```powershell
git tag v1.3.2
git push origin v1.3.2
```

Upload to GitHub Releases:
- `Project-Nimbus-1.3.2.exe` (signed)
- `Project-Nimbus-Setup-1.3.2.exe` (signed)
- Release notes from `CHANGELOG.md` [1.3.2] section

---

## Near-Term (1-2 Sessions)

### 7. Expand the Game Compatibility Database

**Current state**: 30 games in `src/borderless.py`'s `GAME_COMPATIBILITY` list

**Action items**:
- Every game you or a tester verifies should be added to the list
- Update `docs/GAME_COMPATIBILITY.md` to match
- The in-app Compatibility tab surfaces this automatically

**How to add a game**:

1. Edit `src/borderless.py` → add a new `GameCompatEntry` to the list:
```python
GameCompatEntry(
    name="Game Name",
    status="verified",  # or "likely", "partial", "incompatible"
    input_method="clipcursor",  # or "rawinput", "exclusive_fullscreen"
    notes="Works perfectly with borderless + cursor release.",
    window_title_hint="Game Name",  # substring to match window title
    needs_borderless=True,
    needs_cursor_release=True,
    recommended_interval_ms=50
),
```

2. Update `docs/GAME_COMPATIBILITY.md` → add to the appropriate table (Verified/Likely/Partial/Incompatible)

3. Commit: `git commit -m "feat: add [Game Name] to compatibility database"`

**Priority games to test**:
- Popular indie games (Hollow Knight, Dead Cells, Hades)
- Strategy games (Civilization VI, Age of Empires)
- Simulation games (Cities: Skylines, Planet Coaster)
- Any game with known accessibility barriers

### 8. Test with Existing Users' Profiles

**Scenario**: Users who had `flight_simulator`, `xbox_controller`, or `adaptive_platform_1` in their `%APPDATA%\ProjectNimbus\profiles\` will still have those files.

**Expected behavior**:
- Those profiles still appear in the **File → Profile** menu
- They still load correctly (backward compatible)
- New installs only get `adaptive_platform_2`

**Test**:
1. Manually create `%APPDATA%\ProjectNimbus\profiles\flight_simulator.json` with old content
2. Launch Nimbus
3. Verify it appears in the profile menu
4. Switch to it — verify it loads the FlightSimLayout
5. Switch back to Adaptive Platform 2

**Why this matters**: Ensures we didn't break anyone's existing setup.

---

## Longer-Term (From the Roadmap)

### 9. Voice Command Integration

**Status**: Architecture documented in `docs/distribution/VOICE_COMMAND.md`

**What it is**: Speak to trigger buttons, axes, and macros. Offline engines (Faster-Whisper, Vosk) for low latency and privacy, or cloud engines (DeepGram Nova-3) for higher accuracy.

**Next steps**:
- Port the existing DeepGram streaming implementation from the companion project to Python/PySide6
- Add a **Voice** tab to the settings menu
- Implement interim result handling for time-critical commands (e.g., "fire" triggers immediately on interim, confirms on final)
- Add voice-triggered macro support to the macro joystick system

**Priority**: High for accessibility users who cannot use physical input

### 10. Keyboard Output Mode

**Status**: Documented in `docs/vision/KEYBOARD_OUTPUT.md`

**What it is**: Any Nimbus button or slider can emit native keyboard shortcuts to any application — Photoshop, DaVinci Resolve, OBS, a browser — with no external software.

**Implementation**:
- Use Windows `SendInput` API (same `user32.dll` already used by Nimbus)
- Fully bundled in the installer, no driver install required
- Per-widget config: "Output Type" dropdown → "vJoy Button" or "Keyboard Shortcut"
- Shortcut editor: Ctrl+Shift+K, etc.

**Use cases**:
- **Stream Deck replacement** — buttons trigger OBS scene switches, mute/unmute
- **Drawing tablet express keys** — buttons trigger Photoshop brush size, undo, layer shortcuts
- **DAW controller** — sliders control volume, buttons trigger play/pause/record
- **Video editing** — buttons trigger DaVinci Resolve cut, ripple delete, color grade shortcuts

**Priority**: Medium-high — expands Nimbus beyond gaming into productivity

### 11. Physical Hardware Integration

**Status**: Documented in `docs/vision/HARDWARE_INTEGRATION.md`

**What it is**: Nimbus can wrap existing adaptive hardware — **Xbox Adaptive Controller**, **QuadStick**, foot pedals, head trackers — reading their input via XInput/DirectInput and re-emitting through vJoy with Nimbus's sensitivity curves, macros, and voice layer applied on top.

**Implementation**:
- Detect XInput devices (XAC appears as a standard XInput device)
- Add "Input Source" dropdown in settings: "Mouse" or "XInput Device 1" or "DirectInput Device"
- Map XAC buttons/sticks → Nimbus widgets → vJoy output with sensitivity curves applied
- No special SDK needed — XAC is just XInput

**Use case**: User has an XAC but wants Nimbus's macro system, voice commands, and sensitivity curves on top of it.

**Priority**: Medium — requires hardware for testing

### 12. AAC — Augmentative & Alternative Communication

**Status**: Documented in `docs/vision/AAC_INTEGRATION.md`

**What it is**: The same customizable button surface that controls a game can output spoken phrases via text-to-speech, navigate AAC vocabulary pages, or trigger keyboard shortcuts in dedicated AAC software.

**Implementation**:
- Add "AAC Mode" toggle in widget config
- AAC button config: phrase text, TTS voice, volume
- Switch access (single/dual switch scanning) support
- Eye gaze integration (Windows Eye Control already works with Nimbus today)

**Use case**: A gaming + AAC hybrid on one screen — something no commercial product currently offers.

**Priority**: High for non-verbal users

### 13. Research Platform

**Status**: Documented in `docs/vision/RESEARCH_PLATFORM.md`

**What it is**: Every Nimbus session generates behavioral data — axis configurations, input frequency, profile choices, fatigue patterns — that the disability gaming research community doesn't have at scale.

**Implementation**:
- Opt-in, IRB-appropriate telemetry
- Anonymized session logs: widget usage, sensitivity settings, game compatibility results
- Partnership with AbleGamers, Shirley Ryan AbilityLab, CMU HCII, etc.

**Use case**: Understand how people with disabilities actually play, at scale, to inform future assistive tech design.

**Priority**: Low — requires institutional partnerships and IRB approval

### 14. Modular Control Surface

**Status**: Documented in `docs/vision/MODULAR_CONTROL_SURFACE.md`

**What it is**: Beyond gaming — Nimbus as a universal adaptive input layer for video editing, music production, streaming, and any Windows application.

**Implementation**:
- Pre-built profiles for DaVinci Resolve, Photoshop, Ableton, OBS
- Auto-switch profiles by active window (detect foreground app, load matching profile)
- Keyboard output mode (see #10) is the foundation for this

**Use case**: One device, one learned interface, works everywhere.

**Priority**: Medium — depends on keyboard output mode (#10)

---

## Sustainability & Business Model

**Status**: Documented in `docs/distribution/BUSINESS_MODEL.md`

**Core principle**: Project Nimbus is and will remain **free for all accessibility use**.

**Freemium model**:
- **Free forever**: All layouts, vJoy/ViGEm, profiles, custom builder, borderless gaming
- **Optional subscription** ($5-10/month): Voice commands, advanced macros, AI copilot (Spectator+), cloud sync
- **Institutional licenses**: Hospitals, rehab centers, VA — bulk licensing for clinical use
- **Corporate sponsorships**: Microsoft, Logitech, AbleGamers Foundation
- **Research grants**: NIH SBIR, NSF, accessibility-focused foundations

**Next steps**:
- Finalize freemium tier boundaries
- Implement Stripe integration for subscriptions
- Draft sponsorship outreach emails (templates in `docs/distribution/SPONSORSHIP_OUTREACH.md`)
- Apply for grants (sources in `docs/distribution/RELEASE_STRATEGY.md`)

---

## Testing Checklist (Before Each Release)

- [ ] Build exe with PyInstaller
- [ ] Test borderless gaming with 3+ games
- [ ] Test profile switching (AP2 → legacy → AP2)
- [ ] Test widget drag/resize/delete in edit mode
- [ ] Test joystick triple-click lock + unlock
- [ ] Test macro joystick with all action types
- [ ] Test button toggle/momentary modes
- [ ] Test slider snap modes (none, left, center)
- [ ] Test sensitivity curve preview in config dialog
- [ ] Test Game Focus Mode (Windows only)
- [ ] Test vJoy connection status
- [ ] Test ViGEm connection (if available)
- [ ] Build installer with NSIS
- [ ] Sign exe + installer with EV cert
- [ ] Verify UIAccess works (install in trusted location)
- [ ] Test uninstall (verify profiles preserved)
- [ ] Tag release, upload to GitHub

---

## Documentation Maintenance

**Keep these in sync**:
- `README.md` — user-facing overview, features, installation
- `CHANGELOG.md` — version history with semantic versioning
- `docs/GAME_COMPATIBILITY.md` — game list (matches `src/borderless.py`)
- `docs/architecture/architecture.md` — technical architecture
- `docs/development/LLM_NOTES.md` — AI assistant reference
- `DIRECTORY.md` — project structure guide

**When adding a new feature**:
1. Update `README.md` features section
2. Add to `CHANGELOG.md` under `[Unreleased]` or next version
3. Update `docs/architecture/architecture.md` if it changes the architecture
4. Update `docs/development/LLM_NOTES.md` if it adds new APIs or conventions
5. Update `DIRECTORY.md` if it adds new files or directories

---

## Contact & Support

- **GitHub Issues**: Bug reports, feature requests
- **Email**: [your email]
- **Discord**: [if you have a community server]
- **AbleGamers**: Partnership for accessibility testing and outreach

---

**Remember**: Every feature should make the app more accessible, not less. If a feature adds complexity, add a tutorial or simplify the UI. The goal is a **software Xbox Adaptive Controller** that anyone can use, regardless of physical ability.
