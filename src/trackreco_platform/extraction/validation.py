from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

from .catalogs import RULE_CATALOG
from .config import ValidationConfig


@dataclass
class ValidationFinding:
    code: str
    severity: str
    passed: bool
    explanation: str
    remediation: str
    detail: str


@dataclass
class ValidationResult:
    publishable: bool
    findings: list[ValidationFinding]
    report_text: str


class ValidationEngine:
    def __init__(self, config: ValidationConfig):
        self.config = config

    def run(
        self,
        boundary: Polygon | None,
        centerline: LineString | None,
        artifacts_complete: bool,
    ) -> ValidationResult:
        findings: list[ValidationFinding] = []
        findings.append(self._boundary_rule(boundary))
        findings.append(self._centerline_rule(centerline))
        findings.append(self._inside_rule(boundary, centerline))
        findings.append(self._width_rule(boundary, centerline))
        findings.append(self._length_rule(centerline))
        findings.append(self._artifact_rule(artifacts_complete))
        publishable = all(f.passed or f.severity != "error" for f in findings)
        lines = [f"[{f.code}] {f.severity.upper()} - {'PASS' if f.passed else 'FAIL'}: {f.detail}" for f in findings]
        return ValidationResult(publishable=publishable, findings=findings, report_text="\n".join(lines))

    def _make(self, code: str, passed: bool, detail: str) -> ValidationFinding:
        meta = RULE_CATALOG[code]
        return ValidationFinding(code, meta["severity"], passed, meta["explanation"], meta["remediation"], detail)

    def _boundary_rule(self, boundary: Polygon | None) -> ValidationFinding:
        ok = boundary is not None and boundary.is_valid and not boundary.is_empty
        return self._make("VAL001", ok, "Boundary geometry validity check")

    def _centerline_rule(self, centerline: LineString | None) -> ValidationFinding:
        ok = centerline is not None and centerline.is_ring
        return self._make("VAL002", ok, "Centerline closure/continuity check")

    def _inside_rule(self, boundary: Polygon | None, centerline: LineString | None) -> ValidationFinding:
        if not boundary or not centerline:
            return self._make("VAL003", False, "Missing geometry")
        inside = centerline.buffer(0.01).difference(boundary).length / max(centerline.length, 1e-6)
        ok = inside <= self.config.max_centerline_outside_ratio
        return self._make("VAL003", ok, f"Outside ratio={inside:.6f}")

    def _width_rule(self, boundary: Polygon | None, centerline: LineString | None) -> ValidationFinding:
        if not boundary or not centerline:
            return self._make("VAL004", False, "Missing geometry")
        width = boundary.area / max(centerline.length, 1e-6)
        ok = self.config.min_mean_width_m <= width <= self.config.max_mean_width_m
        return self._make("VAL004", ok, f"Mean width={width:.2f}m")

    def _length_rule(self, centerline: LineString | None) -> ValidationFinding:
        length = 0.0 if centerline is None else centerline.length
        ok = self.config.min_track_length_m <= length <= self.config.max_track_length_m
        return self._make("VAL005", ok, f"Length={length:.2f}m")

    def _artifact_rule(self, artifacts_complete: bool) -> ValidationFinding:
        return self._make("VAL006", artifacts_complete, "Mandatory artifact presence check")
