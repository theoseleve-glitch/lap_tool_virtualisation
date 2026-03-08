from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely.geometry import MultiPolygon, Polygon
from shapely.validation import make_valid

from .config import BoundaryConfig
from .geometry_utils import connected_components, mask_to_polygon


@dataclass
class BoundaryResult:
    success: bool
    reason_code: str | None
    raw_polygon: Polygon | MultiPolygon | None
    cleaned_polygon: Polygon | None
    metrics: dict
    confidence: float
    ambiguous: bool


class BoundaryExtractor:
    def __init__(self, config: BoundaryConfig):
        self.config = config

    def run(self, mask: np.ndarray, pixel_size_m: float) -> BoundaryResult:
        comps = connected_components(mask)
        polygons: list[Polygon] = []
        for comp in comps:
            poly = mask_to_polygon(comp, pixel_size_m)
            if poly and poly.area >= self.config.min_area_m2:
                polygons.append(poly)

        if not polygons:
            return BoundaryResult(False, "boundary_no_polygon", None, None, {"components": len(comps)}, 0.0, False)

        polygons.sort(key=lambda p: p.area, reverse=True)
        ambiguous = len(polygons) > 1 and polygons[1].area / polygons[0].area > 0.35
        raw = MultiPolygon(polygons) if len(polygons) > 1 else polygons[0]
        cleaned = polygons[0].simplify(self.config.simplify_tolerance_m, preserve_topology=True)
        if not cleaned.is_valid:
            cleaned = make_valid(cleaned)
        if cleaned.geom_type == "MultiPolygon":
            cleaned = max(cleaned.geoms, key=lambda g: g.area)
        if not isinstance(cleaned, Polygon) or not cleaned.is_valid:
            return BoundaryResult(False, "boundary_invalid", raw, None, {"ambiguous": ambiguous}, 0.0, ambiguous)
        holes = [h for h in cleaned.interiors if Polygon(h).area >= self.config.hole_area_threshold_m2]
        cleaned = Polygon(cleaned.exterior.coords, holes=[h.coords for h in holes])
        confidence = 0.5 if ambiguous else 0.9
        reason = "boundary_ambiguous_multi" if ambiguous else None
        return BoundaryResult(
            success=not ambiguous,
            reason_code=reason,
            raw_polygon=raw,
            cleaned_polygon=cleaned,
            metrics={"candidate_count": len(polygons), "area_m2": cleaned.area, "hole_count": len(holes), "ambiguous": ambiguous},
            confidence=confidence,
            ambiguous=ambiguous,
        )
