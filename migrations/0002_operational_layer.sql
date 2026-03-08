ALTER TYPE reviewactiontype ADD VALUE IF NOT EXISTS 'submit_for_review';
ALTER TYPE publishaction ADD VALUE IF NOT EXISTS 'rollback';

DO $$ BEGIN
    CREATE TYPE reviewstatus AS ENUM ('draft', 'in_review', 'changes_requested', 'approved', 'rejected');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

ALTER TABLE layout_versions ADD COLUMN IF NOT EXISTS review_status reviewstatus NOT NULL DEFAULT 'draft';
ALTER TABLE publish_history ADD COLUMN IF NOT EXISTS previous_layout_version_id uuid REFERENCES layout_versions(id);

CREATE TABLE IF NOT EXISTS audit_events (
    id uuid PRIMARY KEY,
    event_type varchar(80) NOT NULL,
    entity_type varchar(80) NOT NULL,
    entity_id varchar(36) NOT NULL,
    correlation_id varchar(64) NOT NULL,
    payload json NOT NULL DEFAULT '{}'::json,
    created_at timestamptz,
    updated_at timestamptz,
    created_by varchar(120),
    updated_by varchar(120)
);

CREATE INDEX IF NOT EXISTS ix_audit_events_entity ON audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_correlation ON audit_events(correlation_id);
