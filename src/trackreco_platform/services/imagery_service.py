import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from trackreco_platform.domain.enums import ImageryStatus, JobStatus, JobType
from trackreco_platform.domain.models import ImageryAsset, ProcessingJob
from trackreco_platform.imagery.fetcher import ImageryFetcher
from trackreco_platform.storage.s3 import S3Storage


class ImageryService:
    def __init__(self, db: Session):
        self.db = db
        self.fetcher = ImageryFetcher()
        self.storage = S3Storage()

    def enqueue_ingestion(self, venue_id: str, source_name: str, source_uri: str, user_id: str) -> ProcessingJob:
        job = ProcessingJob(
            job_type=JobType.IMAGERY_INGESTION,
            status=JobStatus.QUEUED,
            requested_payload={"venue_id": venue_id, "source_name": source_name, "source_uri": source_uri},
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def run_ingestion(self, job_id: str, user_id: str) -> ImageryAsset:
        job = self.db.get(ProcessingJob, job_id)
        job.status = JobStatus.RUNNING
        self.db.commit()
        req = job.requested_payload

        fetched = self.fetcher.fetch(req["source_uri"])
        sha = hashlib.sha256(fetched.payload).hexdigest()

        existing_versions = self.db.scalars(
            select(ImageryAsset.version).where(ImageryAsset.venue_id == req["venue_id"])
        ).all()
        version = max(existing_versions, default=0) + 1

        prefix = f"venues/{req['venue_id']}/imagery/v{version}"
        raw_path = self.storage.put_bytes(f"{prefix}/raw.bin", fetched.payload)
        normalized = self.storage.put_bytes(f"{prefix}/normalized.bin", fetched.payload)
        thumb = self.storage.put_bytes(f"{prefix}/thumb.bin", fetched.payload[:32])

        asset = ImageryAsset(
            venue_id=req["venue_id"],
            version=version,
            source_name=req["source_name"],
            source_metadata=fetched.metadata,
            raw_path=raw_path,
            normalized_path=normalized,
            thumbnail_path=thumb,
            sha256=sha,
            status=ImageryStatus.READY,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(asset)
        job.status = JobStatus.SUCCEEDED
        job.result_payload = {"imagery_asset_id": asset.id, "sha256": sha}
        self.db.commit()
        self.db.refresh(asset)
        return asset
