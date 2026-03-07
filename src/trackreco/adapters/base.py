from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from trackreco.models import SourceEvidence


class SourceAdapter(ABC):
    source_type: str
    parser_version: str = "1.0"
    confidence_tier: int

    @abstractmethod
    def fetch(self) -> Iterable[SourceEvidence]:
        raise NotImplementedError
