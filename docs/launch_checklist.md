# Launch Checklist

- [ ] Validate deterministic config (`config/pipeline.json`) checked into version control.
- [ ] Verify tier-1 source connectors parse current official pages.
- [ ] Ensure legal/robots constraints for fetched artifacts are respected.
- [ ] Run test suite.
- [ ] Execute pipeline and inspect `run_report.json` counts.
- [ ] Manually review `candidate_review_queue.csv` before publishing.
- [ ] Confirm no accepted row lacks `acceptance_reason_codes`.
- [ ] Confirm NI rows are explicitly separable by `country` + `ni_flag`.
- [ ] Archive run artifacts for traceability.
