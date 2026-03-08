import pytest
pytest.importorskip("shapely")

import json
from pathlib import Path

import numpy as np

from trackreco_platform.extraction import ExtractionOrchestrator, load_extraction_config
from trackreco_platform.extraction.orchestrator import RunRequest


def make_ring_image(size: int = 180) -> np.ndarray:
    image = np.ones((size, size, 3), dtype=np.uint8) * 220
    yy, xx = np.indices((size, size))
    center = size // 2
    dist = np.sqrt((yy - center) ** 2 + (xx - center) ** 2)
    ring = (dist < size * 0.38) & (dist > size * 0.25)
    image[ring] = np.array([70, 70, 70], dtype=np.uint8)
    return image


def test_end_to_end_extraction(tmp_path: Path):
    cfg = load_extraction_config("config/extraction_pipeline.json")
    orchestrator = ExtractionOrchestrator(cfg, tmp_path)
    request = RunRequest("lyon-kart", 1, 1, "run-001", 1.0)
    status = orchestrator.run(request, make_ring_image())

    assert status["state"] == "succeeded"
    assert "stages" in status
    run_status = tmp_path / "lyon-kart" / "imagery_v1" / "crop_v1" / "extraction-v1" / "run-001" / "run" / "status.json"
    payload = json.loads(run_status.read_text())
    assert payload["publishable"] in (True, False)


def test_segmentation_failure_persists_reason(tmp_path: Path):
    cfg = load_extraction_config("config/extraction_pipeline.json")
    orchestrator = ExtractionOrchestrator(cfg, tmp_path)
    image = np.ones((80, 80, 3), dtype=np.uint8) * 250
    request = RunRequest("no-track", 1, 1, "run-002", 1.0)
    status = orchestrator.run(request, image)
    assert status["state"] == "failed"
    assert "segmentation_empty" in status["error"]["message"]


def test_golden_artifacts_exist(tmp_path: Path):
    cfg = load_extraction_config("config/extraction_pipeline.json")
    orchestrator = ExtractionOrchestrator(cfg, tmp_path)
    status = orchestrator.run(RunRequest("marseille", 2, 1, "run-003", 1.0), make_ring_image(200))
    assert status["state"] == "succeeded"
    base = tmp_path / "marseille" / "imagery_v2" / "crop_v1" / "extraction-v1" / "run-003"
    expected = [
        base / "segmentation" / "final_mask.npy",
        base / "boundary" / "cleaned_boundary.geojson",
        base / "centerline" / "centerline.geojson",
        base / "validation" / "validation_report.json",
        base / "validation" / "validation_report.txt",
    ]
    assert all(p.exists() for p in expected)
