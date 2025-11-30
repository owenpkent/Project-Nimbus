# Game Window Focus Solution - Progress

## Problem Statement

When using Project Nimbus as a touchscreen virtual controller, clicking on the UI causes the game window to lose focus, which breaks gameplay (games pause, input stops).

**Current Setup:**
- Wheelchair Bluetooth connects to laptop only (1 device limit)
- Laptop has touchscreen running Project Nimbus
- Gaming PC runs the actual games
- Synergy extends keyboard/mouse from laptop to gaming PC

## Solutions Evaluated

### ⭐⭐⭐ Top Choice: Moonlight Game Streaming

**Status:** Ready to research/test

**Why it's best for current setup:**
- Game runs on Gaming PC, you interact with laptop screen
- Moonlight has built-in virtual controller passthrough
- No focus issues since game is on different machine
- Replaces Synergy for gaming sessions
- Low latency on local network

**Next steps:**
1. Install Sunshine on Gaming PC
2. Install Moonlight on Laptop
3. Test if vJoy on laptop passes through as Xbox controller to Gaming PC
4. Measure latency and test with actual games

**Resources:**
- Sunshine: https://github.com/LizardByte/Sunshine
- Moonlight: https://moonlight-stream.org/

---

### ⭐ Backup: Windows API No-Focus Mode

**Status:** Implementation plan complete, ready to prototype

**How it works:**
- Make Project Nimbus window not steal focus when clicked
- Game stays focused even when interacting with controller UI
- Single machine solution, no extra software

**Implementation steps:**
1. Try Qt flag `Qt.WindowDoesNotAcceptFocus` (5 min test)
2. If works → add menu toggle, done
3. If not → use Windows API `WS_EX_NOACTIVATE` via ctypes
4. Add native event filter if mouse still activates window
5. Test with touch input
6. Add "Gaming Mode" toggle in menu

**Code locations:**
- `src/window_utils.py` - Windows API helpers
- `src/qt_qml_app.py` - Initialize no-focus mode
- `qml/Main.qml` - Add menu option and window flags

**Detailed plan:** See `game-focus-solutions.md` section 4

---

## Other Solutions Considered

| Solution | Verdict | Why |
|----------|---------|-----|
| Borderless Gaming | ❓ Needs testing | May not solve focus issue directly |
| VirtualHere | ❓ Uncertain | Unclear if works with virtual devices like vJoy |
| Steam Big Picture | ✅ Partial | Only works with Steam games |
| Remote Desktop | 🔬 Workaround | Practical but requires extra setup |

---

## Recommended Path Forward

### Phase 1: Test Moonlight (Week 1)
- [ ] Install Sunshine on Gaming PC
- [ ] Install Moonlight on Laptop
- [ ] Test vJoy passthrough
- [ ] Measure latency
- [ ] Test with a game

**Decision point:** If latency is acceptable and vJoy passes through → use Moonlight as primary solution

### Phase 2: Implement No-Focus Mode (Parallel or if Moonlight fails)
- [ ] Add Qt window flags to Main.qml
- [ ] Test with Notepad (simple focus test)
- [ ] Test with actual game
- [ ] Add menu toggle for "Gaming Mode"
- [ ] Add visual indicator when active

**Decision point:** If Qt flag works → quick win. If not → implement Windows API approach

### Phase 3: Integration & Polish
- [ ] Document chosen solution in README
- [ ] Add user guide for setup
- [ ] Test with multiple games
- [ ] Handle edge cases (window resize, minimize, etc.)

---

## Technical Notes

- Windows gives focus to whatever window receives user input
- Touch input treated same as mouse clicks for focus purposes
- vJoy input typically requires window focus unless app handles background input
- Moonlight's controller passthrough is designed for this exact use case
- Qt's `WindowDoesNotAcceptFocus` may not work on all systems - Windows API is more reliable

---

## Files Created

- `research/game-focus-solutions.md` - Detailed analysis of all solutions
- `research/PROGRESS.md` - This file

## Next Meeting

Decide: Start with Moonlight research or Windows API prototype?
