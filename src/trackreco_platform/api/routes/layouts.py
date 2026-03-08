import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from trackreco_platform.api.schemas.layout_extraction import ExtractionRequest
from trackreco_platform.api.schemas.review import GeometryEditRequest, PublishRequest, ReviewActionRequest
from trackreco_platform.config import settings
from trackreco_platform.db import get_db
from trackreco_platform.domain.enums import LayoutStatus, ReviewActionType, ReviewStatus
from trackreco_platform.domain.models import Layout, LayoutVersion, PublishHistory, ReviewAction, ValidationReport
from trackreco_platform.observability import current_correlation_id
from trackreco_platform.services.permissions import Actor, require_permission
from trackreco_platform.services.review_workflow import (
    WorkflowError,
    apply_review_action,
    publish_history_for_layout,
    publish_layout_version,
    unpublish_layout,
)
from trackreco_platform.workers.celery_app import celery_app

router = APIRouter(prefix="/layouts", tags=["layouts"])


@router.get("")
def list_layouts(db: Session = Depends(get_db), _: Actor = require_permission("read")):
    stmt = select(LayoutVersion).order_by(LayoutVersion.created_at.desc())
    versions = db.scalars(stmt).all()
    return [
        {
            "id": v.id,
            "layout_id": v.layout_id,
            "version": v.version,
            "status": v.status.value,
            "review_status": v.review_status.value,
        }
        for v in versions
    ]


@router.get("/{layout_version_id}")
def layout_detail(layout_version_id: str, db: Session = Depends(get_db), _: Actor = require_permission("read")):
    v = db.get(LayoutVersion, layout_version_id)
    if not v:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout version not found"})
    return {
        "id": v.id,
        "layout_id": v.layout_id,
        "version": v.version,
        "status": v.status.value,
        "review_status": v.review_status.value,
        "immutable_hash": v.immutable_hash,
        "corner_graph_ref": v.corner_graph_ref,
    }


@router.get("/{layout_version_id}/validation")
def validation_reports(layout_version_id: str, db: Session = Depends(get_db), _: Actor = require_permission("read")):
    reports = db.scalars(select(ValidationReport).where(ValidationReport.layout_version_id == layout_version_id)).all()
    return [{"id": r.id, "passed": r.passed, "findings": r.findings, "validator_version": r.validator_version} for r in reports]


@router.post("/{layout_version_id}/review")
def review_action(
    layout_version_id: str,
    req: ReviewActionRequest,
    db: Session = Depends(get_db),
    actor: Actor = require_permission("review"),
):
    version = db.get(LayoutVersion, layout_version_id)
    if not version:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout version not found"})
    try:
        apply_review_action(
            db,
            layout_version=version,
            action=req.action,
            notes=req.notes,
            actor=actor,
            correlation_id=current_correlation_id(),
        )
        db.commit()
    except WorkflowError as exc:
        raise HTTPException(status_code=409, detail={"code": "invalid_transition", "message": str(exc)}) from exc
    return {"layout_version_id": version.id, "review_status": version.review_status.value}


@router.post("/{layout_version_id}/publish")
def publish(
    layout_version_id: str,
    req: PublishRequest,
    db: Session = Depends(get_db),
    actor: Actor = require_permission("publish"),
):
    version = db.get(LayoutVersion, layout_version_id)
    if not version:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout version not found"})
    layout = db.get(Layout, version.layout_id)
    if not layout:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout not found"})
    try:
        history = publish_layout_version(
            db,
            layout=layout,
            target_version=version,
            actor=actor,
            reason=req.reason,
            correlation_id=current_correlation_id(),
        )
        db.commit()
    except WorkflowError as exc:
        raise HTTPException(status_code=409, detail={"code": "publish_blocked", "message": str(exc)}) from exc
    return {"layout_version_id": layout_version_id, "action": history.action.value, "active_version_id": layout.active_version_id}


@router.post("/{layout_id}/unpublish")
def unpublish(layout_id: str, req: PublishRequest, db: Session = Depends(get_db), actor: Actor = require_permission("publish")):
    layout = db.get(Layout, layout_id)
    if not layout:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout not found"})
    try:
        history = unpublish_layout(
            db,
            layout=layout,
            actor=actor,
            reason=req.reason,
            correlation_id=current_correlation_id(),
        )
        db.commit()
    except WorkflowError as exc:
        raise HTTPException(status_code=409, detail={"code": "unpublish_blocked", "message": str(exc)}) from exc
    return {"layout_id": layout_id, "action": history.action.value, "active_version_id": layout.active_version_id}


@router.get("/{layout_id}/publish-history")
def publish_history(layout_id: str, db: Session = Depends(get_db), _: Actor = require_permission("read")):
    history = publish_history_for_layout(db, layout_id)
    return [
        {
            "id": h.id,
            "layout_version_id": h.layout_version_id,
            "previous_layout_version_id": h.previous_layout_version_id,
            "action": h.action.value,
            "reason": h.reason,
            "created_at": h.created_at,
            "created_by": h.created_by,
        }
        for h in history
    ]


@router.post("/{layout_version_id}/geometry-edits")
def geometry_edits(
    layout_version_id: str,
    req: GeometryEditRequest,
    db: Session = Depends(get_db),
    actor: Actor = require_permission("edit_layout"),
):
    base = db.get(LayoutVersion, layout_version_id)
    if not base:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout version not found"})

    next_version = db.scalar(
        select(LayoutVersion.version).where(LayoutVersion.layout_id == base.layout_id).order_by(LayoutVersion.version.desc())
    )
    cloned = LayoutVersion(
        layout_id=base.layout_id,
        extraction_run_id=base.extraction_run_id,
        version=(next_version or 0) + 1,
        status=LayoutStatus.DRAFT,
        review_status=ReviewStatus.IN_REVIEW if req.submit_for_review else ReviewStatus.DRAFT,
        boundary_polygon=req.boundary_polygon_wkt,
        centerline=req.centerline_wkt,
        start_finish=req.start_finish_wkt,
        sectors=req.sectors,
        corner_graph_ref=base.corner_graph_ref,
        supersedes_layout_version_id=base.id,
        immutable_hash=f"manual-edit-{base.id}-{(next_version or 0) + 1}",
        created_by=actor.email,
        updated_by=actor.email,
    )
    db.add(cloned)
    db.add(
        ReviewAction(
            layout_version_id=cloned.id,
            action=ReviewActionType.SUBMIT_FOR_REVIEW if req.submit_for_review else ReviewActionType.REQUEST_CHANGES,
            notes=req.audit_note,
            created_by=actor.email,
            updated_by=actor.email,
        )
    )
    db.commit()
    return {"layout_version_id": cloned.id, "version": cloned.version, "review_status": cloned.review_status.value}


@router.post("/extraction-runs")
def submit_extraction(req: ExtractionRequest, _: Actor = require_permission("manage_jobs")):
    job = celery_app.send_task("layout.extract", args=[req.model_dump()])
    return {"job_id": job.id, "run_id": req.run_id, "status": "queued"}


@router.get("/extraction-runs/{run_id}")
def extraction_status(venue_slug: str, imagery_version: int, crop_version: int, run_id: str, _: Actor = require_permission("read")):
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
