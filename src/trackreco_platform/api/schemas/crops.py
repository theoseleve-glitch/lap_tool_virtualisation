from pydantic import BaseModel


class CropCreateRequest(BaseModel):
    venue_id: str
    imagery_asset_id: str
    bbox_wkt: str
    boundary_wkt: str
    area_ha: float


class CropResponse(BaseModel):
    id: str
    venue_id: str
    version: int
    status: str
