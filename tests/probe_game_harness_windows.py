"""
Game harness runner (throwaway, not Nimbus code).

Launches a real game from a recipe in ``tests/games/``, owns the pad it
reads, and measures what stick and button input do to it, in the game's own
units where the recipe has a console oracle. ``docs/vision/GAME_TEST_HARNESS.md``
is the plan and the results log; ``tests/game_harness.py`` is the machinery.

Actuators
---------
pad (default)
    A ViGEm pad of the harness's own. Calibrates the game:

    G0  launch: the game window appears within the recipe's timeout
    G1  ready: the oracle answers (a pose is read from the console log)
    G2  reset: the player is put back within 2 units and 1 degree
    G3  idle: one second of nothing leaves the pose alone; frame noise floor
    G4  yaw control: right stick full right turns more than 10 degrees, the recipe's way
    G5  yaw sweep: degrees per second at each magnitude; the game's deadzone;
        the frame-difference verdict beside the ground truth for each step
    G6  yaw left: opposite sign, rate within 25 percent of the right turn
    G7  pitch: right stick up changes the pitch by more than 1 degree
    G8  move: left stick up for a second moves the player more than 20 units
    G9  button: the pad button bound to an echo marker lands in the console log
    G10 release: nothing is stuck afterwards
    G11 latency: the first pose sample whose yaw moved after the stick went on
    G12 calibration: yaw against hold time at several magnitudes, and walk
        against hold time; ``--write-calibration`` writes the table into
        ``src/spectator/calibrations/<game>.json`` for the primitives
nimbus
    The real Nimbus app in-process, driving the same environment through its
    widgets, on a throwaway copy of the bundled profile (``--profile <id>``
    runs an existing one instead); what the bridge sent is recorded beside
    what the game did, and the expected values come from the bridge's own
    resolved parameters, never from a number in the docs:

    N0  app: window, ViGEm mode, an rx/ry stick found, game launched second and ready
    N1  full drag: turns more than 10 degrees, the bridge sent its ceiling (0.95 bundled)
    N2  one-pixel drag: turns more than 1 degree (the anti-deadzone floor, in degrees)
    N3  release: the bridge reads zero and the pose is stable
    N4  button: a click on the bumper widget produces the echo marker
    N5  left stick: a full drag up moves the player more than 20 units, ceiling sent

    then the Spectator+ v0 primitives through the bridge's runner, planned
    from the calibration G12 wrote and measured by the game:

    P0  the bridge's runner loads this game's calibration
    P1  turn right 90 degrees, P2 turn left 45, P3 turn right 10: within
        15 percent or 5 degrees
    P4  walk 100 units: within 20 percent or 10 units
    P5  stop: a long walk cut short releases the stick and the player stops

Run (from the repo root, venv with PySide6 and vgamepad; ViGEmBus installed;
Steam able to sign in without a prompt)::

    venv\\Scripts\\python tests\\probe_game_harness_windows.py --game left4dead2 --actuator pad
    venv\\Scripts\\python tests\\probe_game_harness_windows.py --game left4dead2 --actuator nimbus

Run them one at a time: each session's pad has to be player one, and the
runner quits the game at the end unless ``--keep-game`` is given. A recipe
whose ``reset_pose`` is null takes the first pose read as the session's reset
pose and prints it; ``--write-reset-pose`` writes it into the recipe.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

if sys.platform != "win32":
    sys.exit("Windows only")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

from game_harness import (  # noqa: E402
    FRAMES_DIR, GameEnv, NimbusActuator, PadActuator, load_recipe, on_qt, pose_delta, pose_error, wrap_deg,
    write_reset_pose,
)

DEFAULT_SWEEP = "0.20,0.26,0.28,0.30,0.40,0.60,0.80,1.00"
DEFAULT_CAL_MAGS = "0.40,0.60,1.00"
DEFAULT_CAL_HOLDS = "0.10,0.25,0.50,1.00"
DEFAULT_WALK_HOLDS = "0.25,0.50,1.00"
RESULTS: List[Dict[str, Any]] = []


def record(name: str, ok: bool, note: str = "") -> None:
    RESULTS.append({"check": name, "ok": bool(ok), "note": note})
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({note})" if note else ""), flush=True)


def fmt_pose(p: Optional[Dict[str, Any]]) -> str:
    if not p:
        return "no pose"
    x, y, z = p["pos"]
    pitch, yaw, roll = p["ang"]
    return f"pos=({x:.1f}, {y:.1f}, {z:.1f}) ang=({pitch:.1f}, {yaw:.1f}, {roll:.1f})"


def sgn(v: float) -> int:
    return (v > 0) - (v < 0)


# ---- shared checks -------------------------------------------------------------
def launch_and_ready(env: GameEnv, launch_name: str, ready_name: str) -> bool:
    ok = env.launch()
    record(launch_name, ok, f"window after {env.window_at - env.launched_at:.0f}s" if ok else
           f"no window titled {env.recipe['title']!r} owned by {env.recipe.get('process')} "
           f"within {env.recipe.get('window_timeout_s')}s")
    if not ok:
        return False
    env.run_sequence()
    ready = env.wait_ready()
    p = env.pose() if ready else None
    console = env.oracle.kind == "source_console"
    log_ok = (not console) or env.oracle.log.exists()
    record(ready_name, ready and log_ok and (not console or p is not None),
           (f"ready after {env.ready_at - env.launched_at:.0f}s; " if ready else "not ready in time; ")
           + (f"console log {'present' if log_ok else 'missing'}; " if console else "")
           + fmt_pose(p))
    return ready and log_ok


def establish_reset_pose(env: GameEnv, args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    p = env.pose()
    if env.oracle.reset_pose is None and p is not None:
        env.set_reset_pose(p)
        print(f"[harness] no reset_pose in the recipe; using the first pose read: {fmt_pose(p)}", flush=True)
        print(f'[harness] recipe line: "reset_pose": {{"pos": {[round(v, 3) for v in p["pos"]]}, '
              f'"ang": {[round(v, 3) for v in p["ang"]]}}}', flush=True)
        if args.write_reset_pose:
            write_reset_pose(env.recipe, p)
            print(f"[harness] wrote reset_pose into {env.recipe['_path']}", flush=True)
    return p


def check_reset(env: GameEnv, name: str) -> None:
    ok = env.reset()
    q = env.pose()
    rp = env.oracle.reset_pose
    dist, dang = pose_error(rp, q) if (q and rp) else (math.inf, math.inf)
    record(f"{name} reset puts the player back within 2 units and 1 degree",
           ok and dist < 2.0 and dang < 1.0, f"dist={dist:.2f} dang={dang:.2f} {fmt_pose(q)}")


def check_idle(env: GameEnv, name: str, label: str, set_noise: bool) -> None:
    r = env.step({}, 1.0, label)
    if set_noise:
        env.noise = int(r.get("changed") or 0)
    if r.get("pose_before") and r.get("pose_after"):
        stable = abs(r["d_yaw"]) < 0.5 and r["d_horiz"] < 1.0
        note = f"d_yaw={r['d_yaw']:+.2f} d_horiz={r['d_horiz']:.2f} changed={r['changed']}"
    else:
        stable = env.oracle.kind != "source_console"
        note = f"changed={r['changed']} (no pose)"
    record(f"{name} idle: one second of nothing leaves the pose alone", stable, note)


def yaw_note(r: Dict[str, Any], env: GameEnv) -> str:
    if "d_yaw" not in r:
        return f"changed={r['changed']} {env.verdict(r['changed'])} (no pose)"
    return (f"d_yaw={r['d_yaw']:+.2f} deg in {r['hold']:.2f}s = {r['d_yaw'] / r['hold']:+.1f} deg/s; "
            f"changed={r['changed']} {env.verdict(r['changed'])}")


# ---- pad -----------------------------------------------------------------------
def pad_checks(env: GameEnv, args: argparse.Namespace) -> None:
    recipe = env.recipe
    sign = int(recipe.get("turn_right_sign", -1))
    hold = float(args.hold)
    mags = [float(m) for m in args.sweep.split(",") if m.strip()]
    console = env.oracle.kind == "source_console"

    establish_reset_pose(env, args)
    if console:
        check_reset(env, "G2")
    else:
        record("G2 reset", True, "frame_diff oracle: no reset available, skipped")

    # GS walk survey: turn the reset pose to face the longest clear run, so
    # the walk checks and the walk calibration are not capped by a wall
    if console and args.survey_walk and env.oracle.reset_pose:
        base = env.oracle.reset_pose
        rows = []
        for yaw in range(0, 360, 45):
            env.set_reset_pose({"pos": list(base["pos"]), "ang": [0.0, wrap_deg(float(yaw)), 0.0]})
            env.reset()
            r = env.step({"ly": 1.0}, 1.0, f"survey_{yaw}", with_frame=False)
            rows.append((yaw, float(r.get("d_horiz", 0.0))))
            print(f"    yaw {yaw:>3}: {rows[-1][1]:6.1f} units in 1.0s", flush=True)
        best = max(rows, key=lambda t: t[1])
        chosen = {"pos": [round(v, 3) for v in base["pos"]], "ang": [0.0, wrap_deg(float(best[0])), 0.0]}
        env.set_reset_pose(chosen)
        env.reset()
        record("GS walk survey: the reset pose faces the longest clear run", best[1] > 150.0,
               f"best yaw {best[0]} at {best[1]:.1f} units; " + ", ".join(f"{y}:{d:.0f}" for y, d in rows))
        if args.write_reset_pose:
            write_reset_pose(env.recipe, chosen)
            print(f"[harness] wrote the surveyed reset_pose into {env.recipe['_path']}", flush=True)
    check_idle(env, "G3", "idle", set_noise=True)
    print(f"[harness] frame noise floor {env.noise}; moved if > {env.thresholds()[0]}, still if <= {env.thresholds()[1]}",
          flush=True)

    # G4 control
    r = env.step({"rx": 1.0}, hold, "rx_1.00")
    if console and "d_yaw" in r:
        ok = abs(r["d_yaw"]) > 10.0 and sgn(r["d_yaw"]) == sign
    else:
        ok = env.verdict(r["changed"]) == "MOVED"
    record("G4 yaw control: right stick full right turns more than 10 degrees, the recipe's way", ok, yaw_note(r, env))
    env.reset()
    if not ok:
        print("[harness] the game is not reading the right stick; the sweep would measure nothing", flush=True)
        return

    # G5 sweep
    rows = []
    for m in mags:
        r = env.step({"rx": m}, hold, f"rx_{m:.2f}")
        env.reset()
        dyaw = r.get("d_yaw")
        rows.append({"magnitude": m, "d_yaw": dyaw, "rate": (dyaw / hold) if dyaw is not None else None,
                     "changed": r["changed"], "verdict": env.verdict(r["changed"])})
        print(f"    rx={m:.2f}  " + (f"d_yaw={dyaw:+8.2f}  {dyaw / hold:+7.1f} deg/s  " if dyaw is not None else "")
              + f"changed={r['changed']:>6}  {rows[-1]['verdict']}", flush=True)
    moved = [row for row in rows if row["d_yaw"] is not None and abs(row["d_yaw"]) > 1.0]
    first = min((row["magnitude"] for row in moved), default=None)
    still = [row["magnitude"] for row in rows if row["d_yaw"] is not None and abs(row["d_yaw"]) <= 1.0
             and (first is None or row["magnitude"] < first)]
    disagreements = [row["magnitude"] for row in rows if row["d_yaw"] is not None
                     and ((row["verdict"] == "MOVED") != (abs(row["d_yaw"]) > 1.0))]
    env.sweep_rows = rows
    if console:
        record("G5 yaw sweep: the game's right-stick deadzone",
               first is not None,
               (f"first moved at {first:.2f}" if first is not None else "never moved")
               + (f", still at {max(still):.2f}" if still else "")
               + f"; frame verdict disagreed with the pose at {disagreements or 'no magnitude'}")
    else:
        moved_v = [row["magnitude"] for row in rows if row["verdict"] == "MOVED"]
        record("G5 yaw sweep (frame verdicts only)", bool(moved_v),
               f"first MOVED at {min(moved_v):.2f}" if moved_v else "never MOVED")

    # G6 left
    right = next((row for row in rows if abs(row["magnitude"] - 0.6) < 1e-6), None)
    if right is None or right["d_yaw"] is None:
        r_right = env.step({"rx": 0.6}, hold, "rx_0.60")
        env.reset()
        right = {"magnitude": 0.6, "d_yaw": r_right.get("d_yaw"), "rate": (r_right.get("d_yaw") or 0) / hold}
    r = env.step({"rx": -0.6}, hold, "rx_-0.60")
    env.reset()
    if console and "d_yaw" in r and right["d_yaw"] is not None and right["d_yaw"] != 0:
        ratio = abs(r["d_yaw"]) / abs(right["d_yaw"])
        ok = sgn(r["d_yaw"]) == -sgn(right["d_yaw"]) and 0.75 <= ratio <= 1.25
        note = yaw_note(r, env) + f"; right turn at 0.60 was {right['d_yaw']:+.2f}, ratio {ratio:.2f}"
    else:
        ok = env.verdict(r["changed"]) == "MOVED"
        note = yaw_note(r, env)
    record("G6 yaw left: opposite sign, rate within 25 percent of the right turn", ok, note)

    # G7 pitch
    r = env.step({"ry": 0.6}, hold, "ry_0.60")
    env.reset()
    if console and "d_pitch" in r:
        ok = abs(r["d_pitch"]) > 1.0
        note = (f"d_pitch={r['d_pitch']:+.2f} deg ({'up' if r['d_pitch'] < 0 else 'down'} for stick up); "
                f"changed={r['changed']} {env.verdict(r['changed'])}")
    else:
        ok = env.verdict(r["changed"]) == "MOVED"
        note = f"changed={r['changed']} {env.verdict(r['changed'])}"
    record("G7 pitch: right stick up changes the pitch by more than 1 degree", ok, note)

    # G8 move
    r = env.step({"ly": 1.0}, 1.0, "ly_1.00")
    env.reset()
    if console and "d_horiz" in r:
        ok = r["d_horiz"] > 20.0
        note = (f"d_horiz={r['d_horiz']:.1f} units in 1.0s, d_z={r['d_z']:+.1f}; "
                f"changed={r['changed']} {env.verdict(r['changed'])}")
    else:
        ok = env.verdict(r["changed"]) == "MOVED"
        note = f"changed={r['changed']} {env.verdict(r['changed'])}"
    record("G8 move: left stick up for a second moves the player more than 20 units", ok, note)

    # G9 button
    echo = env.oracle.echo_buttons()
    if not echo:
        record("G9 button", not console, "no console oracle, skipped" if not console else "the recipe binds no echo button")
    for bid, marker in echo:
        env.front()
        off = env.log_offset()
        t0 = time.monotonic()
        env.actuator.apply({"buttons": [bid]})
        ok = env.oracle.wait_echo(marker, off, 2.0)
        dt = (time.monotonic() - t0) * 1000.0
        time.sleep(0.1)
        env.actuator.release()
        record(f"G9 button: pad button {bid} lands in the console log as {marker}", ok,
               f"{dt:.0f} ms" if ok else "no echo within 2 s")
    time.sleep(0.3)

    # G10 release
    check_idle(env, "G10", "idle_after", set_noise=False)

    # G11 latency
    if console:
        env.front()
        p0 = env.oracle.pose()
        samples = []
        first = None
        t0 = time.monotonic()
        env.actuator.apply({"rx": 1.0})
        while time.monotonic() - t0 < 1.5:
            p = env.oracle.pose(timeout=0.5, tries=1)
            t = time.monotonic() - t0
            d = wrap_deg(p["ang"][1] - p0["ang"][1]) if (p and p0) else None
            samples.append((round(t * 1000), None if d is None else round(d, 2)))
            if d is not None and abs(d) > 0.5:
                first = t
                break
        env.actuator.release()
        env.reset()
        record("G11 latency: the first pose sample whose yaw moved after the stick went on", first is not None,
               (f"{first * 1000:.0f} ms (a bound: one key press and a log read per sample); " if first else "")
               + f"samples (ms, deg)={samples}")

    # G12 calibration: yaw against hold time at several magnitudes, and walk
    # against hold time. This is the table a turn or walk primitive is planned
    # from (src/spectator/calibration.py), so the holds are short as well as
    # long: games ramp stick input, and one rate would not do.
    if console:
        cal_mags = [float(m) for m in args.cal_mags.split(",") if m.strip()]
        cal_holds = [float(h) for h in args.cal_holds.split(",") if h.strip()]
        walk_holds = [float(h) for h in args.walk_holds.split(",") if h.strip()]
        yaw_table: Dict[str, List[List[float]]] = {}
        monotone = True
        for m in cal_mags:
            rows: List[List[float]] = []
            for h in cal_holds:
                r = env.step({"rx": m}, h, f"cal_rx_{m:.2f}_{h:.2f}", with_frame=False)
                env.reset()
                rows.append([h, round(float(r.get("d_yaw", 0.0)), 3)])
            yaw_table[f"{m:.2f}"] = rows
            amounts = [abs(a) for _, a in rows]
            monotone = monotone and all(b >= a for a, b in zip(amounts, amounts[1:]))
            print(f"    rx={m:.2f}  " + "  ".join(f"{h:.2f}s: {a:+.1f}" for h, a in rows), flush=True)
        walk_rows: List[List[float]] = []
        for h in walk_holds:
            r = env.step({"ly": 1.0}, h, f"cal_ly_1.00_{h:.2f}", with_frame=False)
            env.reset()
            walk_rows.append([h, round(float(r.get("d_horiz", 0.0)), 2)])
        print("    ly=1.00  " + "  ".join(f"{h:.2f}s: {u:.1f}" for h, u in walk_rows), flush=True)
        walk_ok = bool(walk_rows) and walk_rows[-1][1] > 20.0 and all(
            b >= a for (_, a), (_, b) in zip(walk_rows, walk_rows[1:]))
        record("G12 calibration: yaw and walk grow with hold time at every magnitude", monotone and walk_ok,
               f"yaw at {list(yaw_table)} for holds {cal_holds}; walk {walk_rows}")
        env.calibration = {"game": recipe["name"], "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                           "turn_right_sign": sign, "yaw": yaw_table, "walk": {"1.00": walk_rows}}
        if args.write_calibration:
            from src.spectator.calibration import CALIBRATIONS_DIR
            os.makedirs(CALIBRATIONS_DIR, exist_ok=True)
            path = os.path.join(CALIBRATIONS_DIR, f"{recipe['name']}.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(env.calibration, fh, indent=4)
                fh.write("\n")
            print(f"[harness] wrote {path}", flush=True)


# ---- nimbus --------------------------------------------------------------------
def nimbus_checks(env: GameEnv, act: NimbusActuator, args: argparse.Namespace) -> None:
    recipe = env.recipe
    sign = int(recipe.get("turn_right_sign", -1))
    hold = float(args.hold)
    console = env.oracle.kind == "source_console"

    establish_reset_pose(env, args)
    if console:
        check_reset(env, "N0b")
    check_idle(env, "N0c", "nimbus_idle", set_noise=True)

    # N1 full drag. The expected value is the bridge's own ceiling for this
    # stick (0.95 on the bundled profile; a user's copy may differ), so the
    # check is that the game turned and that the bridge sent what it says it
    # would, not a number copied from the docs.
    exp_full = act.expected("right", 1.0)
    r = env.step({"rx": 1.0}, hold, "nimbus_rx_full")
    env.reset()
    sent = float((r.get("sent") or {}).get("right_x", 0.0))
    sent_ok = abs(sent - exp_full) <= 0.02
    if console and "d_yaw" in r:
        ok = abs(r["d_yaw"]) > 10.0 and sgn(r["d_yaw"]) == sign and sent_ok
    else:
        ok = env.verdict(r["changed"]) == "MOVED" and sent_ok
    record("N1 full drag turns more than 10 degrees and the bridge sent its ceiling", ok,
           f"sent RX={sent:+.3f} (bridge ceiling {exp_full:.3f}, travel {act.travel('right'):.0f} px); "
           + yaw_note(r, env))
    if not ok and not sent_ok:
        print("[harness] the bridge did not send its own ceiling: the drag missed the stick or hit another widget",
              flush=True)
    elif not ok:
        print("[harness] the game is not reading Nimbus's pad (is it player one?)", flush=True)

    # N2 one-pixel drag: the anti-deadzone floor, in degrees
    exp_nudge = act.expected("right", float(args.nudge) / act.travel("right"))
    r = env.step({"rx_px": float(args.nudge)}, hold, "nimbus_rx_1px")
    env.reset()
    sent = float((r.get("sent") or {}).get("right_x", 0.0))
    sent_ok = abs(sent - exp_nudge) <= 0.02
    if console and "d_yaw" in r:
        ok = abs(r["d_yaw"]) > 1.0 and sgn(r["d_yaw"]) == sign and sent_ok
    else:
        ok = env.verdict(r["changed"]) == "MOVED" and sent_ok
    record(f"N2 a {args.nudge:g} px drag turns the camera by more than 1 degree", ok,
           f"sent RX={sent:+.3f} (bridge floor {exp_nudge:.3f}); " + yaw_note(r, env))

    # N3 release
    sent_now = act.sent()
    zero = all(abs(float(sent_now.get(k, 0.0))) < 1e-6 for k in ("left_x", "left_y", "right_x", "right_y"))
    check_idle(env, "N3a", "nimbus_idle_after", set_noise=False)
    record("N3 release: the bridge reads zero on every stick", zero, f"sent={sent_now}")

    # N4 button
    echo = env.oracle.echo_buttons()
    if not echo:
        record("N4 button", not console, "no console oracle, skipped" if not console else "the recipe binds no echo button")
    for bid, marker in echo:
        if bid not in act.buttons:
            record(f"N4 button: the profile has no widget for button {bid}", False, f"widgets={act.buttons}")
            continue
        env.front()
        off = env.log_offset()
        t0 = time.monotonic()
        act.apply({"buttons": [bid]})
        ok = env.oracle.wait_echo(marker, off, 2.0)
        dt = (time.monotonic() - t0) * 1000.0
        time.sleep(0.1)
        act.release()
        record(f"N4 button: a click on the {act.buttons[bid]} widget produces {marker}", ok,
               f"{dt:.0f} ms" if ok else "no echo within 2 s")
    time.sleep(0.3)

    # N5 left stick
    if "left" not in act.sticks:
        record("N5 left stick", False, "the profile has no joystick mapped to x/y")
        return
    exp_left = act.expected("left", 1.0)
    r = env.step({"ly": 1.0}, 1.0, "nimbus_ly_full")
    env.reset()
    sent = (r.get("sent") or {})
    ly = float(sent.get("left_y", 0.0))
    sent_ok = abs(ly - exp_left) <= 0.02
    if console and "d_horiz" in r:
        ok = r["d_horiz"] > 20.0 and sent_ok
        note = (f"sent LX={float(sent.get('left_x', 0)):+.3f} LY={ly:+.3f} (bridge ceiling {exp_left:.3f}); "
                f"d_horiz={r['d_horiz']:.1f} units in 1.0s; changed={r['changed']} {env.verdict(r['changed'])}")
    else:
        ok = env.verdict(r["changed"]) == "MOVED" and sent_ok
        note = f"sent LY={ly:+.3f} (bridge ceiling {exp_left:.3f}); changed={r['changed']} {env.verdict(r['changed'])}"
    record("N5 left stick: a full drag up moves the player more than 20 units and the bridge sent its ceiling",
           ok, note)

    primitive_checks(env, act, args)


def primitive_checks(env: GameEnv, act: NimbusActuator, args: argparse.Namespace) -> None:
    """Spectator+ v0 primitives through the bridge's runner, measured by the game."""
    from src.spectator.calibration import CALIBRATIONS_DIR
    recipe = env.recipe
    sign = int(recipe.get("turn_right_sign", -1))
    if env.oracle.kind != "source_console":
        record("P0 primitives", True, "no console oracle to measure a turn with, skipped")
        return
    cal_path = os.path.join(CALIBRATIONS_DIR, f"{recipe['name']}.json")
    runner = on_qt(lambda: act.bridge.get_spectator())
    loaded = on_qt(lambda: runner.use_game(recipe["name"]))
    record("P0 the bridge's Spectator+ runner loads this game's calibration", loaded,
           cal_path + ("" if loaded else " is missing: run the pad actuator with --write-calibration first"))
    if not loaded:
        return

    cases = [
        ("P1 turn right 90", lambda: runner.turn(90.0), "d_yaw", sign * 90.0),
        ("P2 turn left 45", lambda: runner.turn(-45.0), "d_yaw", -sign * 45.0),
        ("P3 turn right 10", lambda: runner.turn(10.0), "d_yaw", sign * 10.0),
        ("P4 walk 100 units", lambda: runner.walk(100.0), "d_horiz", 100.0),
    ]
    for name, call, key, expected in cases:
        env.front()
        p0 = env.oracle.pose()
        plan = on_qt(call)
        if not plan:
            record(name, False, "the runner refused the plan (busy, or no calibration row)")
            continue
        deadline = time.monotonic() + float(plan["hold"]) + 3.0
        while on_qt(lambda: runner.busy) and time.monotonic() < deadline:
            time.sleep(0.03)
        done = not on_qt(lambda: runner.busy)
        time.sleep(0.4)
        p1 = env.oracle.pose()
        d = pose_delta(p0, p1)
        env.reset()
        got = d.get(key)
        tol = max(5.0, 0.15 * abs(expected)) if key == "d_yaw" else max(10.0, 0.2 * abs(expected))
        ok = done and got is not None and abs(got - expected) <= tol
        record(f"{name}: within {tol:.0f} of {expected:+.0f}", ok,
               (f"got {got:+.1f}" if got is not None else "no pose")
               + f" with axis {plan['axis_value']:+.2f} held {plan['hold']:.3f}s"
               + ("" if done else "; the runner never finished"))

    # P5 stop: a long walk cut short releases the stick and the player stops
    env.front()
    p0 = env.oracle.pose()
    plan = on_qt(lambda: runner.walk(400.0))
    time.sleep(0.3)
    on_qt(runner.stop)
    still_busy = on_qt(lambda: runner.busy)
    sent = act.sent()
    time.sleep(0.5)
    p1 = env.oracle.pose()
    before = pose_delta(p0, p1).get("d_horiz", 0.0)
    after = env.step({}, 1.0, "primitive_stop_idle", with_frame=False).get("d_horiz", 1e9)
    env.reset()
    ok = plan is not None and not still_busy and abs(float(sent.get("left_y", 0.0))) < 1e-6 and after < 1.0
    record("P5 stop: a walk cut short releases the stick and the player stops", ok,
           f"moved {before:.1f} units before the stop, {after:.1f} in the next second; sent LY={sent.get('left_y')}")


# ---- drivers -------------------------------------------------------------------
def summary(env: Optional[GameEnv]) -> int:
    failed = [r for r in RESULTS if not r["ok"]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed", flush=True)
    if env is not None:
        out = env.write({"checks": RESULTS, "sweep": getattr(env, "sweep_rows", None),
                         "calibration": getattr(env, "calibration", None)})
        print(f"wrote {out}", flush=True)
    return 1 if failed or not RESULTS else 0


def run_pad(args: argparse.Namespace, recipe: Dict[str, Any]) -> int:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841  (the screen grab needs one)
    try:
        act = PadActuator()       # before the game launches: Source looks for the pad at start-up
    except Exception as exc:      # noqa: BLE001
        print(f"no ViGEm pad: {exc}")
        return 2
    env = GameEnv(recipe, act, frames_dir=args.frames, skip_top=args.skip_top, save_frames=not args.no_frames)
    try:
        if launch_and_ready(env, "G0 launch: the game window appears", "G1 ready: the oracle answers"):
            pad_checks(env, args)
    except Exception as exc:      # noqa: BLE001
        traceback.print_exc()
        record("run crashed", False, f"{type(exc).__name__}: {exc}")
    finally:
        env.close(keep_game=args.keep_game)
        act.close()
    return summary(env)


def run_nimbus(args: argparse.Namespace, recipe: Dict[str, Any]) -> int:
    act = NimbusActuator(profile=args.profile)
    if not act.start():
        return 2
    holder: Dict[str, GameEnv] = {}

    def scenario() -> None:
        err = act.prepare()
        env = GameEnv(recipe, act, call=on_qt, frames_dir=args.frames, skip_top=args.skip_top,
                      save_frames=not args.no_frames)
        holder["env"] = env
        if err:
            record("N0 app", False, err)
            return
        try:
            if not launch_and_ready(env, "N0 launch: the game window appears (Nimbus's pad already exists)",
                                    "N0 ready: the oracle answers"):
                return
            act.place_beside(env)
            record("N0 app: window, ViGEm, the profile's sticks and buttons", True,
                   f"sticks={act.sticks} buttons={sorted(act.buttons)}")
            nimbus_checks(env, act, args)
        finally:
            env.close(keep_game=args.keep_game)

    act.run(scenario)
    return summary(holder.get("env"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", default="left4dead2", help="recipe name in tests/games/ or a path to a recipe")
    ap.add_argument("--actuator", choices=("pad", "nimbus"), default="pad")
    ap.add_argument("--hold", type=float, default=1.0, help="seconds to hold each stick step")
    ap.add_argument("--sweep", default=DEFAULT_SWEEP, help="right-stick magnitudes for the yaw sweep")
    ap.add_argument("--nudge", type=float, default=1.0, help="nimbus: pixels of drag for the floor check")
    ap.add_argument("--profile", default=None,
                    help="nimbus: an existing profile id to run instead of the throwaway copy of the bundled one")
    ap.add_argument("--keep-game", action="store_true", help="leave the game running at the end")
    ap.add_argument("--write-reset-pose", action="store_true",
                    help="write the first pose read into the recipe when it has none")
    ap.add_argument("--cal-mags", default=DEFAULT_CAL_MAGS, help="G12: right-stick magnitudes for the hold-time table")
    ap.add_argument("--cal-holds", default=DEFAULT_CAL_HOLDS, help="G12: hold times for the yaw table")
    ap.add_argument("--walk-holds", default=DEFAULT_WALK_HOLDS, help="G12: hold times for the walk table")
    ap.add_argument("--write-calibration", action="store_true",
                    help="G12: write the table into src/spectator/calibrations/<game>.json")
    ap.add_argument("--survey-walk", action="store_true",
                    help="after G2, walk a second in eight directions and turn the reset pose to the clearest one "
                         "(with --write-reset-pose, into the recipe)")
    ap.add_argument("--skip-top", type=int, default=0)
    ap.add_argument("--no-frames", action="store_true", help="do not save before/after frames")
    ap.add_argument("--frames", default=FRAMES_DIR)
    args = ap.parse_args()
    recipe = load_recipe(args.game)
    print(f"[harness] {recipe['name']} ({recipe['title']}), oracle {recipe.get('oracle', {}).get('type', 'frame_diff')}, "
          f"actuator {args.actuator}", flush=True)
    return run_nimbus(args, recipe) if args.actuator == "nimbus" else run_pad(args, recipe)


if __name__ == "__main__":
    sys.exit(main())
