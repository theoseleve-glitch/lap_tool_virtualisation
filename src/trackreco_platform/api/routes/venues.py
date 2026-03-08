from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from trackreco_platform.api.schemas.venues import VenueCreate, VenueImportResult, VenueResponse
from trackreco_platform.db import get_db
from trackreco_platform.errors import ValidationError
from trackreco_platform.repositories.venue_repository import VenueRepository
from trackreco_platform.services.venue_service import VenueService

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("", response_model=list[VenueResponse])
def list_venues(db: Session = Depends(get_db)):
    venues = VenueRepository(db).list()
    return [VenueResponse(id=v.id, name=v.name, slug=v.slug, status=v.status.value) for v in venues]


@router.post("", response_model=VenueResponse)
def create_venue(payload: VenueCreate, db: Session = Depends(get_db)):
    try:
        venue = VenueService(db).create_venue(name=payload.name, alias=payload.alias, user_id="system")
    except ValidationError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code, "message": exc.message}) from exc
    return VenueResponse(id=venue.id, name=venue.name, slug=venue.slug, status=venue.status.value)


@router.post("/import", response_model=VenueImportResult)
async def import_venues(file: UploadFile, db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8")
    _, result = VenueService(db).import_csv(content, user_id="system")
    return VenueImportResult(**result)
