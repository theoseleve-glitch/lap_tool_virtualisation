from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class SourceEvidence:
    evidence_id: str
    source_type: str
    source_url: str
    fetched_at: str
    parser_version: str
    source_confidence_tier: int
    source_record_id: str | None
    raw_snippet: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CandidateRecord:
    candidate_id: str
    venue_name_raw: str
    venue_name_normalized: str
    country: str
    subdivision: str | None
    locality: str | None
    postal_code: str | None
    address_raw: str | None
    source_type: str
    source_url: str
    source_record_id: str | None
    source_confidence_tier: int
    source_evidence_snippet: str
    website: str | None
    phone: str | None
    email: str | None
    lat: float | None
    lon: float | None
    geometry_source: str | None
    osm_id: str | None
    osm_type: str | None
    osm_tags: dict[str, Any]
    outdoor_status: str
    karting_relevance_status: str
    operating_status: str
    recurring_venue_status: str
    mixed_mode_flag: bool = False
    ni_flag: bool = False
    evidence_ids: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VenueEntity:
    venue_id: str
    canonical_name: str
    aliases: list[str]
    country: str
    subdivision: str | None
    locality: str | None
    postal_code: str | None
    full_address: str | None
    outdoor_status: str
    mixed_mode_flag: bool
    karting_status: str
    existing_status: str
    recurring_venue_status: str
    official_website: str | None
    contact_phone: str | None
    contact_email: str | None
    lat: float | None
    lon: float | None
    point_geom: str | None
    bbox_geom: str | None
    initial_working_bbox: str | None
    osm_refs: list[str]
    source_geometry_refs: list[str]
    acceptance_confidence_score: float
    acceptance_reason_codes: list[str]
    primary_evidence_summary: str
    source_count: int
    source_types_present: list[str]
    first_seen_at: str
    last_checked_at: str
    created_by_pipeline_version: str
    parser_versions: list[str]
    review_status: str
    review_notes: str | None
    evidence_ids: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def deterministic_id(prefix: str, *parts: str) -> str:
    blob = "|".join(p.strip().lower() for p in parts if p)
    digest = hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
