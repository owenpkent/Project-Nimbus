"""
Per-game calibration for Spectator+ primitives.

A calibration is what the game test harness measured with an exact pad: how
far the view turns when the right stick is held at a magnitude for a time,
and how far the player walks when the left stick is held up. Games ramp
stick input (Source applies acceleration above a threshold), so each
magnitude carries several (hold, amount) samples rather than one rate, and
the hold for a wanted amount is found by piecewise-linear interpolation
between them, or by extending the last segment beyond them.

Files live in ``src/spectator/calibrations/<game>.json``::

    {
        "game": "left4dead2",
        "when": "2026-09-07 16:30:00",
        "turn_right_sign": -1,
        "yaw": {"0.40": [[0.1, -1.2], [0.25, -3.0], [0.5, -6.6], [1.0, -13.7]], ...},
        "walk": {"1.00": [[0.25, 28.0], [0.5, 57.0], [1.0, 114.0]]}
    }

``yaw`` samples are signed yaw deltas in degrees for a positive (right)
stick; ``turn_right_sign`` is the sign a right turn has in the game's
angles. ``walk`` samples are horizontal units for the left stick up.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

CALIBRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibrations")


def hold_for(samples: List[List[float]], amount: float) -> Optional[float]:
    """The hold time that yields ``amount`` from ``(hold, amount)`` samples.

    The samples are taken as starting from (0, 0), sorted by hold and read
    by absolute amount. Between samples the answer is linear; past the last
    sample the last segment's slope continues. ``None`` when the samples
    never grow, or when ``amount`` is not positive.
    """
    if amount <= 0:
        return None
    pts: List[Tuple[float, float]] = [(0.0, 0.0)]
    pts += sorted((float(t), abs(float(a))) for t, a in samples if float(t) > 0)
    for (t0, a0), (t1, a1) in zip(pts, pts[1:]):
        if a1 > a0 and a1 >= amount:
            return t0 + (amount - a0) * (t1 - t0) / (a1 - a0)
    if len(pts) >= 2:
        (t0, a0), (t1, a1) = pts[-2], pts[-1]
        if a1 > a0:
            return t1 + (amount - a1) * (t1 - t0) / (a1 - a0)
    return None


class GameCalibration:
    """One game's measured stick response, and the plans built from it.

    Parameters
    ----------
    data : dict
        The calibration file's content (see the module docstring).
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        self.game = str(data.get("game", ""))
        self.when = str(data.get("when", ""))
        self.turn_right_sign = 1 if int(data.get("turn_right_sign", -1)) >= 0 else -1
        self.yaw: Dict[float, List[List[float]]] = {float(k): list(v) for k, v in (data.get("yaw") or {}).items()}
        self.walk: Dict[float, List[List[float]]] = {float(k): list(v) for k, v in (data.get("walk") or {}).items()}

    @classmethod
    def load(cls, game: str, directory: str = CALIBRATIONS_DIR) -> "GameCalibration":
        """Load ``<directory>/<game>.json``. Raises ``FileNotFoundError`` when the game has none."""
        path = os.path.join(directory, f"{game}.json")
        with open(path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    @staticmethod
    def _plan(table: Dict[float, List[List[float]]], amount: float, max_hold: float,
              min_hold: float) -> Optional[Tuple[float, float]]:
        """The (magnitude, hold) that yields ``amount``: the smallest magnitude
        whose hold fits under ``max_hold`` and over ``min_hold``, else the
        largest magnitude with whatever hold it needs."""
        if amount <= 0 or not table:
            return None
        best: Optional[Tuple[float, float]] = None
        for m in sorted(table):
            h = hold_for(table[m], amount)
            if h is None:
                continue
            best = (m, h)
            if min_hold <= h <= max_hold:
                return best
        return best

    def plan_turn(self, degrees: float, max_hold: float = 2.0, min_hold: float = 0.2) -> Optional[Tuple[float, float]]:
        """Signed right-stick magnitude and hold for a turn of ``degrees``
        (positive turns right). Small angles get a small magnitude so the
        hold is long enough for timing error not to matter; large ones get
        the biggest magnitude the table has."""
        plan = self._plan(self.yaw, abs(degrees), max_hold, min_hold)
        if plan is None:
            return None
        m, h = plan
        return (m if degrees >= 0 else -m), h

    def plan_walk(self, units: float, max_hold: float = 4.0, min_hold: float = 0.2) -> Optional[Tuple[float, float]]:
        """Left-stick magnitude (up positive) and hold for ``units`` of forward travel."""
        plan = self._plan(self.walk, abs(units), max_hold, min_hold)
        if plan is None:
            return None
        m, h = plan
        return (m if units >= 0 else -m), h
