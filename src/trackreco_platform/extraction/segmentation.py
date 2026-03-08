from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .catalogs import REASON_CODES
from .config import SegmentationConfig
from .geometry_utils import connected_components, open_close


@dataclass
class SegmentationResult:
    success: bool
    reason_code: str | None
    normalized: np.ndarray
    candidate_masks: dict[str, np.ndarray]
    cleaned_masks: dict[str, np.ndarray]
    final_mask: np.ndarray
    metrics: dict
    confidence: float


class Segmenter:
    def __init__(self, config: SegmentationConfig):
        self.config = config

    def run(self, image: np.ndarray) -> SegmentationResult:
        normalized = self._normalize(image)
        if self.config.mode == "ml":
            mask, reason = self._ml_mask(normalized)
            if mask is None:
                return SegmentationResult(
                    success=False,
                    reason_code=reason,
                    normalized=normalized,
                    candidate_masks={},
                    cleaned_masks={},
                    final_mask=np.zeros(normalized.shape[:2], dtype=bool),
                    metrics={"mode": "ml", "thresholds": self.config.__dict__},
                    confidence=0.0,
                )
            candidate = {"ml_mask": mask}
        else:
            gray = normalized.mean(axis=2)
            sat = normalized.max(axis=2) - normalized.min(axis=2)
            candidate = {
                "dark_surface": gray < self.config.grayscale_threshold,
                "low_saturation": sat < self.config.saturation_threshold,
            }
            candidate["combined"] = candidate["dark_surface"] & candidate["low_saturation"]

        cleaned = {k: open_close(v, self.config.opening_iterations, self.config.closing_iterations) for k, v in candidate.items()}
        final = cleaned.get("combined") if "combined" in cleaned else next(iter(cleaned.values()))
        comps = connected_components(final)
        retained = [c for c in comps if int(c.sum()) >= self.config.min_component_pixels]
        if not retained:
            return SegmentationResult(
                success=False,
                reason_code="segmentation_empty",
                normalized=normalized,
                candidate_masks=candidate,
                cleaned_masks=cleaned,
                final_mask=np.zeros_like(final, dtype=bool),
                metrics={"components": len(comps), "retained": 0, "thresholds": self.config.__dict__},
                confidence=0.0,
            )
        final_mask = np.logical_or.reduce(retained)
        fill_ratio = float(final_mask.mean())
        confidence = max(0.0, min(1.0, 1.0 - abs(fill_ratio - 0.23) / 0.23))
        return SegmentationResult(
            success=True,
            reason_code=None,
            normalized=normalized,
            candidate_masks=candidate,
            cleaned_masks=cleaned,
            final_mask=final_mask,
            metrics={
                "components": len(comps),
                "retained": len(retained),
                "fill_ratio": fill_ratio,
                "thresholds": self.config.__dict__,
            },
            confidence=confidence,
        )

    def _normalize(self, image: np.ndarray) -> np.ndarray:
        img = image.astype(np.float32)
        if img.max() <= 1.0:
            img *= 255.0
        img = np.clip(img, 0, 255)
        return img.astype(np.uint8)

    def _ml_mask(self, image: np.ndarray) -> tuple[np.ndarray | None, str | None]:
        try:
            import torch  # type: ignore
        except Exception:
            return None, "segmentation_ml_unavailable"
        _ = torch
        gray = image.mean(axis=2)
        return gray < self.config.grayscale_threshold, None


def reason_message(code: str | None) -> str | None:
    if not code:
        return None
    return REASON_CODES.get(code, code)
