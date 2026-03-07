from __future__ import annotations

from typing import Iterable

from trackreco.adapters.base import SourceAdapter
from trackreco.models import SourceEvidence, deterministic_id, utc_now_iso


class OSMAdapter(SourceAdapter):
    def __init__(self, records: list[dict], parser_version: str = "1.0"):
        self.source_type = "osm_overpass"
        self.confidence_tier = 2
        self.records = records
        self.parser_version = parser_version

    def fetch(self) -> Iterable[SourceEvidence]:
        fetched_at = utc_now_iso()
        for record in self.records:
            osm_id = str(record.get("osm_id", ""))
            osm_type = record.get("osm_type", "")
            snippet = record.get("name", "")
            evidence_id = deterministic_id("ev", self.source_type, osm_type, osm_id)
            yield SourceEvidence(
                evidence_id=evidence_id,
                source_type=self.source_type,
                source_url=record.get("source_url", "https://overpass-api.de"),
                fetched_at=fetched_at,
                parser_version=self.parser_version,
                source_confidence_tier=self.confidence_tier,
                source_record_id=f"{osm_type}/{osm_id}",
                raw_snippet=snippet,
                payload=record,
            )
