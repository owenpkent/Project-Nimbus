# Game Compatibility — Borderless Gaming & Mouse Capture

Project Nimbus includes built-in borderless gaming support that lets you free your cursor from games that lock it, so you can interact with the Nimbus controller interface while gaming.

## How It Works

Games capture the mouse using one of three mechanisms:

| Mechanism | How Nimbus Handles It |
|---|---|
| **ClipCursor** — game confines cursor to its window rect | Nimbus continuously releases the clip via polling (`ClipCursor(NULL)`) |
| **Exclusive Fullscreen** — game takes over the display | Nimbus converts the window to borderless windowed mode |
| **Raw Input** — game reads mouse delta directly from HID | **Cannot be solved externally** — use second monitor or streaming |

## Access

**View → Borderless Gaming...** opens the control panel where you can:
- Auto-detect running games from our compatibility database
- Select any window and convert it to borderless fullscreen
- Toggle continuous cursor release on/off
- Adjust the release polling speed

---

## Verified Games

These games have been tested and confirmed working with Project Nimbus borderless mode.

| Game | Input Method | Notes |
|---|---|---|
| **Minecraft (Java Edition)** | ClipCursor | Set to windowed mode first. Cursor release works perfectly. |
| **Stardew Valley** | ClipCursor | XNA/MonoGame engine. Very accessible with controller support. |
| **Terraria** | ClipCursor | XNA/MonoGame engine. Great accessibility with controller support. |
| **The Elder Scrolls V: Skyrim** | ClipCursor | Set to windowed mode in launcher. Full controller support via ViGEm/vJoy. |

## Likely Compatible Games

High confidence based on engine analysis. These games use ClipCursor and should work well.

| Game | Input Method | Notes |
|---|---|---|
| **No Man's Sky** | ClipCursor | Has native borderless option. Excellent controller support — use ViGEm Xbox profile. |
| **Celeste** | ClipCursor | XNA/FNA engine. Strong controller support. Excellent built-in accessibility features. |
| **Hollow Knight** | ClipCursor | Unity engine. Good controller support. |
| **Hades** | ClipCursor | Custom engine with standard windowing. Excellent controller support. |
| **Slay the Spire** | ClipCursor | Java/LibGDX. Turn-based — very accessible for adaptive controllers. |
| **Civilization VI** | ClipCursor | Turn-based strategy — ideal for adaptive controllers. Has native borderless option. |
| **Factorio** | ClipCursor | Pausable — great for players who need extra time. |
| **Among Us** | ClipCursor | Unity engine. Simple controls — very accessible. |
| **Undertale / Deltarune** | ClipCursor | GameMaker engine. Simple controls. Excellent for adaptive play. |
| **Cuphead** | ClipCursor | Unity engine. Excellent controller support. |
| **Rocket League** | ClipCursor | Unreal Engine. Has built-in borderless option. Use ViGEm Xbox profile. |
| **Fall Guys** | ClipCursor | Unity engine. Good controller support. |
| **The Binding of Isaac: Rebirth** | ClipCursor | Roguelike — no penalty for taking time. |
| **Portal / Portal 2** | ClipCursor | Source engine. Puzzler — can be paused freely. |

## Partially Compatible Games

Some features work, with limitations.

| Game | Input Method | Notes |
|---|---|---|
| **Elden Ring** | ClipCursor + Raw Input | Use controller mode (ViGEm) — mouse camera won't work. Set to windowed in settings. |
| **Dark Souls III** | ClipCursor + Raw Input | Similar to Elden Ring — use controller mode. Set to windowed in settings first. |

## Incompatible Games

These games use Raw Input exclusively. External cursor release has no effect. Use a second monitor, tablet input device, or game streaming instead.

| Game | Why |
|---|---|
| **Valorant** | Raw Input + Vanguard anti-cheat |
| **Counter-Strike 2** | Raw Input + VAC anti-cheat |
| **Fortnite** | Raw Input + EasyAntiCheat |
| **Apex Legends** | Raw Input + EasyAntiCheat |
| **Overwatch 2** | Raw Input exclusively |

## General Guidelines

### Best Game Genres for Adaptive Controllers
- **Turn-based games** (Civilization, Slay the Spire) — no time pressure
- **Sandbox/creative** (Minecraft, Stardew Valley, Terraria) — relaxed pace
- **Puzzle games** (Portal) — pausable, thoughtful gameplay
- **Platformers with controller support** (Celeste, Hollow Knight) — designed for gamepad
- **Racing** (Rocket League) — joystick maps naturally

### Tips
1. **Always set the game to windowed mode first** before applying borderless
2. **Use Game Focus Mode** (View → Game Focus Mode) alongside borderless for best results
3. **Lower the cursor release interval** (16–30ms) if the game keeps re-locking your cursor
4. **Use ViGEm Xbox profile** for games with native XInput support (most modern games)

### Reporting New Games
If you test a game that works (or doesn't), please open an issue on our GitHub repository with:
- Game name and version
- Whether borderless mode worked
- Whether cursor release was needed
- Any notes about controller compatibility

---

*This list is maintained as part of the Project Nimbus source code in `src/borderless.py` and is displayed in-app via View → Borderless Gaming → Compatibility tab.*
