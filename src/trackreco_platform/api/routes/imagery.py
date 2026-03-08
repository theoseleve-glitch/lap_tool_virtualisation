from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from trackreco_platform.api.schemas.common import JobState
from trackreco_platform.api.schemas.imagery import ImageryIngestRequest
from trackreco_platform.db import get_db
from trackreco_platform.domain.models import ProcessingJob
from trackreco_platform.services.imagery_service import ImageryService

router = APIRouter(prefix="/imagery", tags=["imagery"])


@router.post("/ingest", response_model=JobState)
def trigger_ingestion(payload: ImageryIngestRequest, db: Session = Depends(get_db)):
    job = ImageryService(db).enqueue_ingestion(payload.venue_id, payload.source_name, payload.source_uri, user_id="system")
    return JobState(
        job_id=job.id,
        status=job.status.value,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/jobs/{job_id}", response_model=JobState)
def ingestion_job_detail(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ProcessingJob, job_id)
    return JobState(
        job_id=job.id,
        status=job.status.value,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_code=job.error_code,
        error_message=job.error_message,
    )
