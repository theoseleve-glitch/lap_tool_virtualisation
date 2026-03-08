import csv
from collections import Counter
from io import StringIO

from slugify import slugify
from sqlalchemy.orm import Session

from trackreco_platform.domain.models import ProcessingJob, Venue
from trackreco_platform.domain.enums import JobStatus, JobType
from trackreco_platform.errors import ValidationError
from trackreco_platform.repositories.venue_repository import VenueRepository


class VenueService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VenueRepository(db)

    def create_venue(self, name: str, alias: str | None, user_id: str) -> Venue:
        slug = slugify(name)
        if self.repo.get_by_slug(slug):
            raise ValidationError(code="duplicate_slug", message="Venue slug already exists")
        venue = Venue(name=name, slug=slug, created_by=user_id, updated_by=user_id)
        return self.repo.create(venue, alias=alias)

    def import_csv(self, csv_text: str, user_id: str) -> tuple[ProcessingJob, dict]:
        job = ProcessingJob(job_type=JobType.VENUE_IMPORT, status=JobStatus.RUNNING, created_by=user_id, updated_by=user_id)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        reader = csv.DictReader(StringIO(csv_text))
        rows = list(reader)
        names = [r.get("name", "").strip() for r in rows]
        seen_counts = Counter(n for n in names if n)
        rejection_reasons = []
        accepted = 0
        for idx, row in enumerate(rows, start=2):
            name = row.get("name", "").strip()
            alias = row.get("alias", "").strip() or None
            if not name:
                rejection_reasons.append({"line": idx, "code": "missing_name"})
                continue
            if seen_counts[name] > 1:
                rejection_reasons.append({"line": idx, "code": "duplicate_in_file", "name": name})
                continue
            slug = slugify(name)
            if self.repo.get_by_slug(slug):
                rejection_reasons.append({"line": idx, "code": "slug_exists", "slug": slug})
                continue
            venue = Venue(name=name, slug=slug, created_by=user_id, updated_by=user_id)
            self.db.add(venue)
            self.db.flush()
            if alias:
                from trackreco_platform.domain.models import VenueAlias

                self.db.add(VenueAlias(venue_id=venue.id, alias=alias, created_by=user_id, updated_by=user_id))
            accepted += 1

        job.status = JobStatus.SUCCEEDED
        job.result_payload = {
            "accepted": accepted,
            "rejected": len(rejection_reasons),
            "rejection_reasons": rejection_reasons,
        }
        self.db.commit()
        self.db.refresh(job)
        return job, job.result_payload
