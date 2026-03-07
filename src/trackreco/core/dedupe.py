from __future__ import annotations

from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Iterable

from trackreco.models import CandidateRecord


@dataclass(slots=True)
class MergeSuggestion:
    left_candidate_id: str
    right_candidate_id: str
    score: float
    reasons: list[str]
    action: str


def _dist_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    r = 6371.0
    dlat = radians(b_lat - a_lat)
    dlon = radians(b_lon - a_lon)
    x = sin(dlat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(dlon / 2) ** 2
    return 2 * r * atan2(sqrt(x), sqrt(1 - x))


def pair_score(a: CandidateRecord, b: CandidateRecord) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if a.venue_name_normalized == b.venue_name_normalized:
        score += 0.5
        reasons.append("name_exact")
    elif a.venue_name_normalized in b.venue_name_normalized or b.venue_name_normalized in a.venue_name_normalized:
        score += 0.3
        reasons.append("name_partial")

    if a.website and b.website and a.website.split("/")[2] == b.website.split("/")[2]:
        score += 0.25
        reasons.append("website_domain_match")

    if a.phone and b.phone and a.phone == b.phone:
        score += 0.2
        reasons.append("phone_match")

    if a.email and b.email and a.email.lower() == b.email.lower():
        score += 0.2
        reasons.append("email_match")

    if None not in (a.lat, a.lon, b.lat, b.lon):
        d = _dist_km(a.lat, a.lon, b.lat, b.lon)
        if d < 0.5:
            score += 0.2
            reasons.append("distance_lt_500m")
        elif d > 10:
            score -= 0.2
            reasons.append("distance_gt_10km")

    return max(0.0, min(1.0, score)), reasons


def build_merge_suggestions(candidates: Iterable[CandidateRecord], auto_merge_threshold: float = 0.85, suggest_threshold: float = 0.6) -> list[MergeSuggestion]:
    c = list(candidates)
    out: list[MergeSuggestion] = []
    for i, left in enumerate(c):
        for right in c[i + 1 :]:
            score, reasons = pair_score(left, right)
            if score >= auto_merge_threshold:
                action = "auto_merge"
            elif score >= suggest_threshold:
                action = "review_merge"
            else:
                continue
            out.append(MergeSuggestion(left.candidate_id, right.candidate_id, score, reasons, action))
    return out
