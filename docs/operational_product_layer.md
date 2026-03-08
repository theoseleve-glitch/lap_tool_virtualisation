# Operational Product Layer - Outdoor French Kart Track Layout Registry

## Review state machine

Explicit transitions:

- `draft -> submit_for_review -> in_review`
- `changes_requested -> submit_for_review -> in_review`
- `in_review -> approve -> approved`
- `in_review -> reject -> rejected`
- `in_review -> request_changes -> changes_requested`

Publishing invariants:

- Only `approved` layout versions can be published.
- Publish targets one exact `layout_version_id`.
- Rollback is represented as `publish_history.action = rollback` when an older approved version is republished.
- Unpublish clears `layouts.active_version_id` and appends `publish_history`.
- Published geometry is immutable in-place: edits create new `layout_versions` records with `supersedes_layout_version_id`.

## Role/permission matrix

| Role | Read | Review | Publish | Edit Geometry | Manage Jobs |
|---|---|---|---|---|---|
| viewer | ✅ | ❌ | ❌ | ❌ | ❌ |
| reviewer | ✅ | ✅ | ❌ | ❌ | ❌ |
| editor | ✅ | ❌ | ❌ | ✅ | ❌ |
| publisher | ✅ | ✅ | ✅ | ❌ | ❌ |
| admin | ✅ | ✅ | ✅ | ✅ | ✅ |

## Audit & provenance

Audit events are written for review/publish/unpublish and include correlation ID, actor, payload.

Provenance chain for publication must resolve:

1. publish history entry
2. layout version and immutable hash
3. extraction run
4. working area (crop) version
5. imagery version
6. validation report(s)
7. review actions

## Lap contract policy

- Endpoint: `GET /api/v1/lap/venues/{venue_id}/layout?version={optional}`
- Stable payload field names; additive changes only.
- Contract version string is explicit (`contract_version`).
- Version pinning supported through `version` query parameter.

## Acceptance checklist

### Review + publish safety
- [x] Explicit review transitions only.
- [x] Reviewer identity and timestamps captured.
- [x] Publish/unpublish/rollback fully logged in history.
- [x] No silent replacement of published version.

### Geometry editing safety
- [x] Editing creates new draft version only.
- [x] Audit note required on manual edits.
- [x] Save draft and submit-for-review supported.
- [x] Edit output re-enters validation/review flow via review status.

### Deterministic assets
- [x] Asset keys are version-based (`layouts/{layout}/versions/{version}/...`).
- [x] Checksums persisted in artifact references.
- [x] Re-generation for same version yields identical bytes.

### Observability + auditability
- [x] Correlation IDs propagated and returned.
- [x] Structured request completion logging.
- [x] Audit events capture high-risk actions.
- [x] Failure cases return explicit error codes.
