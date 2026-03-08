from __future__ import annotations

import numpy as np

from trackreco_platform.config import settings
from trackreco_platform.extraction import ExtractionOrchestrator, load_extraction_config
from trackreco_platform.extraction.orchestrator import RunRequest


class ExtractionService:
    def __init__(self):
        self.config = load_extraction_config("config/extraction_pipeline.json")

    def run(self, payload: dict) -> dict:
        image = np.load(payload["image_npy_path"])
        orchestrator = ExtractionOrchestrator(self.config, settings.artifact_local_root)
        request = RunRequest(
            venue_slug=payload["venue_slug"],
            imagery_version=int(payload["imagery_version"]),
            crop_version=int(payload["crop_version"]),
            run_id=payload["run_id"],
            pixel_size_m=float(payload.get("pixel_size_m", 0.25)),
        )
        return orchestrator.run(request, image)
