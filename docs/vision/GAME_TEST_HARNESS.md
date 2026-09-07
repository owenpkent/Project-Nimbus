# Game Test Harness: Automated Tests Against Real Games

> **Status:** designed, built and run 2026-09-07 on `feature/game-test-harness`. The harness is `tests/game_harness.py`, the runner is `tests/probe_game_harness_windows.py`, the recipes are in `tests/games/`, and the first Spectator+ feature it made possible is in `src/spectator/` (section 4.7). Against Left 4 Dead 2 the pad calibration passes 14/14 and the Nimbus end-to-end run 17/17, primitives included; Elden Ring, with no console, passes 11/11 on frame verdicts. The numbers and what the games taught are in section 8.
>
> **Relationship to Spectator+:** the loop this harness runs (put the game in a known state, send controller input, read what the game did) is the loop a Spectator+ agent runs. Section 4.7 says what carries over.

---

## 1. Summary

Nimbus is tested against real games by hand, and once by script: `tests/probe_game_deadzone_windows.py` (aim assistance, layer 3) launches nothing, waits for a game window, holds a virtual right stick at a few magnitudes, and decides "moved" or "still" from how many pixels of the game window changed. That found the game's deadzone and proved the anti-deadzone clears it. It cannot say how far the camera turned, whether the player moved forward, or whether a button reached the game, and it needs the game launched by hand in the right order.

This document is the plan and the record for a harness that makes those measurements unattended, in numbers, from the game itself:

- **Recipes** (`tests/games/<game>.json`): how to launch a game into a playable state, what window to look for, which oracle reads its state, and where to put the player for a repeatable start.
- **Oracles**: the Source engine's own console (`getpos`, `setpos`, `setang`, echoes, all through a console log on disk) for ground truth in degrees and units, and the existing frame differencing for games with no console.
- **Actuators**: a ViGEm pad the harness owns (fast, exact, for calibrating the game), and the real Nimbus app in-process, driven by synthesized pointer events on its widgets (the thing being tested).
- **An environment** with `launch`, `wait_ready`, `reset`, `step`, `observe` and `close`: the environment shape Spectator+ needs, delivered first as a test fixture.
- **A runner** that produces a results table per game and per actuator, in the style of the driver probes.

The first target is Left 4 Dead 2: no anti-cheat, so it starts under test signing; a Source engine, so it has a console; already installed on the dev machine with a known launch line.

---

## 2. What automated game testing has to answer

Three questions, in increasing order of difficulty:

1. **Does the game read the pad at all?** (Player one, XInput present at launch, controller mode on.) Frame differencing answers this.
2. **What does a given stick input do?** Degrees per second of yaw, units per second of movement, which direction, above what magnitude. Frame differencing cannot answer this; it says only "changed".
3. **Does Nimbus's smallest, largest and typical input do the right thing in the game?** The end-to-end claim of the aim work, restated in game units: a one-pixel drag turns the camera by so many degrees per second.

Spectator+ adds a fourth: **can a scripted or learned action reach a goal?** "Turn to face 90 degrees left" needs the answer to question 2 to be calibrated and the answer to question 3 to be executed through the real bridge. So the oracle is the whole problem. A harness without ground truth can only test question 1.

### 2.1 Where ground truth can come from

| Oracle | Games | Cost | What it gives |
|---|---|---|---|
| Frame differencing (exists) | any | none | moved / still against a noise floor |
| Game console log (Source: `-condebug`, `getpos`, `setpos`, `setang`, `echo`) | Source engine titles (Left 4 Dead 2, Half-Life 2, Portal 2, Team Fortress 2, Counter-Strike: Source) | a cfg file and a key bind | position, view angles, button echoes, deterministic resets |
| HUD reading (OpenCV template matching, OCR) | any with a readable HUD | opencv, easyocr; per-game templates | compass, ammo, health, crosshair state |
| Vision-language judge (a model asked a yes or no question about two frames) | any | an API key or a local model; seconds per answer | coarse semantic verdicts, no numbers |
| Memory reading, hooks | any without anti-cheat | Cheat Engine style tooling | exact state; fragile, and the wrong side of the line for an accessibility project |
| A purpose-built test game | none real | a small pygame or Godot target | exact state over a socket; says nothing about real games |

The console log is the only one that is both exact and cheap. It is limited to Source games, which is acceptable: Left 4 Dead 2 is already the reference title for everything that cannot run under anti-cheat, and the harness is built so a second oracle slots in per recipe.

---

## 3. Options considered

| # | Option | Testing gets | Spectator+ gets | Decision |
|---|---|---|---|---|
| 1 | A recipe runner over the existing frame-differencing probe | a regression matrix over games and modes | "the game is reachable" | the runner shape is kept; frame differencing stays as the fallback oracle |
| 2 | Ground truth from the game console | numbers: degrees, units, echoes; deterministic resets | an honest `reset` and `observe` | **built** for Source games |
| 3 | A vision oracle (templates, OCR, a model as judge) | game-agnostic verdicts | the observation layer for non-console games | later, when a non-Source game matters |
| 4 | A Gymnasium-style environment around the real game | conformance tests: reset, step, observe, latency | the environment itself | **built** as `GameEnv`, oracle and actuator pluggable |
| 5 | Spectator+ v0 as scripted primitives with a real-game test each | the spec, as tests | the first user-facing feature | **built** on top of 2 and 4; section 4.7, measured in section 8 |
| 6 | A purpose-built deterministic test game | a hardware-free pipeline check | nothing | not now |

---

## 4. Design

### 4.1 Recipes

One JSON file per game in `tests/games/`. A recipe says how to launch the game into a playable state and how to read it:

```json
{
    "name": "left4dead2",
    "title": "Left 4 Dead 2",
    "process": "left4dead2.exe",
    "steam_exe": "C:\\Program Files (x86)\\Steam\\steam.exe",
    "steam_app_id": 550,
    "game_dir": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Left 4 Dead 2",
    "launch_args": ["-novid", "-windowed", "-noborder", "-w", "1280", "-h", "720",
                    "-condebug", "+sv_cheats", "1", "+map", "c1m2_streets", "+exec", "nimbus_harness"],
    "window_timeout_s": 300,
    "ready_timeout_s": 240,
    "oracle": {
        "type": "source_console",
        "mod_dir": "left4dead2",
        "cfg_name": "nimbus_harness",
        "base_cfg": "360controller",
        "pose_command": "getpos_exact",
        "pose_key": "F7",
        "reset_key": "F8",
        "button_echo": {"L_SHOULDER": "NIMBUS_BUTTON_LB"}
    },
    "reset_pose": null,
    "turn_right_sign": -1,
    "notes": "..."
}
```

- `title` is the window-title substring the harness looks for; `process` is what it kills at the end.
- `launch_args` is the exact Steam launch line, kept literal so a person can paste it. For a `source_console` recipe the harness checks that `-condebug` and `+exec <cfg_name>` are present.
- `oracle.type` selects the oracle; `frame_diff` needs no other keys.
- `reset_pose` is where `reset()` puts the player: `{"pos": [x, y, z], "ang": [pitch, yaw, roll]}`. When it is `null` the first pose read after the game is ready becomes the session's reset pose, and the runner prints it so it can be written into the recipe. A recipe with a fixed pose is a repeatable test; one without is a first run.
- `ready_sequence` (optional) is the list of waits and button presses that take a game from its title screen into a map, for games with no `+map`: `{"wait": 25}`, `{"press": [1], "hold": 0.2}`, `{"wait_until_control": {"rx": 1.0}, "interval": 5, "timeout": 150}`, which holds the stick every few seconds until the picture moves, and `{"press_until_control": [1], "action": {"rx": 1.0}, ...}`, which does the same but presses the buttons after each failed test. Menus and loading screens ignore a stick and the world does not, and "moved" is a twentieth of the sampled frame, because a menu's shimmer changes a few hundred samples and a camera turn tens of thousands. The test runs before the press each cycle, so once the stick works nothing more is pressed. Each step takes an optional `note`. `warmup_s` is the fixed wait the `frame_diff` oracle counts as readiness. The Elden Ring recipe is a wait for the logos and one `press_until_control`.

### 4.2 The launcher, and the launch-order rule

`Launcher.launch()` deletes the previous console log, writes the harness cfg (section 5), and runs `steam.exe -applaunch <id> <args>`. Steam starts if it is not running, and is left running at the end; only the game process is killed.

The pad exists before the game is launched. Source decides at start-up whether an XInput controller is present and never reads one created later (measured 2026-09-06 in the aim work: the mouse moved the camera, the pad did not, and the HUD showed the generic JOY3 glyph). The environment therefore builds its actuator in `__init__` and launches the game afterwards, so the rule is enforced by construction rather than by remembering the order of two commands. In Nimbus mode it is Nimbus's pad that has to exist first, so the app is started in-process, then the game is launched.

### 4.3 Oracles

An oracle answers `pose()` (a position and view angles, or `None` when the game has none), `ready()` (the game is in a state where input does something), `reset(pose)`, `wait_echo(marker)` for button checks, and `frame()` for the picture. Both oracles keep the frame-differencing path, so every step also records how many samples of the window changed, and the two verdicts can be compared.

**`source_console`.** The game is launched with `-condebug`, which appends every console line to `<mod_dir>/console.log`, flushed per line. The harness cannot type into the console (it is disabled in controller mode and typing into a game is fragile), so it does not: a generated cfg binds two keyboard keys, F7 to `getpos_exact` and F8 to `exec nimbus_harness_reset`, a second generated cfg holding `sv_cheats 1; setpos_exact x y z; setang p y r; echo NIMBUS_RESET_DONE` for the reset pose (rewritten whenever the pose changes, since `exec` re-reads the file), and the harness presses them with `SendInput` while the game is in the foreground and reads the answer from the log. `getpos_exact` prints a line of the form `setpos_exact x y z;setang p y r` giving the player's origin rather than the eye position, so a reset lands the player on the floor instead of dropping it from eye height; the line is parsed with a regular expression from the part of the log written after the key press. Readiness is "a pose answers", polled every few seconds, since the command prints nothing until the local player exists in a map. A button check rebinds one pad button to `echo <marker>` and waits for the marker in the log. The cfg runs `exec 360controller` first, because that file starts with `unbindall`, then adds the binds, so nothing the harness needs can be undone by the game's own controller setup. F9 and F10 are avoided: F10 is a system key on Windows and arrives as a different message.

**`frame_diff`.** The capture and differencing of `tests/probe_game_mouselook_windows.py`: a sampled RGB difference between two captures of the client area, `MOVED` above three times the idle noise floor, `STILL` below twice it. `pose()` is `None`, `reset()` is a no-op, readiness is a fixed warm-up.

### 4.4 Actuators

An actuator takes an action, a dictionary with any of `lx`, `ly`, `rx`, `ry` (minus one to one, right and up positive as XInput has it), `lt`, `rt` (zero to one) and `buttons` (a list of the bridge's button ids, 1 to 14 under ViGEm), and applies it. `release()` centres everything.

**`pad`.** A `vgamepad` Xbox 360 pad the harness owns. Exact and fast: what the harness asks for is what the game receives, so this is the actuator for calibrating a game.

**`nimbus`.** The real QML app in-process, the way `tests/probe_stick_shaping_windows.py` runs it: the bridge, the QML engine and the profile are the real ones, the pointer is synthesized `QMouseEvent`s on the joystick and button widgets, and the ViGEm pad is the bridge's own. A stick action becomes a drag of `value * travel` pixels from the widget's centre (`travel` is the widget's `travel_px`, else its drawn radius), so the whole shaping chain runs (deadzone, curve, anti-deadzone floor, extremity cap); the actuator reports what the bridge actually sent from the ViGEm interface's `current_values` beside what the game did, and the expected values come from the bridge's own resolved parameters through `shape_magnitude`, never from a number in this document. The app is placed beside the game window, never over it. By default the run uses a throwaway copy of the bundled `adaptive_platform_2` profile written into the user profiles folder and removed afterwards, so the result does not depend on what the user has done to their own copy; `--profile <id>` runs an existing profile instead. When several widgets could take the press (the user's copy of the bundled profile has two overlapping left sticks), the actuator picks the topmost one whose centre nothing later in the layout covers, because that is where a real press would land. `controller_config.json` is restored afterwards.

### 4.5 The environment

```python
env = GameEnv(recipe, actuator="pad", frames_dir=...)   # the pad exists now
env.launch()                                            # Steam launch, window found
env.wait_ready()                                        # the oracle says the game is playable
env.reset()                                             # known pose (or record one)
obs0 = env.observe()                                    # {"pose": {...}, "frame": ..., "t": ...}
obs1 = env.step({"rx": 0.6}, hold=1.0)                  # apply, hold, release, settle, observe
env.close()                                             # release, kill the game, restore
```

`step` returns the observation after the hold plus the deltas from the observation before it: yaw and pitch, horizontal distance, vertical distance, and the changed-sample count of the frame difference. With a console oracle the pose is also read through the hold, about twenty times a second, and the yaw delta is the sum of the wrapped steps between reads: a full deflection turns past 180 degrees inside a second (480 degrees in one second on Left 4 Dead 2, measured once the harness stopped folding it), so a single before-and-after read gives the wrong angle. The folded value is kept beside it as `d_yaw_wrapped`. The results JSON is a list of those.

Sign conventions, so numbers in the results log read the same way everywhere: `rx` positive is stick right; Source yaw increases turning left, and Left 4 Dead 2's `joy_yawsensitivity` is negative, so stick right should give a negative yaw delta. Pitch is positive looking down in Source. Both are measured, not assumed; the runner's direction checks say what was found.

### 4.6 The runner and its checks

`tests/probe_game_harness_windows.py --game left4dead2 --actuator pad` runs, in order:

| Check | Pass rule |
|---|---|
| G0 launch | the window appears within `window_timeout_s`; with `source_console`, the console log exists |
| G1 ready | the oracle reports ready within `ready_timeout_s`; a pose is read |
| G2 reset | after `reset()` the pose is within 2 units and 1 degree of the reset pose |
| GS walk survey (`--survey-walk`) | a second of left stick in each of eight headings from the reset spot; the reset pose is turned to the longest run, which must exceed 150 units; `--write-reset-pose` writes it into the recipe |
| G3 idle | one second of no input: yaw within 0.5 degrees, position within 1 unit; the frame noise floor is recorded |
| G4 yaw control | `rx` at 1.0 for the hold: more than 10 degrees, and the direction is the recipe's turn-right sign |
| G5 yaw sweep | `rx` at each of the sweep magnitudes; the table of degrees per second; the first magnitude past 1 degree is the game's deadzone; the frame-difference verdict for each step is recorded beside the ground truth |
| G6 yaw left | `rx` at minus 0.6: the opposite sign, and a rate within 25 percent of the right turn at 0.6 |
| G7 pitch | `ry` at 0.6: more than 1 degree of pitch; the sign is recorded |
| G8 move | `ly` at 1.0 for one second: more than 20 units of horizontal travel; units per second recorded |
| G9 button | the pad button bound to the echo marker: the marker appears in the log within two seconds |
| G10 release | after everything: one second idle, pose unchanged (nothing is stuck) |
| G11 latency | `rx` at 1.0 with the pose polled every 60 ms: the first sample whose yaw moved, as a coarse latency bound |
| G12 calibration | yaw against hold time (0.1, 0.25, 0.5 and 1 s) at 0.40, 0.60 and 1.00, and forward travel against hold time at full left stick; every column grows with the hold. `--write-calibration` writes the table to `src/spectator/calibrations/<game>.json` |

With `--actuator nimbus` the same environment runs with the real app, and the checks are the end-to-end ones:

| Check | Pass rule |
|---|---|
| N0 app | the QML window registered with the bridge, ViGEm mode, the profile's rx/ry stick found, game launched second and ready |
| N1 full drag | a drag to the stick's edge turns the camera more than 10 degrees, and the bridge sent its own ceiling for that stick (0.95 on the bundled profile) within 0.02 |
| N2 one-pixel drag | a 1 px drag turns the camera by more than 1 degree, and the bridge sent its own floor for that stick: the anti-deadzone clears the game's threshold, now in degrees |
| N3 release | the stick released reads exactly zero at the bridge and the pose is stable |
| N4 button | a click on the LB widget produces the echo marker in the log |
| N5 left stick | a full drag up on the left stick moves the player more than 20 units, and the bridge sent its ceiling |

then the Spectator+ primitives (section 4.7) through the bridge's own runner, measured by the game:

| Check | Pass rule |
|---|---|
| P0 calibration | the bridge's runner loads `src/spectator/calibrations/<game>.json` |
| P1, P2, P3 turn | turn right 90, left 45, right 10 degrees: the yaw delta is within 15 percent or 5 degrees, whichever is larger |
| P4 walk | walk 100 units: the horizontal travel is within 20 percent or 10 units |
| P5 stop | a 400-unit walk cut short after 0.3 s: the bridge reads zero on the stick and the player stays put for the next second |

Each check prints one line and lands in `tests/probe_frames/harness_<game>_<actuator>.json` with every observation. Frames are saved beside it.

### 4.7 Spectator+ v0: scripted primitives

Built the same day as the harness, as the first Spectator+ feature a user could touch, with no model behind it. `src/spectator/` holds two modules:

- **`calibration.py`.** A game's measured stick response, from G12: for each right-stick magnitude, yaw delta against hold time; for the left stick up, travel against hold time. `hold_for(samples, amount)` interpolates the hold that yields an amount, linearly between samples and along the last segment beyond them. `plan_turn(degrees)` picks the smallest magnitude whose hold fits between 0.2 and 2 s (a small angle gets a slow stick so timing error stays small; a large one gets the fastest), `plan_walk(units)` does the same for travel. The table needs several holds per magnitude because Source ramps stick input above `joy_lowend`: the first tenth of a second turns far less than a tenth of the one-second figure.
- **`primitives.py`.** `PrimitiveRunner`, a `QObject` that executes a plan as timed steps on a precise `QTimer`, never blocking the UI thread: set the axis, wait the hold, zero it. One primitive at a time; `turn`, `walk` and `press` return the plan or `None`; `stop()` cancels and zeroes everything the plan touched; every plan ends with a release whatever happens; `started` and `finished(name, completed)` signals for a future UI.

The bridge owns the runner through `get_spectator()`, created on first use and bound to `setAxis` and `setButton`, so a primitive's output goes through the active driver interface and its limits. It bypasses the widget shaping on purpose: the shaping is for the user's own hand, and "turn 90 degrees" has to be the same turn whatever curve the user has on their stick. A profile switch and the Ctrl+Alt+F12 stop also cancel a running primitive.

What is not there yet: a way to trigger a primitive from the UI or from voice (the concept document's command palette), a closed loop (the runner cannot read the game, so it trusts the calibration; the harness measures how far that trust goes, section 8), and calibrations for any game but Left 4 Dead 2. The environment stays in `tests/` until the app has a consumer for it.

---

## 5. Source engine details

What the `source_console` oracle relies on, checked against the Left 4 Dead 2 install on the dev machine:

- `-condebug` on the launch line writes `left4dead2/console.log`, appending; the harness deletes it before each launch. `con_logfile` exists too but is not needed.
- `getpos`, `getpos_exact`, `setpos`, `setpos_exact` (client), `setang` and `sv_cheats` (client, server, engine) are present in the binaries. `setpos`, `setpos_exact` and `setang` need `sv_cheats 1`, which the launch line sets before `+map` and the reset cfg sets again. `getpos` prints the eye position, `getpos_exact` the origin; the harness uses the exact pair so a reset is a teleport onto the floor.
- `cfg/valve.rc` runs `exec autoexec.cfg` and then `stuffcmds` (the `+` commands from the launch line), in order. The harness uses `+exec nimbus_harness`, not `autoexec.cfg`, so nothing persists between sessions; the generated `cfg/nimbus_harness.cfg` and `cfg/nimbus_harness_reset.cfg` are removed at close.
- `cfg/360controller.cfg` begins with `unbindall`, sets `joy_yawsensitivity -1.5`, `joy_pitchsensitivity 1.0`, `joy_response_look 1`, `joy_lowend 0.65`, `joy_lowmap 0.15`, `joy_accelscale 3.0` and `joy_accelmax 4.0`, and binds the pad buttons (`L_SHOULDER` to `toggle_duck`, `BACK` to `togglescores`). The harness cfg execs it first and then binds `F7`, `F8` and the echo button, so the pad keeps its normal layout except for the one button used as a marker.
- Keys are injected with `SendInput` virtual-key events carrying their scan code, because Source maps keys by scan code; they arrive through the normal message path even with `joystick 1`. The console itself stays disabled (`con_enable 0` in the user's config).
- A map started with `+map` is a local listen server with the player in the first safe room of `c1m2_streets`, which the aim work found stable enough for measurements (the infected cannot enter, the bots stay).

---

## 6. How to run

The pad calibration, unattended, about four minutes including the game start:

```
venv\Scripts\python tests\probe_game_harness_windows.py --game left4dead2 --actuator pad
```

The end-to-end run with the real app, same environment, including the Spectator+ primitives:

```
venv\Scripts\python tests\probe_game_harness_windows.py --game left4dead2 --actuator nimbus
```

The primitives need the calibration the pad run writes with `--write-calibration` (checked in as `src/spectator/calibrations/left4dead2.json`; rerun it after a change to the game's controller cfg or to the harness's hold timing). A game with no console, launched through its title screen by the recipe's `ready_sequence`, about six minutes:

```
venv\Scripts\python tests\probe_game_harness_windows.py --game eldenring --actuator pad
```

Run them in separate invocations, with the game quit in between (the runner does this), so each session's pad is player one. `--keep-game` leaves the game running for a look; `--sweep 0.2,0.26,0.28,0.3,0.4,0.6,0.8,1.0` and `--hold 1.0` change the yaw sweep; `--write-reset-pose` writes the first pose read into the recipe; `--profile <id>` makes the Nimbus run use an existing profile instead of the throwaway copy of the bundled one. Both need ViGEmBus. Both are safe over TeamViewer: every stimulus is injected, and the game window is left in the foreground only while a step runs. Steam must be able to sign in without a prompt. A pad run takes about two and a half minutes from launch to the game quitting; a Nimbus run about the same.

---

## 7. Limits and open questions

- **Anti-cheat titles** cannot be launched by this harness under test signing, and their state cannot be read from a console anyway. Elden Ring stays on frame differencing, launched by hand.
- **The pose is sampled, not streamed.** Each pose read costs a key press and a log read, about 47 ms on the dev machine, so `observe()` is good to about 50 to 100 ms and the latency check is a bound, not a measurement. Fine for tests and for scripted primitives; a learned agent at frame rate would need `cl_showpos` on screen and a reader, or a plugin.
- **The safe room** has walls within 114 to 140 units in three of eight headings from the reset spot. `--survey-walk` measures all eight and turns the reset pose to the clearest (200 units at yaw 135); a game or map change should rerun it with `--write-reset-pose`.
- **Frame differencing is not trustworthy in this scene.** The survivor bots walk through the view and the flashlight glare flickers, so a one-second noise floor is regularly exceeded with the camera still (section 8). The verdict is recorded beside the ground truth and never used for a pass on a Source game. A recipe for a game with no console should pick a scene without moving actors, or a longer noise measurement.
- **The pad's own deadzone is not the game's.** The harness sends exact XInput values, so the sweep measures the game's threshold (0.26 to 0.28 here). A physical pad would add its own.
- **Where does `GameEnv` live?** In `tests/` until Spectator+ has code in `src/` that imports it.

---

## 8. Results log

Filled in by the runs. Each entry: date, machine, game and map, actuator, the table, and what the game taught.

### 2026-09-07, dev machine, Left 4 Dead 2, `c1m2_streets` safe room, windowed 1280x720, pad actuator

Three runs the same afternoon. **Run 1** parsed nothing: `getpos_exact` prints `setpos_exact x y z;setang_exact p y r`, with `setang_exact` rather than `setang`, so the pattern was widened. **Run 2** (11/12) exposed the readiness gap: the server-side player has a pose while the client still shows the loading screen (an all-zero pose early in the load, then the spawn position), so the harness declared the game ready 23 s after launch on a static picture, measured a frame noise floor of 2, and its idle step then watched the spawn move the player 65 units. Readiness now also needs a live picture (two captures half a second apart differing by more than 50 samples; the loading screen differs by 17) and a pose that holds still for 1.5 s. **Run 3, 12/12**, launch to window 4 s (Steam already running; 24 s when Steam had to start), launch to ready 29 s, frame noise floor 100 in the map, reset pose recorded into the recipe. The right-stick yaw sweep, one second per magnitude, from the same reset pose each time:

| `rx` | yaw delta (deg) | deg/s | changed samples | frame verdict | truth |
|---|---|---|---|---|---|
| 0.20 | +0.00 | 0.0 | 2326 | MOVED | still |
| 0.26 | +0.00 | 0.0 | 4329 | MOVED | still |
| 0.28 | -1.51 | -1.5 | 2598 | MOVED | moved |
| 0.30 | -3.55 | -3.6 | 3683 | MOVED | moved |
| 0.40 | -13.75 | -13.8 | 7307 | MOVED | moved |
| 0.60 | -34.38 | -34.4 | 8584 | MOVED | moved |
| 0.80 | -55.24 | -55.2 | 9213 | MOVED | moved |
| 1.00 | -464.78 (run 3 read -122.78, folded past 180) | -464.8 | 10972 | MOVED | moved |

- **Deadzone** between 0.26 and 0.28, where the frame-differencing probe put it on 2026-09-06 and where the XInput constant of 0.265 says it is. At 0.28 the camera turns 1.5 degrees per second: the anti-deadzone floor is above the threshold, but only just, which is the number to remember when a game feels sluggish at the smallest movement.
- **Rates.** 0.40 gives 14 degrees per second, 0.60 gives 34, 0.80 gives 54, each linear in time. Full deflection is another regime: **481 degrees in one second** (465 in the sweep step), a full circle and a third, because `360controller.cfg` turns on Source's stick acceleration (`joy_accelscale 3`, `joy_accelmax 4`) at the stop and the rate ramps up through the second: 8 degrees in the first tenth, 37 by a quarter second, 124 by half. Runs 2 to 4 reported 116 to 123 for the same step because a single before-and-after read folds anything past 180 degrees back into the range, and the sweep table above carried that folded value until run 5; the harness now reads the pose through the hold (section 4.5) and keeps the folded number beside the real one. A turn primitive has to be calibrated per magnitude and per hold, not by one slope.
- **Symmetry.** Left at 0.60 turned +34.3 degrees per second against -34.4 to the right (ratio 1.00). **Pitch** at 0.60 up: -21.2 degrees in a second (up is negative pitch in Source, so stick up looks up on this config).
- **Movement.** Left stick full up moved the player 114 units in a second from the first reset pose, which turned out to face a wall 114 units away (runs 3 and 4 gave the same 114.1 at every hold). Run 5's walk survey tried eight headings from the same spot (121, 142, 184, 200, 140, 195, 114 and 195 units for yaw 0 to 315) and turned the reset pose to yaw 135, where a second of stick gives 200 units on the floor (`d_z` 0), the survivor's run speed.
- **Button.** The left bumper landed in the console log 31 ms after the pad update, in both runs.
- **Latency.** With the stick at 1.00 and the pose polled as fast as the key-and-log loop allows, the first sample (47 ms) still read zero and the second (94 ms) read 2.3 degrees. So the pad-to-game path is under 94 ms and probably close to 47; a finer bound needs a faster oracle. (Run 5 read zero at 47 and 78 ms and 0.8 degrees at 125 ms: at full deflection the ramp starts slowly, so the first visible degree lags the input path.)
- **Nothing stuck** afterwards: one idle second, pose unchanged.
- **Frame differencing over-reports in this scene.** At 0.20 and 0.26 the camera did not turn at all and the frame still changed by 2,300 and 4,300 samples, far above the 300 threshold: the survivor bots walk through the view and the flashlight glare flickers, and a one-second noise floor does not cover them. The 2026-09-06 measurement got the right answer with the same method because the bots happened to be quiet. With ground truth beside it, the frame verdict is now recorded but never trusted on its own for a Source game.

What the game taught, beyond the numbers: the spawn pose differs per launch (yaw -89.6 in one run, -46.9 in the next, 90 units apart), so the recipe carries a fixed reset pose rather than taking the first read; and `+sv_cheats 1` before `+map` does carry into the listen server, so `setpos_exact` and `setang` work from the first reset.

**Runs 4 and 5**, the same day, added G12, the calibration table for the primitives. Run 4 (12/13) is where the fold showed: at full deflection the half-second hold read 124 degrees and the one-second hold 91, which cannot both be true unless the second wrapped, and the walk table stopped at 114 units for every hold, a wall. Run 5, **14/14**, with the pose read through the hold and the walk survey (GS) turning the reset pose to face the clear run, wrote `src/spectator/calibrations/left4dead2.json`:

| Hold | `rx` 0.40 | `rx` 0.60 | `rx` 1.00 | `ly` 1.00 (units) |
|---|---|---|---|---|
| 0.10 s | -1.2 | -3.1 | -7.7 | |
| 0.25 s | -3.3 | -8.2 | -36.6 | 54 |
| 0.50 s | -6.7 | -16.6 | -123.7 | 120 |
| 1.00 s | -13.6 | -32.9 | -456.5 | 200 |

Below the stop the turn is linear in time at 13.6 and 33 degrees per second. At the stop it is not: a tenth of a second gives 8 degrees, a quarter 37, a half 124 and a second 457, the acceleration ramp. The walk is 200 units per second with about 4 units of coasting after a short hold. The rest of run 5 matched run 3 to a tenth of a degree everywhere below the stop, and this time the frame verdicts agreed with the console at every magnitude, which says how much the earlier disagreement was the bots.

### 2026-09-07, the same game, Nimbus actuator

**Run 1, 10/11.** `switchProfile("adaptive_platform_2")` resolves to the user's copy in the profiles folder, which on the dev machine has an aim stick at sensitivity 18 and extremity 40 and a second, larger left stick laid over the first. Everything the bridge did was right and the one failure was the check's own assumption: a full drag sent 0.600, which is that stick's ceiling, and the game turned 36.6 degrees per second, what the pad calibration gives for 0.60 (34.4); a 1 px drag sent 0.285, that stick's floor, and turned 2.2 degrees per second (the pad: 1.5 at 0.28, 3.6 at 0.30); a click on the LB widget echoed in 62 ms; releasing read exactly zero and left the pose still; the left stick's full drag moved the player 114 units but sent 0.794 instead of 0.95, because the press at the smaller stick's centre landed on the larger stick drawn over it (travel 72.8 px against 56.4, and 56.4 / 72.8 = 0.775 raw, which shapes to 0.794). Three changes followed: the Nimbus run uses a throwaway copy of the bundled profile unless `--profile` says otherwise, the expected values come from the bridge's own parameters, and the actuator picks the topmost widget under a press.

**Run 2, 11/11**, on the throwaway copy of the bundled profile (aim stick travel 160 px, left stick drawn radius 81 px), launch to ready 29 s, noise floor 508 with a bot in view:

| Step | Bridge sent | Expected from the bridge's parameters | Game |
|---|---|---|---|
| full drag on the aim stick | RX +0.950 | 0.950 | -140.4 degrees in the step |
| 1 px drag on the aim stick | RX +0.289 | 0.289 | -2.7 degrees in the step |
| release | all sticks 0.0 | 0 | pose still for a second |
| click on the LB widget | button 5 | | echo in the log after 47 ms |
| full drag up on the left stick | LY +0.950 | 0.950 | 114 units forward in a second |

The step numbers are consistent with the pad calibration once the drag time is counted: the synthesized press and three moves take 125 ms before the one-second hold starts, so the stick is on for about 1.13 s, and 140 degrees over 1.13 s is 125 degrees per second against the pad's 123 at full deflection; the 1 px drag's 2.7 degrees sits between the pad's 1.5 at 0.28 and 3.6 at 0.30, where 0.289 belongs. That is the aim work's claim (section 14 of the aim document) restated in the game's units: the smallest movement Nimbus can make turns this game's camera at about 2.5 degrees per second. (The "125 at full drag" this run reported was the folded figure; run 3 below has the real one.) The throwaway profile was removed and `controller_config.json` restored at the end.

**Run 3, 17/17**, after the yaw unwrapping, the surveyed reset pose, and the Spectator+ primitives. The N-series repeated (a 0.95 drag now reads 406 degrees in the step, the 1 px drag 2.4, the left stick 200 units on the clear run, the button 62 ms), and then the primitives ran through `ControllerBridge.get_spectator()` with the calibration from run 5, each measured by the console:

| Primitive | Plan | Result |
|---|---|---|
| turn right 90 | `rx` +1.00 for 0.403 s | -86.4 degrees (tolerance 14) |
| turn left 45 | `rx` -0.60 for 1.370 s | +45.7 degrees (tolerance 7) |
| turn right 10 | `rx` +0.40 for 0.741 s | -9.9 degrees (tolerance 5) |
| walk 100 units | `y` +1.00 for 0.425 s | 105.6 units (tolerance 20) |
| stop a 400-unit walk after 0.3 s | | 72.7 units before the stop, 0.0 in the next second, stick at zero |

The planner's choices are what section 4.7 intends: small angles go to the slow stick and long holds, the 90 goes to the stop where timing matters most, and that is where the error is largest (4 degrees short on a 0.4 s hold, about 10 ms of ramp). A closed loop would fix it; for v0 the tolerance is the honest number.

### 2026-09-07, dev machine, Elden Ring 1.17, full screen 2560x1440, pad actuator, frame-differencing oracle

The second recipe, for a game with no console: verdicts, not numbers. Three runs. **Run 1** (4/5) never left the title screen: a notice that the last session was not quit from the menu ("Quit Game or Return to Desktop might not have been selected") sits in front of it with an OK button, and it will always be there, because the harness kills the game at the end of a run; the fixed sequence's presses came before it appeared and the control step saw zero changed samples. **Run 2** (4/5) reached the main menu and stopped there with Continue highlighted: the third press came before the menu was up, and the menu's gold shimmer (200 of 102,480 samples) passed the old fixed threshold of 150 for "the stick moved the picture". **Run 3, 11/11**, with a 30 s wait for the logos and one `press_until_control` step (test the stick, press A after a failed test, every 5 s, "moved" a twentieth of the frame) reached the world 69 s after launch, 19,726 samples moving under the stick. Against a noise floor of 330 in the world:

| Step | changed samples | verdict |
|---|---|---|
| control `rx` 1.00 | 31,787 | MOVED |
| 0.20 | 1,057 | MOVED (marginal: the threshold was 990) |
| 0.26 | 3,053 | MOVED |
| 0.28 | 5,205 | MOVED |
| 0.30 | 6,762 | MOVED |
| 0.40 | 11,880 | MOVED |
| 0.60 | 37,223 | MOVED |
| 0.80 | 44,191 | MOVED |
| 1.00 | 15,947 | MOVED |
| left 0.60 | 13,772 | MOVED |
| pitch up 0.60 | 8,619 | MOVED |
| walk 1.00 | 7,707 | MOVED |
| idle after | 2,131 | (open ground, more grass in the wind) |

What the game taught: its camera deadzone is at or below 0.20 by this measure (0.20 is marginal, 0.26 is not), lower than Left 4 Dead 2's 0.28, which is worth knowing for the anti-deadzone default; the full-deflection step changed fewer samples than 0.80 because the camera came most of the way round in the second and the frame was compared with something like itself, which is the frame oracle's blind spot and exactly the fold the console oracle had to be taught to unwrap; and with no console there is no reset, no calibration and no primitives for this game until another oracle exists (section 2.1). The unclean-exit notice is the harness's own doing; quitting through the menu would need a scripted path through the System menu, which is a later refinement.

---

## Related Documents

- [Aim Assistance](AIM_ASSISTANCE.md): sections 12.3 and 14, the frame-differencing measurement this harness replaces and the numbers it has to reproduce.
- [Windows Mouse Filter Plan](WINDOWS_MOUSE_FILTER_PLAN.md): section 5, the probe style and the results-log convention.
- [Host Mode & Input Isolation](HOST_MODE_ISOLATION.md): section 8, the measurements on what Left 4 Dead 2 and Elden Ring read.
- [Research Platform](RESEARCH_PLATFORM.md): Spectator+ effectiveness as a research question.
