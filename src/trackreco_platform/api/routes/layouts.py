import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from trackreco_platform.api.schemas.layout_extraction import ExtractionRequest
from trackreco_platform.config import settings
from trackreco_platform.db import get_db
from trackreco_platform.domain.enums import LayoutStatus, PublishAction
from trackreco_platform.domain.models import LayoutVersion, PublishHistory, ReviewAction, ValidationReport
from trackreco_platform.workers.celery_app import celery_app

router = APIRouter(prefix="/layouts", tags=["layouts"])


@router.get("")
def list_layouts(db: Session = Depends(get_db)):
    stmt = select(LayoutVersion).order_by(LayoutVersion.created_at.desc())
    versions = db.scalars(stmt).all()
    return [{"id": v.id, "layout_id": v.layout_id, "version": v.version, "status": v.status.value} for v in versions]


@router.get("/{layout_version_id}")
def layout_detail(layout_version_id: str, db: Session = Depends(get_db)):
    v = db.get(LayoutVersion, layout_version_id)
    if not v:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout version not found"})
    return {
        "id": v.id,
        "layout_id": v.layout_id,
        "version": v.version,
        "status": v.status.value,
        "immutable_hash": v.immutable_hash,
        "corner_graph_ref": v.corner_graph_ref,
    }


@router.get("/{layout_version_id}/validation")
def validation_reports(layout_version_id: str, db: Session = Depends(get_db)):
    reports = db.scalars(select(ValidationReport).where(ValidationReport.layout_version_id == layout_version_id)).all()
    return [{"id": r.id, "passed": r.passed, "findings": r.findings, "validator_version": r.validator_version} for r in reports]


@router.post("/{layout_version_id}/review")
def review_action(layout_version_id: str, action: str, notes: str | None = None, db: Session = Depends(get_db)):
    record = ReviewAction(layout_version_id=layout_version_id, action=action, notes=notes, created_by="system", updated_by="system")
    db.add(record)
    db.commit()
    return {"id": record.id, "layout_version_id": layout_version_id, "action": action}


@router.post("/{layout_version_id}/publish")
def publish(layout_version_id: str, reason: str | None = None, db: Session = Depends(get_db)):
    version = db.get(LayoutVersion, layout_version_id)
    if not version:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout version not found"})
    if version.status == LayoutStatus.PUBLISHED:
        raise HTTPException(status_code=409, detail={"code": "already_published", "message": "Already published"})
    version.status = LayoutStatus.PUBLISHED
    history = PublishHistory(layout_version_id=layout_version_id, action=PublishAction.PUBLISH, reason=reason, created_by="system", updated_by="system")
    db.add(history)
    db.commit()
    return {"layout_version_id": layout_version_id, "status": version.status.value}


@router.post("/{layout_version_id}/unpublish")
def unpublish(layout_version_id: str, reason: str | None = None, db: Session = Depends(get_db)):
    version = db.get(LayoutVersion, layout_version_id)
    if not version:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout version not found"})
    version.status = LayoutStatus.UNPUBLISHED
    history = PublishHistory(layout_version_id=layout_version_id, action=PublishAction.UNPUBLISH, reason=reason, created_by="system", updated_by="system")
    db.add(history)
    db.commit()
    return {"layout_version_id": layout_version_id, "status": version.status.value}


@router.post("/extraction-runs")
def submit_extraction(req: ExtractionRequest):
    job = celery_app.send_task("layout.extract", args=[req.model_dump()])
    return {"job_id": job.id, "run_id": req.run_id, "status": "queued"}


@router.get("/extraction-runs/{run_id}")
def extraction_status(venue_slug: str, imagery_version: int, crop_version: int, run_id: str):
    status_path = (
        Path(settings.artifact_local_root)
        / venue_slug
        / f"imagery_v{imagery_version}"
        / f"crop_v{crop_version}"
        / "extraction-v1"
        / run_id
        / "run"
        / "status.json"
    )
    if not status_path.exists():
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": "Extraction run status not found"})
    return json.loads(status_path.read_text())
