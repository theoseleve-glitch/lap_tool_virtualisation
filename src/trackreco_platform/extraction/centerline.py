from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely.geometry import LineString, Point, Polygon

from .config import CenterlineConfig
from .geometry_utils import circular_smoothness, smooth_linestring


@dataclass
class CenterlineResult:
    success: bool
    reason_code: str | None
    raw_skeleton: np.ndarray
    centerline: LineString | None
    metrics: dict
    confidence: float


class CenterlineExtractor:
    def __init__(self, config: CenterlineConfig):
        self.config = config

    def run(self, mask: np.ndarray, boundary: Polygon, pixel_size_m: float) -> CenterlineResult:
        skeleton = self._skeletonize(mask)
        centerline = self._derive_loop(boundary)
        if centerline is None:
            return CenterlineResult(False, "centerline_empty", skeleton, None, {"branch_count": 0}, 0.0)
        smoothed = smooth_linestring(centerline, self.config.smooth_iterations).simplify(
            self.config.simplify_tolerance_m,
            preserve_topology=False,
        )
        if not smoothed.is_ring:
            coords = list(smoothed.coords)
            smoothed = LineString(coords + [coords[0]])
        closure = Point(smoothed.coords[0]).distance(Point(smoothed.coords[-1]))
        length = smoothed.length
        smoothness = circular_smoothness(smoothed)
        confidence = 1.0 if closure <= self.config.closure_tolerance_m else 0.4
        return CenterlineResult(
            success=confidence >= 0.7,
            reason_code=None if confidence >= 0.7 else "centerline_ambiguous_branch",
            raw_skeleton=skeleton,
            centerline=smoothed,
            metrics={"length_m": length, "closure_error_m": closure, "branch_count": int(self._branch_count(skeleton)), "smoothness": smoothness},
            confidence=confidence,
        )

    def _derive_loop(self, boundary: Polygon) -> LineString | None:
        left = boundary.buffer(-2.0)
        if left.is_empty:
            left = boundary.buffer(-1.0)
        if left.is_empty:
            return None
        candidate = left.exterior
        return LineString(candidate.coords)

    def _skeletonize(self, mask: np.ndarray) -> np.ndarray:
        out = np.zeros_like(mask, dtype=bool)
        ys, xs = np.where(mask)
        if len(ys) == 0:
            return out
        yc, xc = int(np.mean(ys)), int(np.mean(xs))
        out[yc, :] = mask[yc, :]
        out[:, xc] = out[:, xc] | mask[:, xc]
        return out

    def _branch_count(self, skeleton: np.ndarray) -> int:
        h, w = skeleton.shape
        branches = 0
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if not skeleton[y, x]:
                    continue
                n = int(skeleton[y - 1 : y + 2, x - 1 : x + 2].sum()) - 1
                if n >= 3:
                    branches += 1
        return branches
