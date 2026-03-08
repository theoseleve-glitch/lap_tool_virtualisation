from pydantic import BaseModel, Field


class VenueCreate(BaseModel):
    name: str
    alias: str | None = None


class VenueResponse(BaseModel):
    id: str
    name: str
    slug: str
    status: str


class VenueImportResult(BaseModel):
    accepted: int
    rejected: int
    rejection_reasons: list[dict] = Field(default_factory=list)
