from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trackreco_platform.db import get_db
from trackreco_platform.domain.models import Layout, LayoutVersion
from trackreco_platform.services.permissions import Actor, require_permission

router = APIRouter(prefix="/lap", tags=["lap"])


@router.get("/venues/{venue_id}/layout")
def lap_layout_contract(venue_id: str, version: int | None = None, db: Session = Depends(get_db), _: Actor = require_permission("read")):
    layout = db.query(Layout).filter(Layout.venue_id == venue_id).one_or_none()
    if not layout:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found", "message": "Layout not found"})

    target = None
    if version is not None:
        target = (
            db.query(LayoutVersion)
            .filter(LayoutVersion.layout_id == layout.id, LayoutVersion.version == version)
            .one_or_none()
        )
    elif layout.active_version_id:
        target = db.get(LayoutVersion, layout.active_version_id)

    if not target:
        raise HTTPException(status_code=404, detail={"code": "version_not_found", "message": "Requested version not found"})

    return {
        "contract_version": "2026-01-01",
        "layout_id": layout.id,
        "layout_version_id": target.id,
        "version": target.version,
        "canonical_geometry": {
            "boundary_polygon": target.boundary_polygon,
            "centerline": target.centerline,
            "start_finish": target.start_finish,
            "sectors": target.sectors,
            "corner_graph_ref": target.corner_graph_ref,
        },
    }
