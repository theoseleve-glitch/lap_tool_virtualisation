from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from shapely.geometry import mapping


@dataclass(frozen=True)
class ArtifactContext:
    venue_slug: str
    imagery_version: int
    crop_version: int
    pipeline_version: str
    run_id: str


class ArtifactStore:
    def __init__(self, root: str | Path, ctx: ArtifactContext):
        self.root = Path(root)
        self.ctx = ctx
        self.base_dir = (
            self.root
            / ctx.venue_slug
            / f"imagery_v{ctx.imagery_version}"
            / f"crop_v{ctx.crop_version}"
            / ctx.pipeline_version
            / ctx.run_id
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def stage_dir(self, stage: str) -> Path:
        target = self.base_dir / stage
        target.mkdir(parents=True, exist_ok=True)
        return target

    def write_json(self, stage: str, name: str, payload: dict[str, Any]) -> str:
        target = self.stage_dir(stage) / f"{name}.json"
        target.write_text(json.dumps(payload, indent=2, sort_keys=True))
        return str(target)

    def write_mask(self, stage: str, name: str, mask: np.ndarray) -> str:
        target = self.stage_dir(stage) / f"{name}.npy"
        np.save(target, mask.astype(np.uint8))
        return str(target)

    def write_geometry(self, stage: str, name: str, geometry: Any) -> str:
        target = self.stage_dir(stage) / f"{name}.geojson"
        target.write_text(json.dumps({"type": "Feature", "geometry": mapping(geometry), "properties": {}}))
        return str(target)

    def write_text(self, stage: str, name: str, content: str) -> str:
        target = self.stage_dir(stage) / f"{name}.txt"
        target.write_text(content)
        return str(target)

    def write_stage_manifest(self, stage: str, artifacts: dict[str, str], metrics: dict[str, Any]) -> str:
        payload = {
            "stage": stage,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "artifacts": artifacts,
            "metrics": metrics,
            "checksum": hashlib.sha256(json.dumps(metrics, sort_keys=True).encode()).hexdigest(),
        }
        return self.write_json(stage, "manifest", payload)
