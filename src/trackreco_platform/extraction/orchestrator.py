from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import traceback

import numpy as np

from .alternate_layouts import AlternateLayoutAnalyzer
from .artifacts import ArtifactContext, ArtifactStore
from .boundary import BoundaryExtractor
from .config import ExtractionConfig
from .intelligence import GeometryIntelligenceBuilder
from .segmentation import Segmenter, reason_message
from .validation import ValidationEngine
from .centerline import CenterlineExtractor


@dataclass
class RunRequest:
    venue_slug: str
    imagery_version: int
    crop_version: int
    run_id: str
    pixel_size_m: float


class ExtractionOrchestrator:
    def __init__(self, config: ExtractionConfig, artifact_root: str | Path):
        self.config = config
        self.artifact_root = artifact_root

    def run(self, request: RunRequest, image: np.ndarray) -> dict:
        ctx = ArtifactContext(
            venue_slug=request.venue_slug,
            imagery_version=request.imagery_version,
            crop_version=request.crop_version,
            pipeline_version=self.config.versions.pipeline,
            run_id=request.run_id,
        )
        store = ArtifactStore(self.artifact_root, ctx)
        status = {"run_id": request.run_id, "stages": [], "state": "running", "started_at": datetime.now(timezone.utc).isoformat()}
        try:
            seg = Segmenter(self.config.segmentation).run(image)
            seg_artifacts = {"normalized": store.write_mask("segmentation", "normalized", seg.normalized[:, :, 0])}
            for k, m in seg.candidate_masks.items():
                seg_artifacts[f"candidate_{k}"] = store.write_mask("segmentation", f"candidate_{k}", m)
            for k, m in seg.cleaned_masks.items():
                seg_artifacts[f"cleaned_{k}"] = store.write_mask("segmentation", f"cleaned_{k}", m)
            seg_artifacts["final"] = store.write_mask("segmentation", "final_mask", seg.final_mask)
            seg_artifacts["manifest"] = store.write_stage_manifest("segmentation", seg_artifacts, seg.metrics)
            status["stages"].append({"stage": "segmentation", "success": seg.success, "reason": reason_message(seg.reason_code), "confidence": seg.confidence})
            if not seg.success:
                raise RuntimeError(seg.reason_code or "segmentation_failure")

            boundary = BoundaryExtractor(self.config.boundary).run(seg.final_mask, request.pixel_size_m)
            b_artifacts = {}
            if boundary.raw_polygon is not None:
                b_artifacts["raw"] = store.write_geometry("boundary", "raw_boundary", boundary.raw_polygon)
            if boundary.cleaned_polygon is not None:
                b_artifacts["cleaned"] = store.write_geometry("boundary", "cleaned_boundary", boundary.cleaned_polygon)
            b_artifacts["manifest"] = store.write_stage_manifest("boundary", b_artifacts, boundary.metrics)
            status["stages"].append({"stage": "boundary", "success": boundary.success, "reason": boundary.reason_code, "confidence": boundary.confidence})
            if boundary.cleaned_polygon is None:
                raise RuntimeError(boundary.reason_code or "boundary_failure")

            center = CenterlineExtractor(self.config.centerline).run(seg.final_mask, boundary.cleaned_polygon, request.pixel_size_m)
            c_artifacts = {
                "raw_skeleton": store.write_mask("centerline", "raw_skeleton", center.raw_skeleton),
            }
            if center.centerline is not None:
                c_artifacts["centerline"] = store.write_geometry("centerline", "centerline", center.centerline)
            c_artifacts["manifest"] = store.write_stage_manifest("centerline", c_artifacts, center.metrics)
            status["stages"].append({"stage": "centerline", "success": center.success, "reason": center.reason_code, "confidence": center.confidence})
            if center.centerline is None:
                raise RuntimeError(center.reason_code or "centerline_failure")

            alt = AlternateLayoutAnalyzer(self.config.alternate_layout).run(center.centerline, center.metrics["branch_count"])
            alt_payload = asdict(alt)
            alt_artifacts = {"analysis": store.write_json("alternate_layouts", "analysis", alt_payload)}
            alt_artifacts["manifest"] = store.write_stage_manifest("alternate_layouts", alt_artifacts, alt_payload["evidence"])

            intel = GeometryIntelligenceBuilder().run(center.centerline)
            intel_payload = {
                "start_finish_wkt": intel.start_finish.wkt,
                "sectors": intel.sectors,
                "corner_graph": intel.corner_graph,
                "uncertainty": intel.uncertainty,
            }
            i_artifacts = {"intelligence": store.write_json("intelligence", "geometry_intelligence", intel_payload)}
            i_artifacts["manifest"] = store.write_stage_manifest("intelligence", i_artifacts, {"sector_count": len(intel.sectors)})

            mandatory_present = True
            validation = ValidationEngine(self.config.validation).run(boundary.cleaned_polygon, center.centerline, mandatory_present)
            findings = [asdict(f) for f in validation.findings]
            v_payload = {"publishable": validation.publishable, "findings": findings, "report": validation.report_text}
            v_artifacts = {
                "json": store.write_json("validation", "validation_report", v_payload),
                "txt": store.write_text("validation", "validation_report", validation.report_text),
            }
            v_artifacts["manifest"] = store.write_stage_manifest("validation", v_artifacts, {"publishable": validation.publishable})
            status["stages"].append({"stage": "validation", "success": validation.publishable, "reason": None, "confidence": 1.0 if validation.publishable else 0.0})

            status["state"] = "succeeded"
            status["publishable"] = validation.publishable
            status["finished_at"] = datetime.now(timezone.utc).isoformat()
            store.write_json("run", "status", status)
            return status
        except Exception as exc:
            status["state"] = "failed"
            status["error"] = {"message": str(exc), "stack_trace": traceback.format_exc()}
            status["finished_at"] = datetime.now(timezone.utc).isoformat()
            store.write_json("run", "status", status)
            return status
