from pathlib import Path

from trackreco.config import load_config
from trackreco.pipeline import run_pipeline


def test_pipeline_generates_required_outputs(tmp_path: Path):
    cfg_path = tmp_path / "pipeline.json"
    cfg_path.write_text(
        Path("config/pipeline.json").read_text(encoding="utf-8").replace("outputs", str(tmp_path / "outputs")),
        encoding="utf-8",
    )
    config = load_config(cfg_path)
    out = run_pipeline(config)

    required = [
        "master_tracks.csv",
        "master_tracks.json",
        "candidate_review_queue.csv",
        "source_evidence.jsonl",
        "merge_candidates.csv",
        "rejected_candidates.csv",
        "accepted_points.geojson",
        "run_log.jsonl",
        "run_report.json",
    ]
    for f in required:
        assert (out / f).exists(), f"missing {f}"


def test_rejects_indoor_only_candidate(tmp_path: Path):
    cfg_text = Path("config/pipeline.json").read_text(encoding="utf-8")
    cfg_path = tmp_path / "pipeline.json"
    cfg_path.write_text(cfg_text.replace("outputs", str(tmp_path / "outputs")), encoding="utf-8")
    config = load_config(cfg_path)
    out = run_pipeline(config)
    rejected = (out / "rejected_candidates.csv").read_text(encoding="utf-8")
    assert "indoor_only_evidence" in rejected
