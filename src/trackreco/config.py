from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(slots=True)
class PipelineConfig:
    pipeline_version: str
    output_root: str
    countries: list[str]
    uk_include_ni_from_official_flow: bool
    thresholds: dict[str, float]
    sources: dict[str, Any]


def load_config(path: str | Path) -> PipelineConfig:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return PipelineConfig(
        pipeline_version=raw["pipeline_version"],
        output_root=raw["output_root"],
        countries=raw["countries"],
        uk_include_ni_from_official_flow=raw["uk_include_ni_from_official_flow"],
        thresholds=raw["thresholds"],
        sources=raw["sources"],
    )
