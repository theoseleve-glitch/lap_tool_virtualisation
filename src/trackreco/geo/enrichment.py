from __future__ import annotations

from dataclasses import dataclass

from trackreco.models import CandidateRecord


@dataclass(slots=True)
class GeoAttribution:
    lat: float | None
    lon: float | None
    point_geom: str | None
    bbox_geom: str | None
    initial_working_bbox: str | None
    refs: list[str]
    reason_codes: list[str]


def _bbox(lat: float, lon: float, delta: float = 0.0025) -> str:
    return f"POLYGON(({lon-delta} {lat-delta},{lon+delta} {lat-delta},{lon+delta} {lat+delta},{lon-delta} {lat+delta},{lon-delta} {lat-delta}))"


def derive_geometry(candidates: list[CandidateRecord]) -> GeoAttribution:
    coords = [(c.lat, c.lon, c.source_type) for c in candidates if c.lat is not None and c.lon is not None]
    if not coords:
        return GeoAttribution(None, None, None, None, None, [], ["insufficient_evidence"])

    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    lat = sum(lats) / len(lats)
    lon = sum(lons) / len(lons)
    reasons = []
    if max(lats) - min(lats) > 0.01 or max(lons) - min(lons) > 0.01:
        reasons.append("conflicting_coordinates")
    refs = [f"{src}:{la},{lo}" for la, lo, src in coords]
    return GeoAttribution(
        lat=lat,
        lon=lon,
        point_geom=f"POINT({lon} {lat})",
        bbox_geom=_bbox(lat, lon),
        initial_working_bbox=_bbox(lat, lon, delta=0.005),
        refs=refs,
        reason_codes=reasons,
    )
