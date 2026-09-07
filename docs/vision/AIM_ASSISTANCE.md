# Aim Assistance: Why Aiming Is Hard and What To Do About It

**Status:** Research plus a code audit of the live pipeline (section 2, 2026-09-06). Tier 1 (section 4) and steps 1 to 7 of section 11 are implemented as of 2026-09-06 on `feature/aim-assistance-pipeline`; section 14 records what was built and where it departs from the proposal. Section 6 is still proposed work; sections 7 to 9 are options that need no code.
**Question:** Users report that aiming through Nimbus is hard. How much of that is our pipeline, how much is the mouse-to-stick paradigm, and what assistance can we legitimately provide?

---

## 1. Summary

Four things stack against the user, and three of them are ours:

| Cause | Owner | Fix effort |
|---|---|---|
| A 200 px stick widget gives only 81 px of mouse travel for full deflection | Nimbus | Low |
| No output anti-deadzone, so the game's own 24 to 26.5% inner deadzone eats the first quarter of our range | Nimbus | Low |
| The sensitivity curve is applied twice, once in QML and once in the bridge | Nimbus | Low |
| Deadzone and curve are per-axis on a circular control, so the dead region is a cross and diagonals are distorted | Nimbus | Low |
| A mouse is a position-control device and a stick is a rate-control device | Physics | Not fixable, only narrowable |

The first four are a day of work between them and they compound: fixing the anti-deadzone is also what makes the game's *own* aim assist start working for our users (section 7).

---

## 2. The measured problem

### 2.1 The stick has 81 pixels of travel

`qml/components/DraggableWidget.qml` lines 294 to 297:

```qml
readonly property real joyRadius: Math.max(1, Math.min(width, height) / 2 - borderWidth / 2)
readonly property real thumbRadius: Math.min(width, height) * 0.18 * 0.5
readonly property real effectiveRadius: Math.max(1, joyRadius - thumbRadius)
```

For the 200 px sticks in `profiles/adaptive_platform_2.json`: `joyRadius` is 99, `thumbRadius` is 18, `effectiveRadius` is **81 px**. The drag handler at line 615 converts pixel delta straight to normalized deflection by dividing by that radius.

So 81 px of mouse movement covers zero to full turn rate. One pixel is 1.2% of deflection. We are asking for sub-pixel precision from a hand that, for many of our users, does not have sub-pixel precision.

The tuning knob for this is control-display gain, and the direction is counter-intuitive: **more travel is more precision**, bounded only by desk space and screen area. Lock mode currently runs the wrong way. `qml/layouts/CustomLayout.qml` line 306 computes `scale = lockSensitivity * 2`, which at the default of 4 is an 8x gain, meaning full deflection in roughly 12 px.

### 2.2 The game discards the first quarter of our range

`controller.prefer_vigem` is `true` by default, so output is XInput. The standard constants are:

| Constant | Raw | Fraction of range |
|---|---|---|
| `XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE` | 7849 | 24.0% |
| `XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE` | 8689 | 26.5% |
| `XINPUT_GAMEPAD_TRIGGER_THRESHOLD` | 30 | 11.7% |

Nimbus has no anti-deadzone anywhere in the pipeline. Games that use the documented values (most of them) therefore see nothing at all until our output magnitude passes 0.265 on the right stick, and then the crosshair starts at a quarter-speed turn rather than easing in from zero. That discontinuity at the center is the on-off feel users describe as "twitchy" or "it does nothing then it does too much."

### 2.3 The curve is applied twice

`qml/components/DraggableWidget.qml` lines 459 to 460 apply `_applyCurve` per axis, then `src/bridge.py` lines 525 to 526 (`setLeftStick`) and 544 to 545 (`setRightStick`) call `ControllerConfig.apply_sensitivity_curve`, which takes the `apply_joystick_dialog_curve` branch because `joystick_settings.sensitivity` is set in every generated config.

With current defaults (widget: deadzone 0, extremity 5, sensitivity 50; global: deadzone 10, extremity 5, sensitivity 50) the chain is:

```
n  ->  QML:    0.95 * n
   ->  bridge: ((0.95n - 0.025) / 0.975) * 0.95
```

Maximum output is **0.901**, not 1.0. The user can never reach full turn rate. Two extremity caps and two deadzones are stacking.

It gets much worse the moment either sensitivity slider is touched, because the two power curves multiply. A widget at 20% (power 2.8) through a global setting at 20% (power 2.8) is an effective power of **7.84**, at which point 50% stick travel produces 0.4% output. This is almost certainly what a user hits when they try to make aiming easier by lowering sensitivity and find it becomes dramatically worse.

This also violates the rule in `CLAUDE.md`: curves, deadzones and smoothing belong in the bridge, never in QML.

### 2.4 Combined effect

Taking 2.1 through 2.3 together for the right stick against a standard 26.5% game deadzone:

| Mouse travel from center | What the game sees |
|---|---|
| 0 to 2 px | Nothing (our own stacked deadzone) |
| 2 to 25 px | Nothing (inside the game's inner deadzone) |
| 25 px | Turn starts, abruptly, at 26.5% rate |
| 81 px | Maximum, capped at 90% of full rate |

**The entire usable aiming range is 56 px of mouse travel**, entered through a 25 px dead region and never reaching full deflection. That is the headline finding.

### 2.5 Two smaller defects found in the same audit

**Per-axis shaping on a circular control.** Both `_applyCurve` in QML and `apply_sensitivity_curve` in the bridge operate on x and y independently, while the drag handler clamps magnitude to the unit circle. The result is a cross-shaped dead region rather than a circular one, and diagonal response that does not match cardinal response. Microsoft's own XInput guidance recommends a radial (magnitude-based) deadzone for exactly this reason.

A related consequence: with a convex curve (sensitivity above 50, power below 1) a clamped diagonal of 0.707 per axis becomes 0.841 per axis, a magnitude of 1.19. Both backends clamp per axis to [-1, 1] (`src/vigem_interface.py` lines 130 and 162; `src/vjoy_interface.py` `update_axis`), so nothing overflows, but the effective gate becomes square: diagonals are faster than cardinals, and the thumb position on screen stops matching the output.

**No smoothing on the path we actually use.** `src/bridge.py` line 615 returns early from `_smoothing_tick` when ViGEm is active, and the per-widget `tremorFilter` EMA is only wired into the lock-mode handler at `qml/layouts/CustomLayout.qml` line 312. A normal drag on the default ViGEm path gets no filtering at all. For a user with tremor this is the difference between playable and not.

---

## 3. The part that is not our fault

A mouse is a **position control** device: displacement of the device maps to displacement of the controlled object. A stick is a **rate control** device: displacement maps to velocity, and the object keeps moving while the stick is held. The HCI literature is consistent that position control outperforms rate control for pointing tasks, and Nimbus's whole premise converts the better paradigm into the worse one.

That is the price of the architecture and it buys compatibility with every game that accepts a gamepad. It cannot be removed, but the gap can be narrowed from both ends:

- Make the rate-control mapping as good as it can be (sections 4 to 6).
- Let the game's own assistance do the last few degrees (section 7).
- Where a game supports it, offer a genuine position-control mode (section 6.4).

---

## 4. Tier 1: fix the pipeline

Highest value per hour of work, no new concepts, no ethical questions.

### 4.1 Single shaping function, radial, in the bridge

Replace per-axis shaping with one function that takes the whole vector. Proposed for `src/config.py`:

```python
def shape_stick(self, x: float, y: float, joystick: str) -> Tuple[float, float]:
    """
    Shape a raw stick vector into driver output.

    Applies, in order: unit-circle clamp, radial deadzone, response curve,
    output anti-deadzone, and the extremity cap. Radial rather than per-axis
    so the dead region is a circle and diagonals match cardinals.

    Parameters
    ----------
    x, y : float
        Raw normalized deflection from the widget, before any shaping.
    joystick : str
        "left" or "right"; selects the per-stick settings block.

    Returns
    -------
    Tuple[float, float]
        Shaped output in [-1, 1] per axis, magnitude never exceeding 1.
    """
```

The QML side then sends raw values and stops calling `_applyCurve`. Delete the second application in `setLeftStick` / `setRightStick` and route both through `shape_stick`.

This alone restores the missing 10% of range and removes the curve-multiplication trap.

### 4.2 Output anti-deadzone

After the curve, remap non-zero output from `[0, 1]` onto `[anti_deadzone + buffer, 1]` so the smallest real movement produces the smallest movement the game will accept. Steam Input ships exactly this pair of controls, "Output Anti-Deadzone" and "Anti-Deadzone Buffer", and the buffer exists so the user can re-introduce a small dead region of their own choosing once the anti-deadzone is calibrated.

Proposed defaults, since we know the backend:

| Output mode | Stick | Anti-deadzone default |
|---|---|---|
| ViGEm (XInput) | Left | 0.24 |
| ViGEm (XInput) | Right | 0.265 |
| vJoy (DirectInput) | Any | 0.0 (games vary; user calibrates) |

These are defaults, not constants. Games override the XInput values freely, so the setting must be adjustable per profile, and the settings dialog needs a **live readout of the post-shaping output value** so the user can raise the anti-deadzone until the smallest movement produces visible motion. Calibrating this blind is miserable.

### 4.3 Decouple travel from widget size

Add a `travel_px` property to axis widgets: the number of mouse pixels required for full deflection, independent of how large the widget is drawn. A 200 px stick should be able to demand 400 px of travel. Default it to the current `effectiveRadius` so existing profiles do not change behavior.

While there, reconsider lock mode: `lockSensitivity * 2` should probably become a divisor or be re-expressed in the same `travel_px` units so that one concept covers both paths.

### 4.4 Precision modifier

A button that, while held or latched, multiplies gain by a configurable factor (0.25 is a reasonable default) and optionally steepens the curve. This is the standard sniper-toggle pattern and it is the cheapest large win after anti-deadzone, because it lets a single profile serve both "swing the camera around" and "hold on a target."

### 4.5 Tremor filter on the drag path

The EMA already exists at `qml/layouts/CustomLayout.qml` lines 312 to 320. Move it into the bridge (per the `CLAUDE.md` rule) and apply it on every axis path, not just lock mode. Note that filtering costs latency, so it must stay off by default and be exposed per widget.

### 4.6 Response curve default

The sensitivity slider already produces powers from 0.1 to 4.0. For aiming specifically, a wide curve that gives more travel to the low end is the right default, and 50% (linear) is the current one. Worth changing the default for `joystick` widgets specifically, or shipping an "Aiming" preset.

---

## 5. Proposed settings surface

New keys under a profile's config. **This is a schema change and touches the three-way contract** (profile JSON, `CustomLayout.qml` plus `DraggableWidget.qml`, and the bridge mapping), so it needs sign-off before implementation per `CLAUDE.md`.

```jsonc
// controller_config.json / profile, per stick
"aim": {
  "anti_deadzone": 0.265,      // 0..1, fraction of output range to skip
  "anti_deadzone_buffer": 0.02, // 0..1, user-chosen dead region after remap
  "radial": true,               // radial shaping instead of per-axis
  "precision_gain": 0.25,       // gain while the precision modifier is active
  "settle_ms": 0                // dwell-to-settle, 0 = off (section 6.1)
}
```

```jsonc
// custom_layout.widgets[] additions for type "joystick"
"travel_px": 240,        // mouse pixels for full deflection
"anti_deadzone": 0.265,  // per-widget override of the profile value
"tremor_filter": 0.0     // already in the schema, extend to the drag path
```

---

## 6. Tier 2: assistance that is not target-aware

These help without the software knowing anything about what is on screen, which keeps them defensible everywhere (see section 10).

### 6.1 Dwell-to-settle

When the pointer stops moving for N milliseconds, ease output toward zero. Stops the slow drift that happens when a user cannot return the stick exactly to center, which is the most common complaint pattern for head and mouth control.

### 6.2 Axis lock

A modifier that zeroes one axis while held, so horizontal tracking cannot drift vertically. Very effective for tremor, and trivially implemented in the bridge.

### 6.3 Reversal rate limit

Cap how fast output may swing through the center. Kills the overshoot oscillation that happens when a user corrects an overshoot with another overshoot.

### 6.4 Absolute (position) aim mode

For games that tolerate it, drive the stick from the cursor's distance from a fixed screen anchor rather than from drag delta. This keeps the mouse in its native position-control paradigm and is close to what Steam Input calls Mouse Region. It will not work everywhere, but where it works it is a step change rather than an improvement.

This one interacts with the mouse isolation work in `WINDOWS_MOUSE_FILTER_PLAN.md`, since it needs the physical cursor position and needs the game not to see it.

---

## 7. Tier 3: the game's own aim assist, which we already qualify for

Because ViGEm presents a real XInput device, games apply the **controller aim assist path** to Nimbus users with no code on our side. That is two distinct mechanics:

- **Slowdown / friction**: the reticle slows as it crosses a target.
- **Rotational aim assist**: the camera tracks a moving target.

The detail that matters for us: **rotational aim assist only activates while the game registers stick input above its deadzone.** Standing still yields slowdown only. So section 4.2 is not merely a feel fix, it is the precondition for the strongest assistance already available to our users. Today the first 25 px of travel produce input the game does not count as input at all.

**The structural limit.** Rotational assist is strongest when the left stick is also moving, and a single pointer cannot drive both sticks at once. Legitimate mitigations are a latched strafe button or a toggle-hold movement widget, where the user chooses the direction and the software only holds it. Automatically injecting left-stick motion to farm rotational assist is not on the table; see section 10.

## 8. Tier 4: per-game settings, which cost nothing

The best aim assist is usually already in the game and switched off by default. Candidates to document per title in `docs/GAME_COMPATIBILITY.md`, as a new column or a companion table:

| Setting | What it does |
|---|---|
| Aim assist strength | Direct multiplier, often 0 to 100 |
| Lock-on / auto-target | Snaps and holds on the nearest target |
| Aim assist slowdown | Reticle friction over targets |
| Zoom snap | Small snap toward a target on ADS |
| Hold vs toggle aim | Removes a sustained hold from the user |
| Analog vs digital aim | Digital removes the fine-control requirement entirely |

The Last of Us Part I is the reference implementation with more than 60 accessibility options including aim assist strength, and is worth citing in user-facing docs as the standard to look for.

## 9. Tier 5: a different input device

For some users this is the honest answer, and it fits the position already stated in `docs/WHITEPAPER.md` that Nimbus wraps adaptive hardware rather than displacing it. The established pattern in the QuadStick community is **eye tracking for aiming, QuadStick for buttons**. Tobii Eye Tracker 5 does head and eye tracking with native support in 170+ titles.

Nimbus's role there is unchanged: it is the layer that turns whatever pointer the user has into gamepad output. A head tracker or eye tracker producing pointer events flows through the same pipeline, and every fix in section 4 benefits it.

---

## 10. The line we do not cross

Screen-capture target detection driving the stick is an aimbot regardless of intent, and so is injecting synthetic stick motion the user did not command in order to trigger the game's assistance.

As of 2026 both Activision and Respawn have stated publicly that genuine accessibility hardware is exempt and encouraged, and that XIM and Cronus are not accessibility tools despite being marketed as such. Respawn classified XIM adapters as cheating devices in March 2026 with permanent bans and no appeals; Activision's Ricochet update for Black Ops 7 Season 2 describes detection built to recognize *classes of machine-driven behavior* rather than specific device signatures. `HOST_MODE_ISOLATION.md` section 8 already reaches the same conclusion from the driver side: at the device layer Nimbus is not distinguishable from a XIM, so the distinction has to be behavioral.

The property that keeps Nimbus on the right side of that line is simple and worth stating explicitly in the README as a non-goal:

> **Nimbus reshapes input the user produces. It never originates aim.**

Everything in sections 4 through 6 satisfies that. Nothing in this document proposes reading the screen, detecting targets, or generating input the user did not command.

---

## 11. Order of work

1. Delete `_applyCurve` from the QML send path; send raw normalized values. (Fixes 2.3, restores 10% of range.)
2. Add `shape_stick` to `ControllerConfig` with radial deadzone and curve; route both stick slots through it. (Fixes 2.5.)
3. Add output anti-deadzone and buffer with per-backend defaults. (Fixes 2.2, unlocks section 7.)
4. Add `travel_px` to axis widgets. (Fixes 2.1.)
5. Add the precision modifier.
6. Move the tremor EMA into the bridge and apply it on all axis paths.
7. Add a live post-shaping output readout to the joystick settings dialog, so 3 can be calibrated.
8. Then reassess. Sections 6 and 8 come after, and section 6.4 should wait for the isolation work to settle.

Steps 1 and 2 are a behavior change for every existing profile. They need a note in `CHANGELOG.md` and probably a one-time migration that halves any non-default sensitivity value, since users who compensated for the double curve will suddenly find their settings twice as aggressive.

## 12. How to verify

There is no automated suite, so this is manual, in the style of the probes in `tests/`:

- A gamepad tester (web or `tests/test_vjoy.py` for the vJoy path) to confirm the shaped output curve matches the dialog preview and that magnitude never exceeds 1.
- A game with a visible sensitivity setting, to confirm the anti-deadzone value at which the smallest movement produces motion, and that it matches the documented XInput constant.
- Measure travel-to-full-deflection with a ruler on screen before and after step 4.
- Re-run `tests/probe_nimbus_relay_windows.py` after any bridge change, since it exercises the real stick path end to end through ViGEm.

## 13. Open questions

- Should anti-deadzone default to the XInput constants, or to zero with a first-run calibration prompt? Defaulting to 0.265 is right for most games and wrong and confusing for the ones that already compensate.
- Does the migration in section 11 need to be automatic, or is a changelog note plus a "reset to defaults" button enough?
- Is `travel_px` the right unit, or should it be expressed as a gain multiplier so it survives DPI changes? Mouse DPI and Windows pointer speed both affect the physical distance a pixel represents.
- Where does the precision modifier live in a layout that has no spare buttons? A dwell zone, a second pointer button, and a screen-edge region are all candidates.

## 14. Implementation notes (2026-09-06)

Steps 1 to 7 of section 11 are in (`src/config.py`, `src/bridge.py`, `qml/components/DraggableWidget.qml`, `qml/layouts/CustomLayout.qml`, `profiles/adaptive_platform_2.json`). What was built, and where it departs from sections 4 and 5:

- **One shaping function.** `shape_magnitude` and `shape_vector` in `src/config.py` do the whole chain on the vector's magnitude: inner deadzone, gain, power curve, then the remap onto `[floor, ceiling]`. The bridge resolves each custom-layout widget's settings from the profile by id and shapes in `setStickInput` / `setAxisInput`, so QML sends raw geometry and `_applyCurve` is gone. `shape_stick` covers the legacy layouts with the global `joystick_settings` block. The curve preview asks the bridge for its points.
- **Floor inside the ceiling.** Section 4.1 orders the anti-deadzone before the extremity cap. It is the other way round in code: the remap is onto `[anti_deadzone + buffer, 1 - extremity]`, because applying a 5% cap after the floor would push a calibrated 0.265 down to 0.252, back under the game's threshold. The buffer only counts on top of a non-zero anti-deadzone.
- **No profile-level `aim` block.** Section 5 proposed per-stick profile keys with per-widget overrides. Everything is per widget (`anti_deadzone`, `anti_deadzone_buffer`, `travel_px`, `precision_gain`, and the existing `tremor_filter`), since the widget dialog is the only place a custom-layout user edits shaping. `joystick_settings` gained optional `anti_deadzone`, `anti_deadzone_buffer` and `precision_gain` keys for the legacy layouts only. `radial` is not a setting: shaping is always radial. `settle_ms` waits for section 6.1.
- **The precision modifier is a button widget with `modifier: "precision"`**, so no new widget type; `toggle_mode` latches it. The gain is per joystick, so a movement stick can be left at 100%. A held stick is re-shaped the moment the modifier changes. Open question 4 (where it lives in a layout with no spare button) stays open.
- **Defaults.** Anti-deadzone defaults to the XInput constants under ViGEm and 0 under vJoy, resolving open question 1 in favour of the constants; a user whose game already compensates lowers the slider, and the dialog's test pad with "Drive the controller" on is the calibration loop of section 4.2. Sticks keep the 5% extremity cap; sliders and wheels default to none, which also fixes the RT trigger idling at 5% and topping out at 95% (it went through the widget curve and then the rudder curve). Hold and return-to-zero sliders are shaped as the unipolar controls they are. The bundled right stick ships with `travel_px` 160.
- **No migration**, resolving open question 2. With the global block at its defaults the second pass was near linear, so no sensitivity doubles; the visible change is the top 5% of range returning and the global 2.5% deadzone going. A changelog note covers it. The Axis Configuration dialog that edits the global block is hidden for custom layouts anyway.
- **Lock mode is unchanged** apart from its EMA moving into the bridge. `lockSensitivity * 2` still stands; the second paragraph of section 4.3 is open.
- **A release always centres.** The tremor EMA in the bridge treats an exact (0, 0) as a release and drops its state, so a heavily filtered stick can never be left holding a residual deflection after the pointer lets go. This matters more now than in lock mode, where nothing ever released.
- **Verified** with property checks on the shaping function (radial symmetry across the sensitivity range, magnitude never above 1 including convex curves and overflowing input, floor and ceiling, gain), a headless bridge run against the dev machine's profile, and `tests/probe_nimbus_relay_windows.py` 8/8 (the 80 px drag lands at LX +0.95, the single cap; release recentres). The ruler measurement in section 12 and the in-game floor check against a title with a visible sensitivity setting are still to do.

---

## Related Documents

- [Game Compatibility](../GAME_COMPATIBILITY.md): where per-title aim assist settings should be documented (section 8)
- [Host Mode & Input Isolation](HOST_MODE_ISOLATION.md): section 8 on the XIM resemblance, which section 10 depends on
- [Windows Mouse Filter Plan](WINDOWS_MOUSE_FILTER_PLAN.md): the cursor relay that absolute aim mode (6.4) would need
- [Hardware Integration](HARDWARE_INTEGRATION.md): the input pipeline this all sits in, and the eye/head tracking path in section 9
- [Whitepaper](../WHITEPAPER.md): the "wrap, don't displace" position that section 9 follows from

## Sources

- [Getting Started with XInput, Microsoft](https://github.com/MicrosoftDocs/win32/blob/docs/desktop-src/xinput/getting-started-with-xinput.md): deadzone constants and the radial deadzone recommendation
- [Steam Input Wiki: Joystick Mouse](https://steaminput.wiki/en/input-styles/joystick-mouse) and [Steam Input Essentials: Joystick Move](https://bryanrumsey.wordpress.com/2019/05/29/steam-input-essentials-eps-8-joystick-move/): anti-deadzone, anti-deadzone buffer, and response curve terminology
- [Stick Drift, Deadzones, and Aim Assist](https://gamepadtest.app/guides/aim-assist-stick-drift) and [What Is Aim Assist, GPADLAB](https://gpadlab.com/learn/glossary/aim-assist): slowdown vs rotational assist, and the stick-input requirement
- [RubberEdge: Reducing Clutching by Combining Position and Rate Control](https://arxiv.org/pdf/0804.0556): position vs rate control, and control-display gain
- [RICOCHET Anti-Cheat Season 02 Update](https://www.callofduty.com/blog/2026/02/call-of-duty-black-ops-7-ricochet-anti-cheat-season-02) and [Apex Legends XIM & Cronus ban wave 2026](https://www.versaciboosts.com/blog/apex-legends-xim-cronus-titan-two-ban-2026-safe-boosting): the accessibility exemption and the machine-driven-behavior detection class
- [Helping Hand challenge pattern, Accessible Games](https://accessible.games/accessible-player-experiences/challenge-patterns/helping-hand/): the vocabulary used in section 8
- [Tobii Eye Tracker 5](https://gaming.tobii.com/product/eye-tracker-5/) and [QuadStick community discussion](https://groups.google.com/g/quadstick/c/rrgQD5uB1RI): the eye-tracking-plus-switch-input pattern
