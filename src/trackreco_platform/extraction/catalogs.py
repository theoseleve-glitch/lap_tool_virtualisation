REASON_CODES = {
    "segmentation_empty": "No drivable pixels remain after mask cleaning.",
    "segmentation_ml_unavailable": "ML adapter requested but torch/runtime unavailable.",
    "boundary_no_polygon": "Mask did not produce any valid polygon candidate.",
    "boundary_ambiguous_multi": "Multiple disconnected polygon candidates remain.",
    "boundary_invalid": "Boundary polygon remains invalid after repair attempts.",
    "centerline_empty": "Skeleton graph contains no closed-loop candidate.",
    "centerline_ambiguous_branch": "Multiple branch loops have similar scores; requires manual review.",
    "alternate_low_confidence": "Alternate branch evidence exists but confidence below publication threshold.",
    "validation_failed": "One or more publishability rules failed.",
}

RULE_CATALOG = {
    "VAL001": {
        "severity": "error",
        "explanation": "Boundary polygon must be valid and non-empty.",
        "remediation": "Inspect boundary artifacts, repair or redraw working crop/mask.",
    },
    "VAL002": {
        "severity": "error",
        "explanation": "Centerline must be a closed continuous loop.",
        "remediation": "Inspect skeleton branch artifacts and manually resolve branch ambiguity.",
    },
    "VAL003": {
        "severity": "error",
        "explanation": "Centerline must lie mostly inside boundary.",
        "remediation": "Re-run with adjusted segmentation thresholds or crop.",
    },
    "VAL004": {
        "severity": "warn",
        "explanation": "Track mean width should stay within configured sanity range.",
        "remediation": "Check scale metadata and lane extraction quality.",
    },
    "VAL005": {
        "severity": "error",
        "explanation": "Track length must lie within configured limits.",
        "remediation": "Verify CRS, crop extent, and centerline smoothing settings.",
    },
    "VAL006": {
        "severity": "error",
        "explanation": "All mandatory artifacts and metadata must be present.",
        "remediation": "Re-run extraction; verify artifact persistence path permissions.",
    },
}
