# TrackReco

Production-oriented, traceable acquisition pipeline for an authoritative master list of **outdoor kart venues** in France and Britain (England/Scotland/Wales), with explicit Northern Ireland flagging when sourced via official UK flows.

## Key guarantees
- Tiered evidence strategy (official > OSM > venue pages > fallback).
- Conservative classification; no silent assumptions.
- Full provenance for every candidate and accepted/rejected decision.
- Deterministic config and versioned run outputs (`outputs/run_<timestamp>`).

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]
trackreco --config config/pipeline.json
```

## Outputs per run
- `master_tracks.csv`
- `master_tracks.json`
- `candidate_review_queue.csv`
- `source_evidence.jsonl`
- `merge_candidates.csv`
- `rejected_candidates.csv`
- `accepted_points.geojson`
- `run_log.jsonl`
- `run_report.json`

## Launch checklist
See `docs/launch_checklist.md`.
