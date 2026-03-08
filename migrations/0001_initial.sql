CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TYPE venue_status AS ENUM ('active','inactive');
CREATE TYPE imagery_status AS ENUM ('ingesting','ready','failed');
CREATE TYPE crop_status AS ENUM ('draft','active','retired');
CREATE TYPE extraction_run_status AS ENUM ('queued','running','succeeded','failed');
CREATE TYPE layout_status AS ENUM ('draft','validated','published','unpublished');
CREATE TYPE job_status AS ENUM ('queued','running','succeeded','failed');
CREATE TYPE job_type AS ENUM ('venue_import','imagery_ingestion','extraction');
CREATE TYPE review_action_type AS ENUM ('approve','reject','request_changes');
CREATE TYPE publish_action AS ENUM ('publish','unpublish');

CREATE TABLE venues (
  id UUID PRIMARY KEY,
  slug VARCHAR(160) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  status venue_status NOT NULL DEFAULT 'active',
  country_code CHAR(2) NOT NULL DEFAULT 'FR',
  working_bbox geometry(POLYGON,4326),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE venue_aliases (
  id UUID PRIMARY KEY,
  venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
  alias VARCHAR(255) NOT NULL,
  source_ref VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120),
  CONSTRAINT uq_venue_alias UNIQUE (venue_id, alias)
);

CREATE TABLE imagery_assets (
  id UUID PRIMARY KEY,
  venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
  version INT NOT NULL,
  source_name VARCHAR(80) NOT NULL,
  source_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  raw_path TEXT NOT NULL,
  normalized_path TEXT NOT NULL,
  thumbnail_path TEXT,
  sha256 CHAR(64) NOT NULL,
  status imagery_status NOT NULL DEFAULT 'ingesting',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120),
  CONSTRAINT uq_imagery_venue_version UNIQUE (venue_id, version)
);
CREATE INDEX idx_imagery_venue ON imagery_assets(venue_id);

CREATE TABLE working_area_versions (
  id UUID PRIMARY KEY,
  venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
  imagery_asset_id UUID NOT NULL REFERENCES imagery_assets(id) ON DELETE RESTRICT,
  version INT NOT NULL,
  bbox geometry(POLYGON,4326) NOT NULL,
  boundary_polygon geometry(POLYGON,4326) NOT NULL,
  area_ha DOUBLE PRECISION NOT NULL CHECK (area_ha > 0),
  status crop_status NOT NULL DEFAULT 'draft',
  retired_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120),
  CONSTRAINT uq_working_area_version UNIQUE (venue_id, version)
);
CREATE INDEX idx_working_area_venue ON working_area_versions(venue_id);

CREATE TABLE extraction_runs (
  id UUID PRIMARY KEY,
  venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
  working_area_version_id UUID NOT NULL REFERENCES working_area_versions(id) ON DELETE RESTRICT,
  status extraction_run_status NOT NULL DEFAULT 'queued',
  config_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  failure_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE layouts (
  id UUID PRIMARY KEY,
  venue_id UUID NOT NULL UNIQUE REFERENCES venues(id) ON DELETE CASCADE,
  active_version_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE layout_versions (
  id UUID PRIMARY KEY,
  layout_id UUID NOT NULL REFERENCES layouts(id) ON DELETE CASCADE,
  extraction_run_id UUID NOT NULL REFERENCES extraction_runs(id) ON DELETE RESTRICT,
  version INT NOT NULL,
  status layout_status NOT NULL DEFAULT 'draft',
  boundary_polygon geometry(POLYGON,4326) NOT NULL,
  centerline geometry(LINESTRING,4326) NOT NULL,
  start_finish geometry(POINT,4326) NOT NULL,
  sectors JSONB NOT NULL DEFAULT '{}'::jsonb,
  corner_graph_ref TEXT,
  supersedes_layout_version_id UUID REFERENCES layout_versions(id) ON DELETE RESTRICT,
  immutable_hash CHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120),
  CONSTRAINT uq_layout_version UNIQUE (layout_id, version)
);
ALTER TABLE layouts ADD CONSTRAINT fk_layout_active_version FOREIGN KEY (active_version_id) REFERENCES layout_versions(id) ON DELETE RESTRICT;

CREATE TABLE validation_reports (
  id UUID PRIMARY KEY,
  layout_version_id UUID NOT NULL REFERENCES layout_versions(id) ON DELETE CASCADE,
  validator_version VARCHAR(60) NOT NULL,
  passed BOOLEAN NOT NULL,
  findings JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE review_actions (
  id UUID PRIMARY KEY,
  layout_version_id UUID NOT NULL REFERENCES layout_versions(id) ON DELETE CASCADE,
  action review_action_type NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE publish_history (
  id UUID PRIMARY KEY,
  layout_version_id UUID NOT NULL REFERENCES layout_versions(id) ON DELETE RESTRICT,
  action publish_action NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE processing_jobs (
  id UUID PRIMARY KEY,
  job_type job_type NOT NULL,
  status job_status NOT NULL DEFAULT 'queued',
  requested_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_code VARCHAR(80),
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE artifact_references (
  id UUID PRIMARY KEY,
  entity_type VARCHAR(80) NOT NULL,
  entity_id VARCHAR(36) NOT NULL,
  artifact_type VARCHAR(80) NOT NULL,
  storage_path TEXT NOT NULL,
  checksum CHAR(64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(320) UNIQUE NOT NULL,
  role VARCHAR(40) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by VARCHAR(120),
  updated_by VARCHAR(120)
);

CREATE TABLE role_permissions (
  id SERIAL PRIMARY KEY,
  role VARCHAR(40) NOT NULL,
  permission VARCHAR(80) NOT NULL,
  CONSTRAINT uq_role_permission UNIQUE (role, permission)
);

CREATE UNIQUE INDEX uq_single_published_layout_version_per_layout
  ON layout_versions(layout_id)
  WHERE status = 'published';
