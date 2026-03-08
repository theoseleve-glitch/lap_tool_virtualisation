from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass(frozen=True)
class SegmentationConfig:
    mode: str = "heuristic"
    grayscale_threshold: int = 135
    saturation_threshold: int = 80
    min_component_pixels: int = 400
    closing_iterations: int = 2
    opening_iterations: int = 1
    ml_model_ref: str | None = None


@dataclass(frozen=True)
class BoundaryConfig:
    min_area_m2: float = 300.0
    simplify_tolerance_m: float = 0.8
    hole_area_threshold_m2: float = 30.0
    repair_buffer_m: float = 0.2


@dataclass(frozen=True)
class CenterlineConfig:
    prune_min_branch_length_m: float = 6.0
    simplify_tolerance_m: float = 0.6
    smooth_iterations: int = 4
    closure_tolerance_m: float = 2.0


@dataclass(frozen=True)
class AlternateLayoutConfig:
    min_alt_score: float = 0.65
    min_alt_length_ratio: float = 0.2
    max_auto_splits: int = 1


@dataclass(frozen=True)
class ValidationConfig:
    min_track_length_m: float = 250.0
    max_track_length_m: float = 3500.0
    min_mean_width_m: float = 4.0
    max_mean_width_m: float = 15.0
    max_centerline_outside_ratio: float = 0.002


@dataclass(frozen=True)
class PipelineVersion:
    pipeline: str = "extraction-v1"
    segmentation: str = "heuristic-v1"
    boundary: str = "boundary-v1"
    centerline: str = "centerline-v1"
    alternate_layout: str = "alternate-v1"
    intelligence: str = "intel-v1"
    validation: str = "validation-v1"


@dataclass(frozen=True)
class ExtractionConfig:
    segmentation: SegmentationConfig = field(default_factory=SegmentationConfig)
    boundary: BoundaryConfig = field(default_factory=BoundaryConfig)
    centerline: CenterlineConfig = field(default_factory=CenterlineConfig)
    alternate_layout: AlternateLayoutConfig = field(default_factory=AlternateLayoutConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    versions: PipelineVersion = field(default_factory=PipelineVersion)


def load_extraction_config(path: str | Path) -> ExtractionConfig:
    payload = json.loads(Path(path).read_text())

    def _build(dc, key):
        raw = payload.get(key, {})
        return dc(**raw)

    return ExtractionConfig(
        segmentation=_build(SegmentationConfig, "segmentation"),
        boundary=_build(BoundaryConfig, "boundary"),
        centerline=_build(CenterlineConfig, "centerline"),
        alternate_layout=_build(AlternateLayoutConfig, "alternate_layout"),
        validation=_build(ValidationConfig, "validation"),
        versions=_build(PipelineVersion, "versions"),
    )
