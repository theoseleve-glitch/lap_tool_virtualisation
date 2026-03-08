from pydantic import BaseModel, Field

from trackreco_platform.domain.enums import ReviewActionType


class ReviewActionRequest(BaseModel):
    action: ReviewActionType
    notes: str | None = Field(default=None, max_length=4000)


class PublishRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=4000)


class GeometryEditRequest(BaseModel):
    boundary_polygon_wkt: str
    centerline_wkt: str
    start_finish_wkt: str
    sectors: dict = Field(default_factory=dict)
    audit_note: str = Field(min_length=3, max_length=4000)
    submit_for_review: bool = False
