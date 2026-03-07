from __future__ import annotations

import re
import unicodedata

from trackreco.models import CandidateRecord, SourceEvidence, deterministic_id


OUTDOOR_KEYWORDS = ("outdoor", "extérieur", "exterieur", "plein air")
INDOOR_KEYWORDS = ("indoor", "intérieur", "interieur")
KART_KEYWORDS = ("kart", "karting", "go-kart")
CLOSED_KEYWORDS = ("closed", "fermé", "ferme", "permanently closed")
TEMP_KEYWORDS = ("temporary", "event-only", "occasional")


def normalize_name(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    n = re.sub(r"[^a-zA-Z0-9 ]+", " ", n.lower())
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _status_from_text(text: str, tags: dict) -> tuple[str, str, str, str, bool]:
    t = text.lower()
    tag_blob = " ".join(f"{k}={v}" for k, v in tags.items()).lower()
    blob = f"{t} {tag_blob}"

    outdoor = "unclear"
    if any(k in blob for k in OUTDOOR_KEYWORDS):
        outdoor = "confirmed_outdoor"
    elif any(k in blob for k in INDOOR_KEYWORDS):
        outdoor = "probable_indoor"
    if tags.get("indoor") == "yes":
        outdoor = "confirmed_indoor"
    if tags.get("outdoor") == "yes":
        outdoor = "confirmed_outdoor"

    kart = "unclear"
    if any(k in blob for k in KART_KEYWORDS) or tags.get("sport") == "karting":
        kart = "confirmed_kart_track"

    operating = "unclear"
    if any(k in blob for k in CLOSED_KEYWORDS):
        operating = "probably_closed"
    elif tags.get("disused") == "yes":
        operating = "closed"
    else:
        operating = "probably_active"

    recurring = "unclear"
    if any(k in blob for k in TEMP_KEYWORDS):
        recurring = "temporary_or_event_only"
    elif "permanent" in blob:
        recurring = "permanent"
    else:
        recurring = "probably_permanent"

    mixed = any(k in blob for k in OUTDOOR_KEYWORDS) and any(k in blob for k in INDOOR_KEYWORDS)
    return outdoor, kart, operating, recurring, mixed


def evidence_to_candidate(evidence: SourceEvidence) -> CandidateRecord:
    p = evidence.payload
    name = p.get("venue_name") or p.get("name") or evidence.raw_snippet or "unknown"
    normalized = normalize_name(name)
    tags = p.get("osm_tags") or p.get("tags") or {}
    outdoor, kart, operating, recurring, mixed = _status_from_text(
        " ".join([str(p.get("snippet", "")), str(p.get("description", "")), str(name)]), tags
    )

    country = p.get("country", "")
    subdivision = p.get("subdivision") or p.get("region")
    ni_flag = country.lower() in {"northern ireland", "ni"}

    candidate_id = deterministic_id("cand", normalized, country, evidence.source_type, evidence.source_record_id or "")
    return CandidateRecord(
        candidate_id=candidate_id,
        venue_name_raw=name,
        venue_name_normalized=normalized,
        country=country,
        subdivision=subdivision,
        locality=p.get("locality") or p.get("city"),
        postal_code=p.get("postal_code"),
        address_raw=p.get("address_raw") or p.get("address"),
        source_type=evidence.source_type,
        source_url=evidence.source_url,
        source_record_id=evidence.source_record_id,
        source_confidence_tier=evidence.source_confidence_tier,
        source_evidence_snippet=evidence.raw_snippet,
        website=p.get("website"),
        phone=p.get("phone"),
        email=p.get("email"),
        lat=p.get("lat"),
        lon=p.get("lon"),
        geometry_source=p.get("geometry_source"),
        osm_id=str(p.get("osm_id")) if p.get("osm_id") else None,
        osm_type=p.get("osm_type"),
        osm_tags=tags,
        outdoor_status=outdoor,
        karting_relevance_status=kart,
        operating_status=operating,
        recurring_venue_status=recurring,
        mixed_mode_flag=mixed,
        ni_flag=ni_flag,
        evidence_ids=[evidence.evidence_id],
    )
