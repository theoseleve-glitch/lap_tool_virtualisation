# TrackReco - Outdoor French Kart Track Layout Registry

Production-grade foundation for a curated French outdoor kart track layout registry with deterministic, auditable processing.

## Quick start

1. Copy env

```bash
cp .env.example .env
```

2. Start stack

```bash
make up
```

3. Apply migration

```bash
make migrate
```

4. Run tests

```bash
make test
```

## Core guarantees

- No silent overwrite of published/active geometry.
- Explicit state machines for all long-running jobs.
- Full auditability with created/updated user and timestamp fields.
- Versioned imagery, crops, extraction runs, and layout versions.
