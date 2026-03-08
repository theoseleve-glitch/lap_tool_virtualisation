from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union


def binary_morph(mask: np.ndarray, iterations: int, mode: str) -> np.ndarray:
    out = mask.copy().astype(bool)
    for _ in range(max(0, iterations)):
        neighbors = _neighbor_count(out)
        if mode == "dilate":
            out = out | (neighbors >= 1)
        elif mode == "erode":
            out = out & (neighbors == 8)
        else:
            raise ValueError(mode)
    return out


def open_close(mask: np.ndarray, opening: int, closing: int) -> np.ndarray:
    opened = binary_morph(binary_morph(mask, opening, "erode"), opening, "dilate")
    closed = binary_morph(binary_morph(opened, closing, "dilate"), closing, "erode")
    return closed


def _neighbor_count(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask.astype(np.uint8), 1)
    c = np.zeros(mask.shape, dtype=np.uint8)
    for y in (-1, 0, 1):
        for x in (-1, 0, 1):
            if y == 0 and x == 0:
                continue
            c += padded[1 + y : 1 + y + mask.shape[0], 1 + x : 1 + x + mask.shape[1]]
    return c


def connected_components(mask: np.ndarray) -> list[np.ndarray]:
    visited = np.zeros(mask.shape, dtype=bool)
    comps: list[list[tuple[int, int]]] = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue
            q = [(y, x)]
            visited[y, x] = True
            comp = []
            while q:
                cy, cx = q.pop()
                comp.append((cy, cx))
                for ny in (cy - 1, cy, cy + 1):
                    for nx in (cx - 1, cx, cx + 1):
                        if ny < 0 or nx < 0 or ny >= h or nx >= w:
                            continue
                        if visited[ny, nx] or not mask[ny, nx]:
                            continue
                        visited[ny, nx] = True
                        q.append((ny, nx))
            comps.append(comp)
    out = []
    for comp in comps:
        m = np.zeros(mask.shape, dtype=bool)
        ys, xs = zip(*comp)
        m[np.array(ys), np.array(xs)] = True
        out.append(m)
    return out


def mask_to_polygon(mask: np.ndarray, pixel_size_m: float) -> Polygon | None:
    cells: list[Polygon] = []
    ys, xs = np.where(mask)
    for y, x in zip(ys, xs, strict=True):
        cells.append(box(x * pixel_size_m, y * pixel_size_m, (x + 1) * pixel_size_m, (y + 1) * pixel_size_m))
    if not cells:
        return None
    merged = unary_union(cells)
    if merged.geom_type == "Polygon":
        return merged
    parts = [g for g in merged.geoms if g.geom_type == "Polygon"]
    if not parts:
        return None
    return max(parts, key=lambda g: g.area)


def smooth_linestring(line: LineString, iterations: int) -> LineString:
    coords = np.array(line.coords)
    for _ in range(max(0, iterations)):
        new_coords = coords.copy()
        for i in range(1, len(coords) - 1):
            new_coords[i] = (coords[i - 1] + 2 * coords[i] + coords[i + 1]) / 4.0
        coords = new_coords
    return LineString(coords)


def circular_smoothness(line: LineString) -> float:
    coords = np.array(line.coords)
    if len(coords) < 4:
        return 0.0
    angles: list[float] = []
    for i in range(1, len(coords) - 1):
        v1 = coords[i] - coords[i - 1]
        v2 = coords[i + 1] - coords[i]
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            continue
        cosv = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
        angles.append(math.acos(cosv))
    if not angles:
        return 0.0
    return float(np.mean(angles))


def select_longest(lines: Iterable[LineString]) -> LineString | None:
    items = list(lines)
    if not items:
        return None
    return max(items, key=lambda l: l.length)
