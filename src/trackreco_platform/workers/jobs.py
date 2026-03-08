from trackreco_platform.db import SessionLocal
from trackreco_platform.services.imagery_service import ImageryService
from trackreco_platform.workers.celery_app import celery_app


@celery_app.task(name="imagery.ingest")
def imagery_ingest(job_id: str):
    with SessionLocal() as db:
        ImageryService(db).run_ingestion(job_id=job_id, user_id="worker")


def main() -> None:
    celery_app.worker_main(["worker", "--loglevel=INFO"])
