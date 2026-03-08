from sqlalchemy import select
from sqlalchemy.orm import Session

from trackreco_platform.domain.models import Venue, VenueAlias


class VenueRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Venue]:
        return list(self.db.scalars(select(Venue).order_by(Venue.name)).all())

    def get(self, venue_id: str) -> Venue | None:
        return self.db.get(Venue, venue_id)

    def get_by_slug(self, slug: str) -> Venue | None:
        return self.db.scalars(select(Venue).where(Venue.slug == slug)).first()

    def create(self, venue: Venue, alias: str | None = None) -> Venue:
        self.db.add(venue)
        self.db.flush()
        if alias:
            self.db.add(VenueAlias(venue_id=venue.id, alias=alias))
        self.db.commit()
        self.db.refresh(venue)
        return venue
