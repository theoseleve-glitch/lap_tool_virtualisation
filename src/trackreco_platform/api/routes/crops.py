from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trackreco_platform.api.schemas.crops import CropCreateRequest, CropResponse
from trackreco_platform.db import get_db
from trackreco_platform.errors import ValidationError
from trackreco_platform.repositories.crop_repository import CropRepository
from trackreco_platform.services.crop_service import CropService

router = APIRouter(prefix="/crops", tags=["crops"])


@router.post("", response_model=CropResponse)
def create_crop(payload: CropCreateRequest, db: Session = Depends(get_db)):
    try:
        crop = CropService(db).create_crop(
            venue_id=payload.venue_id,
            imagery_asset_id=payload.imagery_asset_id,
            bbox_wkt=payload.bbox_wkt,
            boundary_wkt=payload.boundary_wkt,
            area_ha=payload.area_ha,
            user_id="system",
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc
    return CropResponse(id=crop.id, venue_id=crop.venue_id, version=crop.version, status=crop.status.value)


@router.post("/{crop_id}/activate", response_model=CropResponse)
def activate_crop(crop_id: str, db: Session = Depends(get_db)):
    try:
        crop = CropService(db).activate_crop(crop_id, user_id="system")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"code": str(exc), "message": "Crop not found"}) from exc
    return CropResponse(id=crop.id, venue_id=crop.venue_id, version=crop.version, status=crop.status.value)


@router.get("/venue/{venue_id}", response_model=list[CropResponse])
def list_crops(venue_id: str, db: Session = Depends(get_db)):
    crops = CropRepository(db).list_by_venue(venue_id)
    return [CropResponse(id=c.id, venue_id=c.venue_id, version=c.version, status=c.status.value) for c in crops]
