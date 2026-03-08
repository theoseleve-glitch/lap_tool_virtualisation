import json

from fastapi import APIRouter

from trackreco.config import PipelineConfig, load_config
from trackreco.pipeline import run_pipeline
from trackreco_platform.api.schemas.tool import LaunchToolRequest, LaunchToolResponse
from trackreco_platform.services.permissions import Actor, require_permission

router = APIRouter(prefix="/tool", tags=["tool"])


@router.post("/launch", response_model=LaunchToolResponse)
def launch_tool(req: LaunchToolRequest, _: Actor = require_permission("manage_jobs")):
    base_config = load_config("config/pipeline.json")
    updated_config = PipelineConfig(
        pipeline_version=base_config.pipeline_version,
        output_root=req.output_root,
        countries=base_config.countries,
        uk_include_ni_from_official_flow=req.uk_include_ni_from_official_flow,
        thresholds={
            "auto_merge_threshold": req.auto_merge_threshold,
            "suggest_merge_threshold": req.suggest_merge_threshold,
        },
        sources=base_config.sources,
    )

    output_dir = run_pipeline(updated_config)
    report = json.loads((output_dir / "run_report.json").read_text(encoding="utf-8"))
    return LaunchToolResponse(
        output_dir=str(output_dir),
        run_id=report["run_id"],
        counts=report["counts"],
        pipeline_version=report["pipeline_version"],
    )
