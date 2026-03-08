from sqlalchemy import select
from sqlalchemy.orm import Session

from trackreco_platform.domain.enums import CropStatus
from trackreco_platform.domain.models import WorkingAreaVersion


class CropRepository:
    def __init__(self, db: Session):
        self.db = db

    def next_version(self, venue_id: str) -> int:
        versions = self.db.scalars(select(WorkingAreaVersion.version).where(WorkingAreaVersion.venue_id == venue_id)).all()
        return max(versions, default=0) + 1

    def create(self, crop: WorkingAreaVersion) -> WorkingAreaVersion:
        self.db.add(crop)
        self.db.commit()
        self.db.refresh(crop)
        return crop

    def list_by_venue(self, venue_id: str) -> list[WorkingAreaVersion]:
        return list(self.db.scalars(select(WorkingAreaVersion).where(WorkingAreaVersion.venue_id == venue_id).order_by(WorkingAreaVersion.version.desc())).all())

    def activate(self, crop_id: str, user_id: str) -> WorkingAreaVersion:
        crop = self.db.get(WorkingAreaVersion, crop_id)
        if not crop:
            raise ValueError("crop_not_found")
        current_active = self.db.scalars(
            select(WorkingAreaVersion).where(
                WorkingAreaVersion.venue_id == crop.venue_id,
                WorkingAreaVersion.status == CropStatus.ACTIVE,
            )
        ).first()
        if current_active and current_active.id != crop.id:
            current_active.status = CropStatus.RETIRED
            current_active.retired_reason = f"replaced_by:{crop.id}"
            current_active.updated_by = user_id

        crop.status = CropStatus.ACTIVE
        crop.updated_by = user_id
        self.db.commit()
        self.db.refresh(crop)
        return crop
