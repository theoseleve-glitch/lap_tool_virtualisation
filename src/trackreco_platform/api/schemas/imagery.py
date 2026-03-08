from pydantic import BaseModel


class ImageryIngestRequest(BaseModel):
    venue_id: str
    source_name: str
    source_uri: str


class ImageryResponse(BaseModel):
    id: str
    venue_id: str
    version: int
    status: str
    raw_path: str
    normalized_path: str
    thumbnail_path: str | None = None
