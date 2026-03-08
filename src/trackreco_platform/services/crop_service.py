from shapely import wkt
from sqlalchemy.orm import Session

from trackreco_platform.domain.enums import CropStatus
from trackreco_platform.domain.models import WorkingAreaVersion
from trackreco_platform.errors import ValidationError
from trackreco_platform.repositories.crop_repository import CropRepository


class CropService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CropRepository(db)

    def create_crop(
        self,
        venue_id: str,
        imagery_asset_id: str,
        bbox_wkt: str,
        boundary_wkt: str,
        area_ha: float,
        user_id: str,
    ) -> WorkingAreaVersion:
        bbox = wkt.loads(bbox_wkt)
        boundary = wkt.loads(boundary_wkt)
        if not bbox.is_valid or not boundary.is_valid:
            raise ValidationError(code="invalid_geometry", message="bbox or boundary invalid")
        if not bbox.contains(boundary):
            raise ValidationError(code="boundary_outside_bbox", message="boundary must be within bbox")
        if area_ha <= 0 or area_ha > 1000:
            raise ValidationError(code="invalid_area", message="area_ha must be within (0,1000]")

        version = self.repo.next_version(venue_id)
        crop = WorkingAreaVersion(
            venue_id=venue_id,
            imagery_asset_id=imagery_asset_id,
            version=version,
            bbox=bbox_wkt,
            boundary_polygon=boundary_wkt,
            area_ha=area_ha,
            status=CropStatus.DRAFT,
            created_by=user_id,
            updated_by=user_id,
        )
        return self.repo.create(crop)

    def activate_crop(self, crop_id: str, user_id: str) -> WorkingAreaVersion:
        return self.repo.activate(crop_id, user_id)
