# Layout Extraction Engine

## Artifact directory layout

```text
artifacts/layout_extraction/
  {venue_slug}/
    imagery_v{n}/
      crop_v{n}/
        {pipeline_version}/
          {run_id}/
            segmentation/
            boundary/
            centerline/
            alternate_layouts/
            intelligence/
            validation/
            run/status.json
```

Each stage stores raw/cleaned artifacts and `manifest.json` with deterministic metrics.

## Reason code catalog

See `trackreco_platform/extraction/catalogs.py` for canonical reason codes used by stage failures.

## Validation rule catalog

Rules `VAL001..VAL006` are deterministic and include severity, explanation, and remediation.

## Acceptance checklists

### Segmentation
- [x] Normalized image persisted.
- [x] Candidate and cleaned masks persisted.
- [x] Thresholds and confidence persisted.
- [x] ML adapter fallback reason code implemented.

### Boundary
- [x] Raw polygon and cleaned polygon artifacts persisted.
- [x] Hole handling and simplification.
- [x] Ambiguous multipolygon detection with explicit reason.
- [x] Invalid geometry not silently published.

### Centerline
- [x] Raw skeleton artifact persisted.
- [x] Loop closure quality metric.
- [x] Branch count + smoothness metrics.
- [x] Conservative failure on ambiguity.

### Alternate layouts
- [x] Branch evidence persisted.
- [x] Candidate variants scored conservatively.
- [x] Manual review status for proposed alternates.

### Intelligence
- [x] Start/finish candidate generated.
- [x] Sector + corner graph generated.
- [x] Uncertainty explicitly encoded.

### Validation and orchestration
- [x] JSON + text reports generated.
- [x] Deterministic publishability decision.
- [x] Explicit stage transitions and persisted status.
- [x] Failures persisted with stack trace.
