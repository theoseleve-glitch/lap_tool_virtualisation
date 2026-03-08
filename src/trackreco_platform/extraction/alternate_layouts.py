from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString

from .config import AlternateLayoutConfig


@dataclass
class AlternateLayoutResult:
    candidates: list[dict]
    evidence: dict


class AlternateLayoutAnalyzer:
    def __init__(self, config: AlternateLayoutConfig):
        self.config = config

    def run(self, base_centerline: LineString, branch_count: int) -> AlternateLayoutResult:
        candidates: list[dict] = []
        evidence = {"branch_count": branch_count, "base_length_m": base_centerline.length}
        if branch_count <= 0:
            return AlternateLayoutResult(candidates=[], evidence=evidence)
        alt_score = min(0.9, 0.5 + branch_count * 0.1)
        if alt_score >= self.config.min_alt_score:
            candidates.append(
                {
                    "layout_id": "alternate-1",
                    "score": alt_score,
                    "status": "manual_review_required",
                    "length_ratio": max(self.config.min_alt_length_ratio, 0.25),
                }
            )
        return AlternateLayoutResult(candidates=candidates, evidence=evidence)
