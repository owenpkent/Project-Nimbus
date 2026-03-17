# Mouse Capture Problem

**Status:** � In Progress — Controller Mode Enforcement implemented (v1.4.1), needs testing

## The Problem

Some games capture/lock the mouse cursor, preventing the user from clicking on Project Nimbus at all. This is separate from the focus issue (which is solved by Game Focus Mode).

This primarily affects mouse-based input. Touchscreen input may not be subject to mouse capture, but this hasn't been tested yet.

**Impact:** Users who cannot use a keyboard to Alt+Tab are completely blocked from using Nimbus with these games.

## Current Workaround

1. Have a caregiver press Alt+Tab to switch focus
2. Once Project Nimbus has focus, it works normally
3. Game Focus Mode then restores focus to the game after each interaction

This requires assistance and defeats the goal of independent use.

## Potential Solutions to Research

### 1. Borderless Windowed Mode
- Many games have "Borderless Windowed" or "Windowed Fullscreen" option
- This typically doesn't capture the mouse
- User can move cursor to Project Nimbus on a second monitor or overlay
- **Effort:** Documentation only
- **Limitation:** Not all games support it

### 2. Multi-Monitor Setup
- Game on primary monitor (even fullscreen)
- Project Nimbus on secondary monitor/tablet
- Some games release mouse at screen edges
- **Effort:** Documentation + testing
- **Limitation:** Requires second display

### 3. Global Hotkey to Release Mouse
- Implement a global hotkey (e.g., F12) that forces mouse release
- Would require low-level keyboard hook
- Could trigger Alt+Tab programmatically
- **Effort:** Medium (Windows hooks)
- **Limitation:** Still requires *some* keyboard access

### 4. Overlay Mode
- Run Project Nimbus as a game overlay (like Steam Overlay)
- Would require significant architectural changes
- May conflict with anti-cheat systems
- **Effort:** High
- **Limitation:** Complex, anti-cheat risk

### 5. Separate Touch Input Device
- Use a separate touchscreen/tablet for Project Nimbus
- Touch input may not be captured by the game (untested)
- Could use Spacedesk or similar for wireless display
- **Effort:** Documentation + testing
- **Limitation:** Requires extra hardware; touchscreen support not yet tested

### 6. Moonlight Game Streaming
- Stream game from Gaming PC to Laptop via Moonlight
- Game runs on Gaming PC, user interacts with laptop
- Moonlight has built-in virtual controller passthrough
- **Effort:** Testing/documentation
- **Limitation:** Adds latency, requires Sunshine setup

### 7. Steam Input / Big Picture
- Steam's overlay can work even when games capture mouse
- Could potentially integrate with Steam Input API
- **Effort:** Research
- **Limitation:** Steam games only

## Research Tasks

- [ ] Test multi-monitor behavior — Do games release mouse at screen edges?
- [ ] Investigate global hotkeys — Can we implement Alt+Tab trigger?
- [ ] Test Moonlight — Does vJoy on laptop pass through to Gaming PC?
- [ ] Research overlay solutions — Can we run as a game overlay?
- [ ] Document which games support borderless windowed mode
- [ ] **Test touchscreen input** — Does touchscreen avoid mouse capture? (Future feature)

## Technical Notes

- Mouse capture is a **separate problem from focus** — even with Game Focus Mode, if the game captures the mouse, the user can't click on Nimbus at all
- Touch input is treated the same as mouse clicks
- Some games have "background input" options that help, but many don't
- Controller input (XInput/DirectInput) typically requires window focus unless app specifically handles background input

## v1.4.1 Solution: Controller Mode Enforcement

**Key insight:** Instead of fighting the game's mouse capture (`ClipCursor` race condition), make the game **voluntarily release the mouse** by keeping it in controller mode.

Most games have dual input detection — when they see XInput controller input, they switch to "controller mode," show gamepad prompts, and **stop capturing the mouse**. Since Nimbus already creates a virtual Xbox 360 controller via ViGEm, we can exploit this by sending continuous keep-alive signals.

### How it works
1. ViGEm virtual Xbox controller already exists
2. `mouse_hider.py` sends tiny sub-deadzone stick oscillations at 30Hz
3. Game's `XInputGetState()` sees packet changes → "controller is active"
4. Game switches to controller mode → stops calling `ClipCursor`
5. Mouse is free → user interacts with Nimbus
6. Nimbus sends real controller input → game stays in controller mode

### Implementation
- **Module:** `src/mouse_hider.py`
- **Bridge slots:** `startControllerMode()`, `stopControllerMode()`, `startFullGameMode()`
- **Combined approach:** `startFullGameMode()` runs borderless + cursor release + controller mode
- **See:** `research/in-progress/controller-mode-enforcement.md` for full technical details

### What still needs testing
- [ ] Verify with Minecraft (Java Edition) — ClipCursor game
- [ ] Verify with Elden Ring — dual input game
- [ ] Verify with No Man's Sky — ViGEm + controller mode end-to-end
- [ ] Measure CPU impact of 30Hz pulse thread
- [ ] Test with games that have no controller support (edge case)

## Priority

**HIGH** — This is a core accessibility issue that prevents independent use for many games.
