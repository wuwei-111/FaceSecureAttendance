"""人脸比对：距离阈值 + 与次优的最小间隔，降低误识别。"""

from __future__ import annotations

import os
from typing import Optional, TypeVar

T = TypeVar("T")


def face_match_threshold() -> float:
    return float(os.getenv("FACE_MATCH_THRESHOLD", "0.30"))


def face_match_min_margin() -> float:
    return float(os.getenv("FACE_MATCH_MIN_MARGIN", "0.05"))


def group_face_match_threshold() -> float:
    return float(os.getenv("GROUP_FACE_MATCH_THRESHOLD", "0.32"))


def group_face_match_min_margin() -> float:
    return float(os.getenv("GROUP_FACE_MATCH_MIN_MARGIN", "0.03"))


def pick_match_by_margin(
    scored: list[tuple[T, float]],
    *,
    threshold: Optional[float] = None,
    min_margin: Optional[float] = None,
) -> tuple[Optional[T], float, str]:
    th = face_match_threshold() if threshold is None else threshold
    margin = face_match_min_margin() if min_margin is None else min_margin
    if not scored:
        return None, 1.0, "below_threshold"
    ordered = sorted(scored, key=lambda x: x[1])
    best_item, best_d = ordered[0]
    second_d = ordered[1][1] if len(ordered) > 1 else 1.0
    if best_d > th:
        return None, best_d, "below_threshold"
    if len(ordered) > 1 and (second_d - best_d) < margin:
        return None, best_d, "ambiguous"
    return best_item, best_d, "ok"
