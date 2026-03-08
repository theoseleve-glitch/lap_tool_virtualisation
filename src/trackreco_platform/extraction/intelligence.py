from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely.geometry import LineString, Point


@dataclass
class GeometryIntelligence:
    start_finish: Point
    sectors: list[dict]
    corner_graph: dict
    uncertainty: dict


class GeometryIntelligenceBuilder:
    def run(self, centerline: LineString) -> GeometryIntelligence:
        coords = np.array(centerline.coords)
        start = Point(coords[0])
        n = len(coords)
        sectors = []
        for idx, frac in enumerate((0.33, 0.66, 1.0), start=1):
            sectors.append({"sector": idx, "end_index": int((n - 1) * frac), "confidence": 0.7})
        corners = []
        for i in range(1, n - 1):
            a = coords[i] - coords[i - 1]
            b = coords[i + 1] - coords[i]
            if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
                continue
            turn = float(np.cross(np.append(a, 0), np.append(b, 0))[2])
            if abs(turn) > 0.2:
                corners.append({"vertex_index": i, "turn_strength": abs(turn), "class": "corner"})
        corner_graph = {"nodes": corners, "edges": [{"u": i, "v": i + 1} for i in range(max(0, len(corners) - 1))]}
        return GeometryIntelligence(
            start_finish=start,
            sectors=sectors,
            corner_graph=corner_graph,
            uncertainty={"start_finish_sigma_m": 4.0, "sector_sigma_m": 8.0, "corner_classification_confidence": 0.7},
        )
