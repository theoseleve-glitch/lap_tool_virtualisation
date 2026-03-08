from pydantic import BaseModel, Field


class LaunchToolRequest(BaseModel):
    output_root: str = Field(min_length=1, description="Folder where run outputs should be written")
    auto_merge_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    suggest_merge_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    uk_include_ni_from_official_flow: bool = True


class LaunchToolResponse(BaseModel):
    output_dir: str
    run_id: str
    counts: dict[str, int]
    pipeline_version: str
