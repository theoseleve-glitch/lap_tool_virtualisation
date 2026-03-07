from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import csv
import json

from trackreco.core.dedupe import MergeSuggestion
from trackreco.models import CandidateRecord, SourceEvidence, VenueEntity


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(
    output_dir: Path,
    accepted: list[VenueEntity],
    review_queue: list[dict],
    rejected: list[dict],
    evidence_items: list[SourceEvidence],
    merge_candidates: list[MergeSuggestion],
) -> None:
    accepted_rows = [asdict(v) for v in accepted]
    _write_csv(output_dir / "master_tracks.csv", accepted_rows)
    (output_dir / "master_tracks.json").write_text(json.dumps(accepted_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    _write_csv(output_dir / "candidate_review_queue.csv", review_queue)
    _write_csv(output_dir / "rejected_candidates.csv", rejected)
    _write_csv(output_dir / "merge_candidates.csv", [asdict(m) for m in merge_candidates if m.action == "review_merge"])

    with (output_dir / "source_evidence.jsonl").open("w", encoding="utf-8") as fh:
        for item in evidence_items:
            fh.write(json.dumps(item.to_json(), ensure_ascii=False) + "\n")

    points = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"venue_id": v.venue_id, "name": v.canonical_name},
                "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]} if v.lon is not None and v.lat is not None else None,
            }
            for v in accepted
        ],
    }
    (output_dir / "accepted_points.geojson").write_text(json.dumps(points, ensure_ascii=False, indent=2), encoding="utf-8")
