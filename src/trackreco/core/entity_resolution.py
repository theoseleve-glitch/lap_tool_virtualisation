from __future__ import annotations

from collections import defaultdict

from trackreco.models import CandidateRecord


def cluster_candidates(candidates: list[CandidateRecord]) -> list[list[CandidateRecord]]:
    buckets: dict[str, list[CandidateRecord]] = defaultdict(list)
    for c in candidates:
        key = f"{c.country.lower()}::{c.venue_name_normalized}"
        buckets[key].append(c)
    return list(buckets.values())
