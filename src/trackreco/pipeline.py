from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import json

from trackreco.adapters.official import OfficialSourceAdapter
from trackreco.adapters.osm import OSMAdapter
from trackreco.adapters.venue_web import VenueWebsiteAdapter
from trackreco.config import PipelineConfig
from trackreco.core.dedupe import build_merge_suggestions
from trackreco.core.entity_resolution import cluster_candidates
from trackreco.core.normalization import evidence_to_candidate
from trackreco.io.writers import write_outputs
from trackreco.rules.decision import classify_cluster
from trackreco.utils.logging import JsonlLogger, StageLog


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_pipeline(config: PipelineConfig) -> Path:
    run_id = _run_id()
    out_dir = Path(config.output_root) / f"run_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger = JsonlLogger(out_dir / "run_log.jsonl")

    adapters = [
        OfficialSourceAdapter("ffsa", 1, config.sources.get("ffsa", [])),
        OfficialSourceAdapter("motorsport_uk", 1, config.sources.get("motorsport_uk", [])),
        OfficialSourceAdapter("abkc", 1, config.sources.get("abkc", [])),
        OSMAdapter(config.sources.get("osm", [])),
        VenueWebsiteAdapter(config.sources.get("venue_websites", [])),
    ]

    evidence_items = []
    for adapter in adapters:
        try:
            batch = list(adapter.fetch())
            evidence_items.extend(batch)
            logger.log(StageLog(datetime.now(timezone.utc).isoformat(), "harvest", "ok", f"{adapter.source_type}: {len(batch)}", {}))
        except Exception as exc:  # fail loudly
            logger.log(StageLog(datetime.now(timezone.utc).isoformat(), "harvest", "failed", f"{adapter.source_type} failed", {"error": str(exc)}))
            raise

    candidates = [evidence_to_candidate(e) for e in evidence_items]
    logger.log(StageLog(datetime.now(timezone.utc).isoformat(), "normalize", "ok", f"{len(candidates)} candidates", {}))

    merges = build_merge_suggestions(
        candidates,
        auto_merge_threshold=config.thresholds["auto_merge_threshold"],
        suggest_threshold=config.thresholds["suggest_merge_threshold"],
    )

    clusters = cluster_candidates(candidates)
    accepted = []
    review = []
    rejected = []

    for cluster in clusters:
        status, entity, meta = classify_cluster(cluster, config.pipeline_version)
        summary = {
            "candidate_ids": ",".join(c.candidate_id for c in cluster),
            "name": cluster[0].venue_name_raw,
            "country": cluster[0].country,
            "reason_codes": ",".join(meta.get("reason_codes", [])),
            "recommended_next_action": "manual validation of outdoor karting evidence",
            "unresolved_questions": "confirm recurring outdoor operation and active status",
            "source_urls": " | ".join(sorted({c.source_url for c in cluster})),
            "coordinate_summary": " | ".join(f"{c.lat},{c.lon}" for c in cluster if c.lat is not None and c.lon is not None),
            "merge_suggestions": ",".join(
                m.right_candidate_id
                for m in merges
                if m.left_candidate_id in {c.candidate_id for c in cluster} and m.action == "review_merge"
            ),
        }
        if status in {"confirmed_outdoor_kart_track", "probable_outdoor_kart_track"} and entity:
            accepted.append(entity)
            if status == "probable_outdoor_kart_track":
                review.append(summary | {"reason_code": "manual_review_required"})
        elif status == "reject":
            rejected.append(summary | {"reason_code": meta.get("reason_codes", ["unknown"])[0]})
        else:
            review.append(summary | {"reason_code": "manual_review_required"})

    write_outputs(out_dir, accepted, review, rejected, evidence_items, merges)

    report = {
        "run_id": run_id,
        "pipeline_version": config.pipeline_version,
        "counts": {
            "evidence": len(evidence_items),
            "candidates": len(candidates),
            "accepted": len(accepted),
            "review": len(review),
            "rejected": len(rejected),
        },
    }
    (out_dir / "run_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.log(StageLog(datetime.now(timezone.utc).isoformat(), "finalize", "ok", "run completed", report))
    return out_dir
