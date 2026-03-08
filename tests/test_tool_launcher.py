import json
from pathlib import Path

from trackreco_platform.api.routes.tool import launch_tool
from trackreco_platform.api.schemas.tool import LaunchToolRequest


def test_launch_tool_creates_run_and_report(tmp_path: Path):
    req = LaunchToolRequest(
        output_root=str(tmp_path / "runs"),
        auto_merge_threshold=0.9,
        suggest_merge_threshold=0.55,
        uk_include_ni_from_official_flow=False,
    )

    resp = launch_tool(req)

    out_dir = Path(resp.output_dir)
    assert out_dir.exists()
    assert out_dir.parent == tmp_path / "runs"
    report = json.loads((out_dir / "run_report.json").read_text())
    assert report["run_id"] == resp.run_id
    assert report["counts"]["evidence"] >= 1
