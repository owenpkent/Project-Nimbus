# Controller Mode Enforcement — Making Games Release the Mouse

**Status:** 🟢 Implemented (v1.4.1) — Needs Testing  
**Related:** `research/in-progress/borderless-mouse-capture.md`, `research/in-progress/mouse-capture-problem.md`

## The Insight

Most modern games have **dual input detection**:

| Last Input Detected | Game Behavior |
|---|---|
| Mouse/keyboard | Switch to M/KB mode → capture cursor → show keyboard prompts |
| Controller (XInput) | Switch to controller mode → **release cursor** → show gamepad prompts |

Project Nimbus already creates a virtual Xbox 360 controller via ViGEm. The game *can* see it. The problem is that the user's physical mouse movement also reaches the game, causing it to switch back to M/KB mode and re-capture the cursor.

**Solution:** Send a constant stream of controller input through ViGEm so the game stays in controller mode and voluntarily stops capturing the mouse. No more fighting `ClipCursor` in a race condition — the game cooperates because it thinks a gamepad is the active input device.

---

## Why v1.4.0's Approach Failed

v1.4.0 used `ClipCursor(NULL)` polling at 2ms intervals to fight games that re-apply `ClipCursor` every frame. Problems:

1. **Race condition** — Even at 2ms, some games re-clip faster or use multiple clip calls per frame
2. **Cursor jitter** — The cursor alternates between free and clipped, never staying free long enough to reach Nimbus
3. **Doesn't address root cause** — The game WANTS to capture the mouse because it's in M/KB mode. We're treating the symptom (cursor confinement) not the cause (input mode)
4. **Completely ineffective for Raw Input games** — `ClipCursor` is irrelevant when the game reads mouse delta directly from the HID driver

## Why Controller Mode Works

Instead of fighting the game's mouse capture, we make the game **stop wanting to capture**:

1. ViGEm virtual Xbox controller already exists (from v1.4.0)
2. We send tiny analog stick oscillations (amplitude 0.02, below any deadzone)
3. The game's `XInputGetState()` sees packet number changes → "controller is active"
4. Game switches to controller mode → hides mouse cursor → **stops calling ClipCursor**
5. Mouse is now free because the game isn't trying to capture it
6. User interacts with Nimbus using the free mouse
7. Nimbus translates mouse/touch into controller input via ViGEm
8. Game receives controller input → stays in controller mode

This is a **positive feedback loop** — controller mode makes the mouse free, the free mouse lets the user control Nimbus, Nimbus sends controller input, which keeps the game in controller mode.

---

## Implementation: `src/mouse_hider.py`

### Component 1: Controller Keep-Alive Pulse

A dedicated thread sends tiny stick oscillations at 30Hz (configurable 5-120Hz):

```
angle = (tick % 60) * (2π / 60)
micro_x = 0.02 * cos(angle)    // amplitude 0.02 — below all deadzones
micro_y = 0.02 * sin(angle)
gamepad.left_joystick_float(micro_x, micro_y)
gamepad.update()
```

This produces real `XInputGetState` packet number changes that games detect as "controller is active."

**Why oscillation, not static?** Some games check for input *delta* (change from last frame), not just absolute state. A static value of 0.02 would only register once. Oscillation produces a different value every frame.

**Why 0.02 amplitude?** Typical game deadzones are 0.1-0.3 (10-30%). Our amplitude of 0.02 (2%) is well below this, so the in-game character doesn't actually move, but `XInputGetState` still reports a state change.

### Component 2: Initial Controller Burst

When Controller Mode starts, we send a rapid burst of 10-15 larger (but still sub-deadzone) stick deflections at 60fps timing. This forces an immediate mode switch rather than waiting for the keep-alive to accumulate.

```
for i in range(10):
    val = 0.05 * (1 if i % 2 == 0 else -1)
    gamepad.left_joystick_float(val, val)
    gamepad.update()
    sleep(0.016)
```

### Component 3: WH_MOUSE_LL Hook (Mouse-Over-Game Detection)

A global low-level mouse hook detects when the cursor moves over the game window. When this happens, we immediately send a controller burst to counter the game's automatic switch to M/KB mode.

**Key design decision:** We do NOT suppress mouse events in the hook. Suppressing in `WH_MOUSE_LL` would freeze the cursor on screen (the cursor position update is part of the suppressed message). Instead, we detect and counter.

The hook runs on a dedicated thread with a Win32 message pump (required for `WH_MOUSE_LL`).

### Component 4: Integrated ClipCursor Release

Every 4th pulse cycle, the keep-alive thread also calls `ClipCursor(NULL)` as a fallback. This catches edge cases where the game briefly re-clips before the controller mode signal takes effect.

---

## Bridge API (for QML)

| Slot | Description |
|---|---|
| `startControllerMode(game_hwnd, pulse_hz)` | Start controller mode enforcement for a specific game |
| `stopControllerMode()` | Stop controller mode |
| `isControllerModeActive()` | Check if running |
| `sendControllerBurst()` | One-shot burst without continuous keep-alive |
| `startFullGameMode(game_hwnd, pulse_hz)` | **Recommended**: borderless + cursor release + controller mode |
| `stopFullGameMode(game_hwnd)` | Stop everything and restore window |
| `getControllerModeStats()` | JSON stats: pulses sent, mouse events detected, bursts |

---

## Game Compatibility Analysis

### Best Case: Games with Clear Dual Input Detection

These games cleanly switch between M/KB and controller mode based on the last input received. Controller Mode Enforcement should work perfectly:

- **Elden Ring / Dark Souls III** — FromSoftware games explicitly switch UI prompts and mouse behavior
- **No Man's Sky** — Clear controller/M/KB mode split
- **Hollow Knight** — Unity engine with standard dual detection
- **Skyrim** — Bethesda's input system has explicit mode switching
- **Rocket League** — Designed for controller, M/KB is secondary
- **Hades** — Clean input mode detection
- **Stardew Valley** — XNA/MonoGame with standard XInput detection

### Partial: Games with Aggressive Mouse Detection

Some games switch back to M/KB mode on *any* mouse movement, even tiny jitter. For these, the WH_MOUSE_LL counter-burst is critical — we need to overwhelm the mouse input with controller input.

- **Minecraft (Java Edition)** — Checks mouse position frequently
- **Terraria** — May need higher pulse frequency

### Incompatible: Raw Input + Anti-Cheat

Games that use Raw Input for mouse AND have anti-cheat cannot be helped by any external approach:

- **Valorant** (Vanguard), **CS2** (VAC), **Fortnite** (EAC), **Apex Legends** (EAC)

For these, the only solutions remain: second monitor, tablet input, or game streaming.

---

## Testing Plan

### Priority 1: Verify Core Mechanism
1. Launch a known dual-input game (Minecraft, Skyrim, or Elden Ring)
2. Enable Controller Mode via `startControllerMode(game_hwnd, 30)`
3. Verify: Game shows controller prompts (not keyboard)
4. Verify: Mouse cursor is free to move to Nimbus
5. Verify: Interacting with Nimbus widgets sends controller input to game
6. Verify: Game stays in controller mode even when mouse moves over it

### Priority 2: Edge Cases
1. Start game BEFORE enabling Controller Mode — does the burst switch it?
2. Alt+Tab away and back — does controller mode persist?
3. Very high refresh rate game (144fps+) — is 30Hz pulse enough?
4. Game with no controller support — does it cause issues?

### Priority 3: Performance
1. CPU usage of the pulse thread (should be <1%)
2. Input latency impact — does the keep-alive interfere with real Nimbus input?
3. Memory usage of the WH_MOUSE_LL hook thread

---

## What Didn't Work (v1.4.0 Lessons)

1. **Pure ClipCursor(NULL) polling** — race condition, cursor jitter, doesn't address root cause
2. **Thread-input attachment** (`AttachThreadInput`) — helps but doesn't solve timing issues
3. **Full virtual screen clip** — setting ClipCursor to the entire virtual screen; games detect this and re-clip to their own window

## What We Haven't Tried Yet (Future)

1. **Keyboard hook** — extend to suppress keyboard input going to game (prevents accidental M/KB switch from keyboard)
2. **Auto-detection of mode switch** — monitor game window for cursor visibility changes; if cursor appears, the game switched to M/KB mode, trigger immediate burst
3. **Per-game pulse profiles** — some games may need different pulse frequency or amplitude
4. **Mouse position warping** — when cursor release is active, warp cursor to Nimbus window to prevent accidental mouse-over-game

---

## References

- `XInputGetState` MSDN: https://learn.microsoft.com/en-us/windows/win32/api/xinput/nf-xinput-xinputgetstate
- `XINPUT_STATE.dwPacketNumber`: https://learn.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_state
- ViGEm/vgamepad: https://github.com/yannbouteiller/vgamepad
- WH_MOUSE_LL: https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelmouseproc
- Related: `research/in-progress/borderless-mouse-capture.md`
- Related: `research/in-progress/mouse-capture-problem.md`
