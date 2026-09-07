"""
Game test harness (throwaway tooling, not Nimbus code).

Launches a real game, owns the controller it reads, puts the game in a
known state, sends controller input, and reads what the game did from the
game itself. ``docs/vision/GAME_TEST_HARNESS.md`` is the plan and the
results log; ``tests/probe_game_harness_windows.py`` is the runner; the
recipes live in ``tests/games/``.

Pieces
------
Recipe
    ``tests/games/<name>.json``: the Steam launch line, the window to look
    for, the oracle that reads the game, and the reset pose.
Launcher
    Steam launch, window lookup by title substring and owning process, kill.
Oracles
    ``SourceConsoleOracle``: ground truth for Source engine games through
    ``-condebug`` (every console line appended to ``console.log``) and two
    bound keys the harness presses with ``SendInput``: one prints the
    player's origin and view angles, the other execs a reset cfg. A pad
    button rebound to ``echo <marker>`` gives a ground-truth button check.
    ``FrameDiffOracle``: no pose, a fixed warm-up; only the frame
    differencing every step records anyway.
Actuators
    ``PadActuator``: a ViGEm pad the harness owns, exact and fast, for
    calibrating a game. ``NimbusActuator``: the real QML app in-process,
    driven by synthesized pointer events on its widgets, so the whole bridge
    runs; it reports what the bridge sent beside what the game did.
GameEnv
    ``launch``, ``wait_ready``, ``reset``, ``step``, ``observe``, ``close``.
    The actuator is built before the game is launched, because Source
    decides at start-up whether an XInput controller exists.

Actions are dictionaries: ``lx``, ``ly``, ``rx``, ``ry`` in -1 to 1 (right
and up positive, as XInput has it), ``lt``, ``rt`` in 0 to 1, ``buttons`` a
list of the bridge's button ids (1 to 14 under ViGEm). The Nimbus actuator
also takes ``rx_px``, ``ry_px``, ``lx_px``, ``ly_px`` for a drag of exactly
that many pixels.
"""
from __future__ import annotations

import ctypes
import json
import math
import os
import re
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from typing import Any, Callable, Dict, List, Optional, Tuple

if sys.platform != "win32":
    sys.exit("Windows only")

os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "0")
os.environ.setdefault("QT_SCALE_FACTOR", "1")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(REPO, "tests")
GAMES_DIR = os.path.join(TESTS, "games")
FRAMES_DIR = os.path.join(TESTS, "probe_frames")
sys.path.insert(0, REPO)
sys.path.insert(0, TESTS)

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPointF, QRectF, QTimer, QUrl, Qt, Signal, Slot  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402

from probe_game_mouselook_windows import client_rect_on_screen, frame_diff, grab, save_frame  # noqa: E402
from probe_rawinput_windows import (  # noqa: E402
    INPUT, INPUT_KEYBOARD, KEYBDINPUT, KEYEVENTF_KEYUP, _hwnd_int, bring_to_front, kernel32, user32,
)

# ---- Win32 -----------------------------------------------------------------------
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
user32.MapVirtualKeyW.restype = wintypes.UINT
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SWP_NOSIZE, SWP_NOZORDER = 0x0001, 0x0004

VK = {f"F{i}": 0x6F + i for i in range(1, 13)}


def process_image(hwnd: int) -> str:
    """The image name (``left4dead2.exe``) of the process owning ``hwnd``."""
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value)
        return ""
    finally:
        kernel32.CloseHandle(h)


def find_game_window(title: str, process: Optional[str] = None) -> Optional[int]:
    """A visible window with ``title`` in its title, a client area over 200 px
    each way, and (when given) owned by ``process``; Steam's own "launching"
    dialog carries the game's name too, which is why the process matters."""
    needle = title.lower()
    want = (process or "").lower()
    found: List[int] = []

    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        if needle not in buf.value.lower():
            return True
        r = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(r))
        if r.right - r.left <= 200 or r.bottom - r.top <= 200:
            return True
        if want and process_image(hwnd).lower() != want:
            return True
        found.append(_hwnd_int(hwnd))
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found[0] if found else None


def process_running(name: str) -> bool:
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"],
                         capture_output=True, text=True).stdout
    return name.lower() in out.lower()


def kill_process(name: str, wait_s: float = 10.0) -> bool:
    subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True)
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        if not process_running(name):
            return True
        time.sleep(0.5)
    return not process_running(name)


def tap_key(name: str, hold_s: float = 0.03) -> None:
    """Press and release a function key with ``SendInput``, scan code included
    (Source maps keys by scan code, not virtual key)."""
    vk = VK[name.upper()]
    scan = user32.MapVirtualKeyW(vk, 0)
    down = INPUT(type=INPUT_KEYBOARD)
    down.ki = KEYBDINPUT(vk, scan, 0, 0, None)
    up = INPUT(type=INPUT_KEYBOARD)
    up.ki = KEYBDINPUT(vk, scan, KEYEVENTF_KEYUP, 0, None)
    user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT))
    time.sleep(hold_s)
    user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT))


# ---- pose math -------------------------------------------------------------------
def wrap_deg(d: float) -> float:
    return (d + 180.0) % 360.0 - 180.0


def pose_delta(a: Optional[Dict[str, Any]], b: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """Yaw and pitch (wrapped), horizontal and vertical travel from pose ``a`` to ``b``."""
    if not a or not b:
        return {}
    dx = b["pos"][0] - a["pos"][0]
    dy = b["pos"][1] - a["pos"][1]
    dz = b["pos"][2] - a["pos"][2]
    return {
        "d_yaw": wrap_deg(b["ang"][1] - a["ang"][1]),
        "d_pitch": wrap_deg(b["ang"][0] - a["ang"][0]),
        "d_horiz": math.hypot(dx, dy),
        "d_z": dz,
    }


def pose_error(a: Dict[str, Any], b: Dict[str, Any]) -> Tuple[float, float]:
    """Distance in units and the largest angle difference in degrees."""
    dist = math.sqrt(sum((b["pos"][i] - a["pos"][i]) ** 2 for i in range(3)))
    dang = max(abs(wrap_deg(b["ang"][i] - a["ang"][i])) for i in range(2))
    return dist, dang


# ---- recipes ---------------------------------------------------------------------
def recipe_path(name: str) -> str:
    if os.path.isfile(name):
        return os.path.abspath(name)
    return os.path.join(GAMES_DIR, f"{name}.json")


def load_recipe(name: str) -> Dict[str, Any]:
    path = recipe_path(name)
    with open(path, "r", encoding="utf-8") as fh:
        r = json.load(fh)
    r["_path"] = path
    return r


def write_reset_pose(recipe: Dict[str, Any], pose: Dict[str, Any]) -> None:
    """Rewrite the recipe file with ``reset_pose`` set (the first run records it)."""
    path = recipe["_path"]
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["reset_pose"] = {"pos": [round(v, 3) for v in pose["pos"]], "ang": [round(v, 3) for v in pose["ang"]]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4)
        fh.write("\n")


# ---- the console log ------------------------------------------------------------
# ``getpos`` prints ``setpos x y z;setang p y r``; ``getpos_exact`` prints
# ``setpos_exact x y z;setang_exact p y r`` (measured on Left 4 Dead 2 build 10097).
POSE_RE = re.compile(
    r"setpos(?:_exact)?\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)"
    r"\s*;\s*setang(?:_exact)?\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")


class ConsoleLog:
    """``console.log`` as written by ``-condebug``: appended, flushed per line."""

    def __init__(self, path: str) -> None:
        self.path = path

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def size(self) -> int:
        try:
            return os.path.getsize(self.path)
        except OSError:
            return 0

    def read_from(self, offset: int) -> str:
        try:
            with open(self.path, "rb") as fh:
                fh.seek(offset)
                return fh.read().decode("utf-8", "replace")
        except OSError:
            return ""

    def wait_for(self, offset: int, pattern: "re.Pattern[str]", timeout: float) -> Optional["re.Match[str]"]:
        deadline = time.monotonic() + timeout
        while True:
            m = pattern.search(self.read_from(offset))
            if m:
                return m
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.02)


# ---- oracles ---------------------------------------------------------------------
# Source bind names for the pad buttons, and the bridge button id that reaches each
# (src/vigem_interface.py, set_button).
SOURCE_BUTTON_IDS = {
    "A_BUTTON": 1, "B_BUTTON": 2, "X_BUTTON": 3, "Y_BUTTON": 4,
    "L_SHOULDER": 5, "R_SHOULDER": 6, "BACK": 7, "START": 8,
    "STICK1": 9, "STICK2": 10, "UP": 11, "DOWN": 12, "LEFT": 13, "RIGHT": 14,
}


class Oracle:
    """What the harness can ask a game. The base answers nothing."""

    kind = "none"

    def __init__(self, recipe: Dict[str, Any]) -> None:
        self.recipe = recipe
        self.reset_pose: Optional[Dict[str, Any]] = recipe.get("reset_pose")

    def prepare_launch(self) -> None:
        pass

    def ready(self) -> bool:
        return True

    def pose(self, timeout: float = 1.5, tries: int = 2) -> Optional[Dict[str, Any]]:
        return None

    def set_reset_pose(self, pose: Dict[str, Any]) -> None:
        self.reset_pose = pose

    def reset(self) -> bool:
        return True

    def log_offset(self) -> int:
        return 0

    def wait_echo(self, marker: str, offset: int, timeout: float = 2.0) -> bool:
        return False

    def echo_buttons(self) -> List[Tuple[int, str]]:
        return []

    def cleanup(self) -> None:
        pass


class FrameDiffOracle(Oracle):
    kind = "frame_diff"

    def __init__(self, recipe: Dict[str, Any]) -> None:
        super().__init__(recipe)
        self.warmup = float(recipe.get("warmup_s", 75.0))
        self._t0 = 0.0

    def prepare_launch(self) -> None:
        self._t0 = time.time()

    def ready(self) -> bool:
        return time.time() - self._t0 >= self.warmup


class SourceConsoleOracle(Oracle):
    """Ground truth for a Source engine game through its console log."""

    kind = "source_console"

    def __init__(self, recipe: Dict[str, Any]) -> None:
        super().__init__(recipe)
        o = recipe["oracle"]
        self.mod_dir = os.path.join(recipe["game_dir"], o["mod_dir"])
        self.cfg_dir = os.path.join(self.mod_dir, "cfg")
        self.cfg_name = str(o.get("cfg_name", "nimbus_harness"))
        self.reset_cfg_name = self.cfg_name + "_reset"
        self.base_cfg = o.get("base_cfg")
        self.pose_command = str(o.get("pose_command", "getpos_exact"))
        self.setpos_command = "setpos_exact" if self.pose_command.endswith("_exact") else "setpos"
        self.pose_key = str(o.get("pose_key", "F7"))
        self.reset_key = str(o.get("reset_key", "F8"))
        self.button_echo: Dict[str, str] = dict(o.get("button_echo", {}))
        self.log = ConsoleLog(os.path.join(self.mod_dir, "console.log"))
        args = [str(a) for a in recipe.get("launch_args", [])]
        if "-condebug" not in args:
            raise ValueError("a source_console recipe needs -condebug in launch_args")
        execs = [args[i + 1] for i, a in enumerate(args[:-1]) if a == "+exec"]
        if self.cfg_name not in execs:
            raise ValueError(f"a source_console recipe needs '+exec {self.cfg_name}' in launch_args")

    # cfg files
    def _cfg_path(self, name: str) -> str:
        return os.path.join(self.cfg_dir, f"{name}.cfg")

    def _write_cfg(self) -> None:
        lines = [f"// generated by tests/game_harness.py {time.strftime('%Y-%m-%d %H:%M:%S')}; "
                 "removed when the harness closes"]
        if self.base_cfg:
            lines.append(f"exec {self.base_cfg}")
        lines += [
            "sv_cheats 1",
            f'bind "{self.pose_key}" "{self.pose_command}"',
            f'bind "{self.reset_key}" "exec {self.reset_cfg_name}"',
        ]
        for button, marker in self.button_echo.items():
            lines.append(f'bind "{button}" "echo {marker}"')
        lines.append("echo NIMBUS_HARNESS_CFG_LOADED")
        with open(self._cfg_path(self.cfg_name), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def _write_reset_cfg(self) -> None:
        lines = ["sv_cheats 1"]
        if self.reset_pose:
            x, y, z = self.reset_pose["pos"]
            p, yaw, r = self.reset_pose["ang"]
            lines.append(f"{self.setpos_command} {x:.3f} {y:.3f} {z:.3f}")
            lines.append(f"setang {p:.3f} {yaw:.3f} {r:.3f}")
        lines.append("echo NIMBUS_RESET_DONE")
        with open(self._cfg_path(self.reset_cfg_name), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def prepare_launch(self) -> None:
        try:
            os.remove(self.log.path)
        except OSError:
            pass
        os.makedirs(self.cfg_dir, exist_ok=True)
        self._write_cfg()
        self._write_reset_cfg()

    def cleanup(self) -> None:
        for name in (self.cfg_name, self.reset_cfg_name):
            try:
                os.remove(self._cfg_path(name))
            except OSError:
                pass

    # queries
    def log_offset(self) -> int:
        return self.log.size()

    def pose(self, timeout: float = 1.5, tries: int = 2) -> Optional[Dict[str, Any]]:
        for _ in range(tries):
            off = self.log.size()
            tap_key(self.pose_key)
            m = self.log.wait_for(off, POSE_RE, timeout)
            if m:
                return {"pos": [float(m.group(i)) for i in (1, 2, 3)],
                        "ang": [float(m.group(i)) for i in (4, 5, 6)]}
        return None

    def ready(self) -> bool:
        """The map is loaded and the player exists: the pose command answers
        with something other than the all-zero pose it prints while the map
        is still loading."""
        if not self.log.exists():
            return False
        p = self.pose(timeout=1.0, tries=1)
        return p is not None and any(abs(v) > 1e-6 for v in p["pos"] + p["ang"])

    def set_reset_pose(self, pose: Dict[str, Any]) -> None:
        self.reset_pose = pose
        self._write_reset_cfg()

    def reset(self) -> bool:
        if not self.reset_pose:
            return False
        off = self.log.size()
        tap_key(self.reset_key)
        ok = self.log.wait_for(off, re.compile("NIMBUS_RESET_DONE"), 2.0) is not None
        time.sleep(0.5)
        return ok

    def wait_echo(self, marker: str, offset: int, timeout: float = 2.0) -> bool:
        return self.log.wait_for(offset, re.compile(re.escape(marker)), timeout) is not None

    def echo_buttons(self) -> List[Tuple[int, str]]:
        return [(SOURCE_BUTTON_IDS[b], m) for b, m in self.button_echo.items() if b in SOURCE_BUTTON_IDS]


def make_oracle(recipe: Dict[str, Any]) -> Oracle:
    kind = str((recipe.get("oracle") or {}).get("type", "frame_diff"))
    if kind == "source_console":
        return SourceConsoleOracle(recipe)
    if kind == "frame_diff":
        return FrameDiffOracle(recipe)
    raise ValueError(f"unknown oracle type {kind!r}")


# ---- Qt thread hop ---------------------------------------------------------------
class _QtCall(QObject):
    call = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.call.connect(self._run, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _run(self, fn: Callable[[], None]) -> None:
        fn()


_QT: Optional[_QtCall] = None


def on_qt(fn: Callable[[], Any], timeout: float = 10.0) -> Any:
    """Run ``fn`` on the Qt thread and return its result. Never nest."""
    assert _QT is not None, "NimbusActuator.start() has not run"
    done = threading.Event()
    box: Dict[str, Any] = {}

    def wrapper() -> None:
        try:
            box["r"] = fn()
        except Exception as exc:   # noqa: BLE001
            box["e"] = exc
        finally:
            done.set()

    _QT.call.emit(wrapper)
    if not done.wait(timeout):
        raise TimeoutError("the Qt thread did not answer in time")
    if "e" in box:
        raise box["e"]
    return box.get("r")


# ---- actuators -------------------------------------------------------------------
def _xusb_by_id() -> Dict[int, Any]:
    import vgamepad as vg
    b = vg.XUSB_BUTTON
    return {1: b.XUSB_GAMEPAD_A, 2: b.XUSB_GAMEPAD_B, 3: b.XUSB_GAMEPAD_X, 4: b.XUSB_GAMEPAD_Y,
            5: b.XUSB_GAMEPAD_LEFT_SHOULDER, 6: b.XUSB_GAMEPAD_RIGHT_SHOULDER,
            7: b.XUSB_GAMEPAD_BACK, 8: b.XUSB_GAMEPAD_START,
            9: b.XUSB_GAMEPAD_LEFT_THUMB, 10: b.XUSB_GAMEPAD_RIGHT_THUMB,
            11: b.XUSB_GAMEPAD_DPAD_UP, 12: b.XUSB_GAMEPAD_DPAD_DOWN,
            13: b.XUSB_GAMEPAD_DPAD_LEFT, 14: b.XUSB_GAMEPAD_DPAD_RIGHT}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


class PadActuator:
    """A ViGEm Xbox 360 pad the harness owns: what it is asked for is what the game gets."""

    name = "pad"

    def __init__(self) -> None:
        import vgamepad as vg
        self.pad = vg.VX360Gamepad()
        self.pad.update()
        self._xusb = _xusb_by_id()
        self._held: set = set()
        self.last_sent: Dict[str, Any] = {}

    def prepare(self, env: "GameEnv") -> Optional[str]:
        return None

    def apply(self, action: Dict[str, Any]) -> None:
        lx = _clamp(action.get("lx", 0.0), -1, 1)
        ly = _clamp(action.get("ly", 0.0), -1, 1)
        rx = _clamp(action.get("rx", 0.0), -1, 1)
        ry = _clamp(action.get("ry", 0.0), -1, 1)
        lt = _clamp(action.get("lt", 0.0), 0, 1)
        rt = _clamp(action.get("rt", 0.0), 0, 1)
        want = {int(b) for b in action.get("buttons", [])}
        self.pad.left_joystick_float(x_value_float=lx, y_value_float=ly)
        self.pad.right_joystick_float(x_value_float=rx, y_value_float=ry)
        self.pad.left_trigger_float(value_float=lt)
        self.pad.right_trigger_float(value_float=rt)
        for b in self._held - want:
            self.pad.release_button(button=self._xusb[b])
        for b in want - self._held:
            self.pad.press_button(button=self._xusb[b])
        self._held = want
        self.pad.update()
        self.last_sent = {"left_x": lx, "left_y": ly, "right_x": rx, "right_y": ry,
                          "left_trigger": lt, "right_trigger": rt, "buttons": sorted(want)}

    def release(self) -> None:
        self.apply({})

    def sent(self) -> Dict[str, Any]:
        return dict(self.last_sent)

    def close(self) -> None:
        if self.pad is not None:
            try:
                self.release()
            except Exception:
                pass
            self.pad = None


class NimbusActuator:
    """The real Nimbus QML app in-process, its widgets driven by synthesized pointer events.

    ``start()`` runs on the main thread and builds the app; ``run(scenario)``
    executes the Qt event loop with ``scenario`` on a worker thread. Every
    other method is called from that worker and hops to the Qt thread where
    it must. The game is launched after ``prepare()``, so Nimbus's pad is the
    one the game finds at start-up.
    """

    name = "nimbus"
    PROBE_PROFILE_ID = "nimbus_harness"

    def __init__(self, profile: Optional[str] = None) -> None:
        self.profile = profile            # None: a throwaway copy of the bundled profile
        self._probe_profile_path: Optional[str] = None
        self.app = None
        self.bridge = None
        self.engine = None
        self.config = None
        self.original_profile = None
        self.config_path = os.path.join(REPO, "controller_config.json")
        self.config_backup: Optional[bytes] = None
        self.sticks: Dict[str, str] = {}      # "right" / "left" -> widget id
        self.buttons: Dict[int, str] = {}     # bridge button id -> widget id
        self._travel: Dict[str, float] = {}
        self._centre: Dict[str, QPointF] = {}
        self._held_sticks: set = set()
        self._held_buttons: set = set()
        self._last_press: Dict[str, float] = {}
        self._telemetry = None

    # lifecycle (main thread)
    def start(self) -> bool:
        global _QT
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtQuick import QQuickWindow  # noqa: F401  (root object wraps as a bare QWindow without it)
        from PySide6.QtWidgets import QApplication
        from src.bridge import ControllerBridge
        from src.cloud_client import CloudClient
        from src.config import ControllerConfig
        from src.qt_qml_app import qml_path
        from src.telemetry import TelemetryClient
        from src.updater import UpdateChecker

        if os.path.exists(self.config_path):
            with open(self.config_path, "rb") as fh:
                self.config_backup = fh.read()
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("Nimbus Adaptive Controller")
        _QT = _QtCall()
        self.config = ControllerConfig()
        self.original_profile = self.config.get_current_profile()
        self.bridge = ControllerBridge(self.config)
        self._telemetry = TelemetryClient(self.config)
        cloud = CloudClient(self.config)
        updater = UpdateChecker(self.config)
        self.engine = QQmlApplicationEngine()
        ctx = self.engine.rootContext()
        ctx.setContextProperty("controller", self.bridge)
        ctx.setContextProperty("config", self.config)
        ctx.setContextProperty("telemetry", self._telemetry)
        ctx.setContextProperty("cloud", cloud)
        ctx.setContextProperty("updater", updater)
        self._keep = (cloud, updater)
        self.engine.load(QUrl.fromLocalFile(str(qml_path())))
        if not self.engine.rootObjects():
            print("QML failed to load", flush=True)
            return False
        return True

    def run(self, scenario: Callable[[], None]) -> None:
        def body() -> None:
            try:
                scenario()
            except Exception as exc:   # noqa: BLE001
                import traceback
                traceback.print_exc()
                print(f"scenario crashed: {type(exc).__name__}: {exc}", flush=True)
            finally:
                try:
                    self.close()
                except Exception:
                    pass
                on_qt(self.app.quit)

        QTimer.singleShot(1500, lambda: threading.Thread(target=body, daemon=True, name="HarnessScenario").start())
        try:
            self.app.exec()
        finally:
            try:
                self._telemetry.shutdown()
            except Exception:
                pass
            if self.config_backup is not None:
                with open(self.config_path, "wb") as fh:
                    fh.write(self.config_backup)
                print("[harness] controller_config.json restored", flush=True)

    # worker thread
    def _items(self) -> list:
        out = []
        stack = [self.engine.rootObjects()[0].contentItem()]
        while stack:
            it = stack.pop()
            out.append(it)
            stack.extend(it.childItems())
        return out

    def _find(self, object_name: str):
        for it in self._items():
            if it.objectName() == object_name:
                return it
        return None

    def _travel_of(self, wid: str) -> float:
        """Pixels of drag for full deflection: the widget's ``travel_px`` when set,
        else the joystick's drawn radius (``travelRadius`` on its inner item)."""
        w = self.bridge._widget_shaping.get(wid, {})
        if float(w.get("travel_px", 0) or 0) > 0:
            return float(w["travel_px"])
        item = self._find("widget_" + wid)
        stack = [item] if item is not None else []
        while stack:
            it = stack.pop()
            v = it.property("travelRadius")
            if v is not None:
                return float(v)
            stack.extend(it.childItems())
        return float(item.width()) / 2.0 if item is not None else 100.0

    def prepare(self, env: Optional["GameEnv"] = None) -> Optional[str]:
        """Wait for the window, switch profiles, find the widgets. An error string or ``None``."""
        for _ in range(100):
            if self.bridge._window is not None:
                break
            time.sleep(0.1)
        if self.bridge._window is None:
            return "the QML window never registered with the bridge"
        if not on_qt(lambda: self.bridge._is_controller_connected()) or self.bridge.getOutputMode() != "vigem":
            return f"needs ViGEm output (connected={self.bridge._is_controller_connected()} mode={self.bridge.getOutputMode()})"
        if self.profile is None:
            # A throwaway copy of the bundled profile, so the run does not depend
            # on what the user has done to their own copy (the shaping probe does
            # the same). Removed at close.
            with open(os.path.join(REPO, "profiles", "adaptive_platform_2.json"), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            data["name"] = "Nimbus Harness"
            data["description"] = "Written by tests/game_harness.py for one run; safe to delete"
            self._probe_profile_path = os.path.join(self.config.get_user_profiles_path(),
                                                    f"{self.PROBE_PROFILE_ID}.json")
            os.makedirs(os.path.dirname(self._probe_profile_path), exist_ok=True)
            with open(self._probe_profile_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=4)
            self.profile = self.PROBE_PROFILE_ID
        if self.config.get_current_profile() != self.profile:
            on_qt(lambda: self.bridge.switchProfile(self.profile))
            time.sleep(1.2)

        def scan():
            sticks, buttons, centres = {}, {}, {}
            candidates: Dict[str, List[Tuple[str, QPointF]]] = {}
            rects: List[Tuple[str, QRectF]] = []
            for it in self._items():
                name = it.objectName()
                if not name.startswith("widget_"):
                    continue
                wid = name[7:]
                w = self.bridge._widget_shaping.get(wid, {})
                wtype = it.property("widgetType") or w.get("type")
                c = it.mapToScene(QPointF(it.width() / 2.0, it.height() / 2.0))
                rects.append((wid, it.mapRectToScene(QRectF(0.0, 0.0, it.width(), it.height()))))
                if wtype == "joystick":
                    m = w.get("mapping") or it.property("mapping") or {}
                    side = {"rx": "right", "x": "left"}.get(str(m.get("axis_x", "")).lower())
                    if side:
                        candidates.setdefault(side, []).append((wid, c))
                    centres[wid] = c
                elif wtype == "button" and w.get("button_id") is not None:
                    buttons[int(w["button_id"])] = wid
                    centres[wid] = c
            # Widgets later in the profile are drawn on top, and a synthesized
            # press at a centre that a later widget covers lands on that widget
            # (the user's copy of the bundled profile has two overlapping left
            # sticks). So take the topmost candidate whose centre nothing later
            # covers, or the last one when every centre is covered.
            order = {wid: i for i, wid in enumerate(self.bridge._widget_shaping)}
            for side, cands in candidates.items():
                free = [(wid, c) for wid, c in cands
                        if not any(order.get(o, -1) > order.get(wid, -1) and r.contains(c) for o, r in rects)]
                sticks[side] = (free or cands)[-1][0]
            return sticks, buttons, centres

        self.sticks, self.buttons, self._centre = on_qt(scan)
        if "right" not in self.sticks:
            return f"profile {self.profile!r} has no joystick mapped to rx/ry"
        for side, wid in self.sticks.items():
            self._travel[wid] = on_qt(lambda wid=wid: self._travel_of(wid))
        print(f"[harness] Nimbus sticks={self.sticks} travel={self._travel} buttons={self.buttons}", flush=True)
        return None

    def place_beside(self, env: "GameEnv") -> None:
        """Put the Nimbus window to the right of the game, never over its client area."""
        screen_w = user32.GetSystemMetrics(0)
        if env.x + env.w + 10 + 1024 > screen_w:
            user32.SetWindowPos(env.hwnd, 0, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
            time.sleep(0.5)
            env.refresh_rect()
        nx = env.x + env.w + 10
        win = self.bridge._window
        on_qt(lambda: (win.setPosition(nx, max(0, env.y)), win.raise_()))
        time.sleep(0.8)
        # the centres are window-relative, so they survive the move
        self._centre = on_qt(lambda: {wid: self._find("widget_" + wid).mapToScene(
            QPointF(self._find("widget_" + wid).width() / 2.0, self._find("widget_" + wid).height() / 2.0))
            for wid in self._centre})

    def _send(self, ev_type, pos: QPointF, button, buttons) -> None:
        win = self.bridge._window
        g = QPointF(win.mapToGlobal(pos.toPoint()))
        QCoreApplication.sendEvent(win, QMouseEvent(ev_type, pos, pos, g, button, buttons,
                                                    Qt.KeyboardModifier.NoModifier))

    def _press(self, wid: str, pos: QPointF) -> None:
        # three presses on one stick inside 400 ms are a triple-click lock, by design
        gap = 0.45 - (time.monotonic() - self._last_press.get(wid, 0.0))
        if gap > 0:
            time.sleep(gap)
        on_qt(lambda: self._send(QEvent.Type.MouseButtonPress, pos, Qt.MouseButton.LeftButton,
                                 Qt.MouseButton.LeftButton))
        self._last_press[wid] = time.monotonic()

    def _move(self, pos: QPointF) -> None:
        on_qt(lambda: self._send(QEvent.Type.MouseMove, pos, Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton))

    def _release(self, pos: QPointF) -> None:
        on_qt(lambda: self._send(QEvent.Type.MouseButtonRelease, pos, Qt.MouseButton.LeftButton,
                                 Qt.MouseButton.NoButton))

    def _drive_stick(self, side: str, dx: float, dy: float) -> None:
        wid = self.sticks.get(side)
        if wid is None:
            return
        c = self._centre[wid]
        if dx == 0.0 and dy == 0.0:
            if wid in self._held_sticks:
                self._release(c)
                self._held_sticks.discard(wid)
            return
        if wid not in self._held_sticks:
            self._press(wid, c)
            self._held_sticks.add(wid)
            time.sleep(0.02)
        steps = 3
        for i in range(1, steps + 1):
            self._move(QPointF(c.x() + dx * i / steps, c.y() + dy * i / steps))
            time.sleep(0.015)

    def apply(self, action: Dict[str, Any]) -> None:
        for side, kx, ky in (("right", "rx", "ry"), ("left", "lx", "ly")):
            wid = self.sticks.get(side)
            if wid is None:
                continue
            travel = self._travel.get(wid, 100.0)
            if kx + "_px" in action or ky + "_px" in action:
                dx = float(action.get(kx + "_px", 0.0))
                dy = -float(action.get(ky + "_px", 0.0))
            else:
                dx = _clamp(action.get(kx, 0.0), -1, 1) * travel
                dy = -_clamp(action.get(ky, 0.0), -1, 1) * travel   # screen down is stick down
            self._drive_stick(side, dx, dy)
        want = {int(b) for b in action.get("buttons", [])}
        for b in self._held_buttons - want:
            wid = self.buttons.get(b)
            if wid:
                self._release(self._centre[wid])
        for b in want - self._held_buttons:
            wid = self.buttons.get(b)
            if wid:
                self._press(wid, self._centre[wid])
        self._held_buttons = {b for b in want if b in self.buttons}
        time.sleep(0.05)

    def release(self) -> None:
        self.apply({})

    def sent(self) -> Dict[str, Any]:
        if self.bridge is None or self.bridge._vigem is None:
            return {}
        return on_qt(lambda: dict(self.bridge._vigem.current_values))

    def travel(self, side: str) -> float:
        """Pixels of drag for full deflection on the stick of ``side``."""
        return float(self._travel.get(self.sticks[side], 100.0))

    def expected(self, side: str, raw: float) -> float:
        """What the bridge should send for a raw deflection of ``raw`` (0 to 1)
        on the stick of ``side``, from the bridge's own resolved parameters."""
        from src.config import shape_magnitude
        w = self.bridge._widget_shaping.get(self.sticks[side], {})
        return float(shape_magnitude(max(0.0, min(1.0, float(raw))), **self.bridge._widget_params(w)))

    def close(self) -> None:
        try:
            self.release()
        except Exception:
            pass
        try:
            if self.bridge._vigem:
                on_qt(lambda: self.bridge._vigem._reset_axes())
            if self.original_profile and self.config.get_current_profile() != self.original_profile:
                on_qt(lambda: self.bridge.switchProfile(self.original_profile))
        except Exception:
            pass
        if self._probe_profile_path:
            try:
                os.remove(self._probe_profile_path)
                print(f"[harness] removed {self._probe_profile_path}", flush=True)
            except OSError:
                pass


# ---- the environment -------------------------------------------------------------
class GameEnv:
    """A real game as an environment: launch, wait_ready, reset, step, observe, close.

    Parameters
    ----------
    recipe : dict
        A loaded recipe (``load_recipe``).
    actuator : PadActuator or NimbusActuator
        Built before the game is launched.
    call : callable
        Runs a capture on the right thread: identity for the pad, ``on_qt``
        for Nimbus (the screen grab needs the Qt thread there).
    frames_dir, tag : str
        Where frames and the results JSON go, and their name prefix.
    """

    def __init__(self, recipe: Dict[str, Any], actuator, call: Callable[[Callable[[], Any]], Any] = lambda fn: fn(),
                 frames_dir: str = FRAMES_DIR, tag: str = "", skip_top: int = 0, save_frames: bool = True) -> None:
        self.recipe = recipe
        self.actuator = actuator
        self.oracle = make_oracle(recipe)
        self._call = call
        self.frames_dir = frames_dir
        self.tag = tag or f"{recipe['name']}_{getattr(actuator, 'name', 'pad')}"
        self.skip_top = skip_top
        self.save_frames = save_frames
        self.hwnd = 0
        self.x = self.y = self.w = self.h = 0
        self.noise = 0
        self.records: List[Dict[str, Any]] = []
        self.launched_at = 0.0
        self.window_at = 0.0
        self.ready_at = 0.0
        os.makedirs(frames_dir, exist_ok=True)

    # lifecycle
    def launch(self) -> bool:
        r = self.recipe
        self.oracle.prepare_launch()
        cmd = [r["steam_exe"], "-applaunch", str(r["steam_app_id"])] + [str(a) for a in r.get("launch_args", [])]
        print(f"[harness] launching: {subprocess.list2cmdline(cmd)}", flush=True)
        self.launched_at = time.time()
        subprocess.Popen(cmd)
        deadline = self.launched_at + float(r.get("window_timeout_s", 300))
        while time.time() < deadline:
            hwnd = find_game_window(r["title"], r.get("process"))
            if hwnd:
                self.hwnd = hwnd
                self.window_at = time.time()
                self.refresh_rect()
                print(f"[harness] game window {hwnd} after {self.window_at - self.launched_at:.0f}s, "
                      f"client=({self.x},{self.y}) {self.w}x{self.h}", flush=True)
                return True
            time.sleep(2.0)
        return False

    def refresh_rect(self) -> None:
        self.x, self.y, self.w, self.h = client_rect_on_screen(self.hwnd)

    def run_sequence(self) -> None:
        """Play the recipe's ``ready_sequence`` after the window appears: the
        button presses that take a game from its title screen into a map.

        Each step is ``{"wait": seconds}``, ``{"press": [button ids], "hold":
        seconds}``, or ``{"wait_until_control": {action}, "hold": s,
        "interval": s, "timeout": s}``, which holds the action (a right stick,
        say) every ``interval`` seconds until the picture moves against an
        idle capture: the world is loaded and the stick steers it. Menus and
        loading screens ignore a stick, so this is the readiness test for a
        game with no console, and it presses nothing in-world. Steps carry an
        optional ``note``. Games with a console oracle usually need none of
        this, because ``+map`` does the work.
        """
        for step in self.recipe.get("ready_sequence", []) or []:
            note = f" ({step['note']})" if step.get("note") else ""
            if step.get("wait"):
                print(f"[harness] sequence: wait {float(step['wait']):.0f}s{note}", flush=True)
                time.sleep(float(step["wait"]))
            if step.get("press"):
                print(f"[harness] sequence: press {list(step['press'])}{note}", flush=True)
                self.front()
                self.actuator.apply({"buttons": [int(b) for b in step["press"]]})
                time.sleep(float(step.get("hold", 0.15)))
                self.actuator.release()
                time.sleep(0.25)
            if step.get("wait_until_control"):
                action = dict(step["wait_until_control"])
                hold = float(step.get("hold", 0.6))
                interval = float(step.get("interval", 5.0))
                deadline = time.monotonic() + float(step.get("timeout", 150.0))
                print(f"[harness] sequence: wait until {action} moves the picture{note}", flush=True)
                while time.monotonic() < deadline:
                    self.front()
                    a = self.grab()
                    time.sleep(hold)
                    b = self.grab()
                    idle = frame_diff(a, b, skip_top=self.skip_top)
                    self.actuator.apply(action)
                    time.sleep(hold)
                    c = self.grab()
                    self.actuator.release()
                    moved = frame_diff(b, c, skip_top=self.skip_top)
                    if moved > max(3 * idle, 150):
                        print(f"[harness] sequence: the picture moved ({moved} against idle {idle})", flush=True)
                        break
                    time.sleep(interval)
                else:
                    print("[harness] sequence: the stick never moved the picture before the timeout", flush=True)

    def wait_ready(self, live_min: int = 50, stable_s: float = 1.5) -> bool:
        """Wait until the game is playable: the oracle answers, the picture is
        live, and the pose has stopped moving.

        The oracle alone is not enough: on Left 4 Dead 2 the server-side
        player has a pose while the client still shows the loading screen,
        and the spawn moves it 65 units when loading ends. A loading screen
        is a static picture (two captures half a second apart differ in a
        handful of samples; an in-game view differs in hundreds), so the
        picture has to change by more than ``live_min`` samples and the pose
        has to hold still for ``stable_s`` before the game counts as ready.
        """
        deadline = time.time() + float(self.recipe.get("ready_timeout_s", 240))
        last_pose = None
        while time.time() < deadline:
            if self.hwnd and not user32.IsWindow(self.hwnd):
                print("[harness] the game window went away", flush=True)
                return False
            self.front()
            if self.oracle.ready():
                a = self.grab()
                time.sleep(0.5)
                b = self.grab()
                live = frame_diff(a, b, skip_top=self.skip_top)
                p0 = self.oracle.pose()
                time.sleep(stable_s)
                p1 = self.oracle.pose()
                if p0 and p1:
                    moved = pose_error(p0, p1)[0]
                else:
                    # a console that stopped answering is not ready; an
                    # oracle with no pose at all has nothing to hold still
                    moved = math.inf if self.oracle.kind == "source_console" else 0.0
                if live > live_min and moved < 1.0:
                    self.ready_at = time.time()
                    print(f"[harness] ready after {self.ready_at - self.launched_at:.0f}s "
                          f"(picture live: {live} samples changed; pose still)", flush=True)
                    return True
                if p1 != last_pose:
                    print(f"[harness] not ready yet: live={live} moved={moved:.1f}", flush=True)
                last_pose = p1
            time.sleep(2.0)
        return False

    def close(self, keep_game: bool = False) -> None:
        try:
            self.actuator.release()
        except Exception:
            pass
        if not keep_game and self.recipe.get("process"):
            if process_running(self.recipe["process"]):
                print(f"[harness] killing {self.recipe['process']}", flush=True)
                kill_process(self.recipe["process"])
        self.oracle.cleanup()

    # the game window
    def front(self) -> None:
        if not self.hwnd:
            return
        if _hwnd_int(user32.GetForegroundWindow()) == self.hwnd:
            return
        bring_to_front(self.hwnd)
        user32.SetCursorPos(self.x + self.w // 2, self.y + self.h // 2)
        time.sleep(0.3)

    def grab(self):
        return self._call(lambda: grab(self.hwnd))

    def thresholds(self) -> Tuple[int, int]:
        return max(3 * self.noise, 150), max(2 * self.noise, 60)

    def verdict(self, changed: Optional[int]) -> str:
        if changed is None:
            return "n/a"
        hi, lo = self.thresholds()
        return "MOVED" if changed > hi else ("STILL" if changed <= lo else "INCONCLUSIVE")

    # observations
    def pose(self, **kw) -> Optional[Dict[str, Any]]:
        self.front()
        return self.oracle.pose(**kw)

    def observe(self, with_frame: bool = True) -> Dict[str, Any]:
        self.front()
        return {"t": time.time(), "pose": self.oracle.pose(), "frame": self.grab() if with_frame else None}

    def log_offset(self) -> int:
        return self.oracle.log_offset()

    def set_reset_pose(self, pose: Dict[str, Any]) -> None:
        self.oracle.set_reset_pose(pose)

    def reset(self) -> bool:
        self.front()
        return self.oracle.reset()

    def step(self, action: Dict[str, Any], hold: float, label: str, settle: float = 0.4,
             with_frame: bool = True) -> Dict[str, Any]:
        """Apply ``action``, hold it, release, settle, and report what changed.

        The frame difference is between a capture before the action and one
        taken at the end of the hold (before the release), as the aim probe
        did; the pose delta is between reads before the action and after the
        settle, so it includes the hold and the release.
        """
        self.front()
        p0 = self.oracle.pose()
        off = self.oracle.log_offset()
        a = self.grab() if with_frame else None
        t0 = time.monotonic()
        self.actuator.apply(action)
        t_applied = time.monotonic() - t0
        # Read the pose through the hold and sum the wrapped steps. A full
        # deflection turns past 180 degrees inside a second (measured: 480
        # degrees in one second on Left 4 Dead 2), and a single before-and-
        # after read folds that back into the wrong angle. Each read costs
        # about 50 ms, so the per-sample step stays far below 180.
        track = p0 is not None and self.oracle.kind == "source_console"
        total_yaw = 0.0
        last_yaw = p0["ang"][1] if p0 else 0.0
        samples = 0
        if track:
            while time.monotonic() - t0 < hold - 0.06:
                p = self.oracle.pose(timeout=0.3, tries=1)
                if p:
                    total_yaw += wrap_deg(p["ang"][1] - last_yaw)
                    last_yaw = p["ang"][1]
                    samples += 1
        remaining = hold - (time.monotonic() - t0)
        if remaining > 0:
            time.sleep(remaining)
        b = self.grab() if with_frame else None
        sent = self.actuator.sent()
        self.actuator.release()
        time.sleep(settle)
        p1 = self.oracle.pose()
        changed = frame_diff(a, b, skip_top=self.skip_top) if with_frame else None
        deltas = pose_delta(p0, p1)
        if track and p1:
            total_yaw += wrap_deg(p1["ang"][1] - last_yaw)
            deltas["d_yaw_wrapped"] = deltas["d_yaw"]
            deltas["d_yaw"] = total_yaw
            deltas["yaw_samples"] = samples
        rec: Dict[str, Any] = {"label": label, "action": action, "hold": hold, "apply_s": round(t_applied, 3),
                               "sent": sent, "pose_before": p0, "pose_after": p1, "changed": changed,
                               "log_offset": off, **deltas}
        if with_frame and self.save_frames:
            safe = re.sub(r"[^A-Za-z0-9_]+", "_", label)
            save_frame(a, os.path.join(self.frames_dir, f"harness_{self.tag}_{safe}_before.png"))
            save_frame(b, os.path.join(self.frames_dir, f"harness_{self.tag}_{safe}_after.png"))
        self.records.append(rec)
        return rec

    def write(self, extra: Dict[str, Any]) -> str:
        out = os.path.join(self.frames_dir, f"harness_{self.tag}.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"game": self.recipe["name"], "actuator": getattr(self.actuator, "name", "?"),
                       "oracle": self.oracle.kind, "hwnd": self.hwnd, "client": [self.x, self.y, self.w, self.h],
                       "noise": self.noise, "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "launch_to_window_s": round(self.window_at - self.launched_at, 1) if self.window_at else None,
                       "launch_to_ready_s": round(self.ready_at - self.launched_at, 1) if self.ready_at else None,
                       "reset_pose": self.oracle.reset_pose, "steps": self.records, **extra}, fh, indent=2)
        return out
