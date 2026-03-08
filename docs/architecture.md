# Outdoor French Kart Track Layout Registry - Foundation

## Architecture choice

**Monorepo with clear service boundaries**

- `trackreco_platform` API service (FastAPI): admin and registry read APIs.
- `trackreco_platform` worker service (Celery): long-running ingestion/extraction tasks.
- Shared domain library: SQLAlchemy models, enums, repositories, validation services.
- Shared storage adapter: S3-compatible artifact management.

This monorepo is selected for deterministic schema/API evolution and cross-module traceability.

## Repository tree

- `src/trackreco_platform/api`: route handlers and API schemas.
- `src/trackreco_platform/domain`: immutable enums and relational geometry model.
- `src/trackreco_platform/repositories`: persistence access patterns.
- `src/trackreco_platform/services`: deterministic business workflows.
- `src/trackreco_platform/workers`: async execution.
- `src/trackreco_platform/storage`: object storage abstraction.
- `migrations`: SQL schema migrations.
- `schemas`: OpenAPI contract.
- `tests`: unit + integration-level behaviors.
- `docs`: architecture, state machines, runbooks.

## State machines

### Processing job

`queued -> running -> (succeeded | failed)`

No direct transition from `queued` to `succeeded`.

### Imagery asset

`ingesting -> (ready | failed)`

Once `ready`, immutable object paths and checksum cannot be overwritten.

### Working area version

`draft -> active -> retired`

Only one active crop per venue. Activation retires previous active record with explicit reason.

### Layout version

`draft -> validated -> published -> unpublished`

Published state transition is recorded in `publish_history`; no silent replacement.

## Acceptance checklist

### Repository + service architecture

- [x] Monorepo structure with API + worker + shared domain modules.
- [x] Dockerized local stack (Postgres/PostGIS, Redis, MinIO, API, worker).
- [x] Makefile task runner and environment config sample.

### Domain schema

- [x] PostGIS geometry columns for bbox, boundaries, centerline, start/finish.
- [x] Versioned imagery, crop, and layout models.
- [x] Audit fields + immutable hash + publish history.

### API contracts

- [x] OpenAPI-first baseline at `schemas/openapi.yaml`.
- [x] Explicit job status endpoints for long-running operations.
- [x] Consistent structured failures for domain errors.

### Venue registry

- [x] CSV import with row validation and rejection reason codes.
- [x] Duplicate detection and deterministic slug generation.
- [x] Import run persisted in `processing_jobs`.

### Imagery ingestion

- [x] Fetch abstraction + metadata persistence.
- [x] Deterministic hashing and object storage version paths.
- [x] Explicit ingestion job states and result payload.

### Working area/crop

- [x] Version model and activation semantics.
- [x] Geometry sanity checks and area constraints.
- [x] Auditability via created/updated fields.
