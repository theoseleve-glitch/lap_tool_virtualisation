from __future__ import annotations

from collections import Counter

from trackreco.geo.enrichment import derive_geometry
from trackreco.models import CandidateRecord, VenueEntity, deterministic_id, utc_now_iso


def _mode(values: list[str], default: str = "unclear") -> str:
    clean = [v for v in values if v]
    if not clean:
        return default
    return Counter(clean).most_common(1)[0][0]


def classify_cluster(candidates: list[CandidateRecord], pipeline_version: str) -> tuple[str, VenueEntity | None, dict]:
    reasons: list[str] = []
    source_types = sorted({c.source_type for c in candidates})
    now = utc_now_iso()

    has_official = any(c.source_confidence_tier == 1 for c in candidates)
    if has_official:
        reasons.append("confirmed_by_official_source")
    if len(source_types) >= 2:
        reasons.append("confirmed_by_multiple_independent_sources")

    outdoor_values = [c.outdoor_status for c in candidates]
    kart_values = [c.karting_relevance_status for c in candidates]
    op_values = [c.operating_status for c in candidates]
    recurring_values = [c.recurring_venue_status for c in candidates]

    outdoor = _mode(outdoor_values)
    kart = _mode(kart_values)
    existing = "unknown" if _mode(op_values) == "unclear" else _mode(op_values)
    recurring = _mode(recurring_values)

    if any(v == "confirmed_indoor" for v in outdoor_values):
        reasons.append("indoor_only_evidence")
    if any(c.mixed_mode_flag for c in candidates):
        reasons.append("mixed_indoor_outdoor")
    if any(v == "temporary_or_event_only" for v in recurring_values):
        reasons.append("temporary_event_only")

    if any(c.osm_tags.get("sport") == "karting" or c.osm_tags.get("highway") == "raceway" for c in candidates):
        reasons.append("osmtag_supports_karting")
    if any(c.website for c in candidates):
        reasons.append("venue_website_confirms_location")

    if outdoor in {"confirmed_indoor", "probable_indoor"}:
        reasons.append("not_a_kart_track")
        return "reject", None, {"reason_codes": sorted(set(reasons + ["indoor_only_evidence"]))}

    if recurring == "temporary_or_event_only":
        return "reject", None, {"reason_codes": sorted(set(reasons + ["temporary_event_only"]))}

    if kart not in {"confirmed_kart_track", "probable_kart_track"}:
        return "needs_manual_review", None, {"reason_codes": sorted(set(reasons + ["insufficient_evidence", "manual_review_required"]))}

    if outdoor == "confirmed_outdoor" and has_official and len(source_types) >= 2:
        status = "confirmed_outdoor_kart_track"
        reasons.extend(["outdoor_explicitly_stated", "karting_explicitly_stated"])
        conf = 0.95
    elif outdoor in {"confirmed_outdoor", "probable_outdoor", "unclear"}:
        status = "probable_outdoor_kart_track"
        reasons.append("manual_review_required")
        conf = 0.72
    else:
        return "needs_manual_review", None, {"reason_codes": sorted(set(reasons + ["manual_review_required"]))}

    best = sorted(candidates, key=lambda c: (c.source_confidence_tier, c.website is not None))[0]
    geo = derive_geometry(candidates)
    reasons.extend(geo.reason_codes)

    entity = VenueEntity(
        venue_id=deterministic_id("venue", best.venue_name_normalized, best.country, best.locality or ""),
        canonical_name=best.venue_name_raw,
        aliases=sorted({c.venue_name_raw for c in candidates if c.venue_name_raw != best.venue_name_raw}),
        country=best.country,
        subdivision=best.subdivision,
        locality=best.locality,
        postal_code=best.postal_code,
        full_address=best.address_raw,
        outdoor_status=outdoor,
        mixed_mode_flag=any(c.mixed_mode_flag for c in candidates),
        karting_status=kart,
        existing_status=existing,
        recurring_venue_status=recurring,
        official_website=best.website,
        contact_phone=best.phone,
        contact_email=best.email,
        lat=geo.lat,
        lon=geo.lon,
        point_geom=geo.point_geom,
        bbox_geom=geo.bbox_geom,
        initial_working_bbox=geo.initial_working_bbox,
        osm_refs=sorted({f"{c.osm_type}/{c.osm_id}" for c in candidates if c.osm_id}),
        source_geometry_refs=geo.refs,
        acceptance_confidence_score=conf,
        acceptance_reason_codes=sorted(set(reasons)),
        primary_evidence_summary=f"{len(candidates)} candidates from {', '.join(source_types)}",
        source_count=len(candidates),
        source_types_present=source_types,
        first_seen_at=now,
        last_checked_at=now,
        created_by_pipeline_version=pipeline_version,
        parser_versions=sorted({"1.0"}),
        review_status="accepted" if status.startswith("confirmed") else "review_needed",
        review_notes=None,
        evidence_ids=sorted({eid for c in candidates for eid in c.evidence_ids}),
    )
    return status, entity, {"reason_codes": sorted(set(reasons))}
