from __future__ import annotations

from typing import Iterable

from trackreco.adapters.base import SourceAdapter
from trackreco.models import SourceEvidence, deterministic_id, utc_now_iso


class OfficialSourceAdapter(SourceAdapter):
    def __init__(self, source_type: str, confidence_tier: int, records: list[dict], parser_version: str = "1.0"):
        self.source_type = source_type
        self.confidence_tier = confidence_tier
        self.records = records
        self.parser_version = parser_version

    def fetch(self) -> Iterable[SourceEvidence]:
        fetched_at = utc_now_iso()
        for record in self.records:
            url = record.get("source_url", "")
            record_id = record.get("source_record_id")
            snippet = record.get("snippet", "")
            evidence_id = deterministic_id(
                "ev",
                self.source_type,
                url,
                record_id or "",
                snippet,
            )
            yield SourceEvidence(
                evidence_id=evidence_id,
                source_type=self.source_type,
                source_url=url,
                fetched_at=fetched_at,
                parser_version=self.parser_version,
                source_confidence_tier=self.confidence_tier,
                source_record_id=record_id,
                raw_snippet=snippet,
                payload=record,
            )
