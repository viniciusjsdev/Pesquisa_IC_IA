-- Application database only. Additive and safe to apply repeatedly.
CREATE TABLE IF NOT EXISTS observability_destinations (
    destination_id text PRIMARY KEY,
    descriptor jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS run_observability (
    harness_run_id uuid PRIMARY KEY,
    run_id uuid UNIQUE REFERENCES runs(id),
    job_id uuid REFERENCES run_jobs(id),
    principal_id uuid NOT NULL REFERENCES researchers(id),
    trace_id uuid NOT NULL UNIQUE,
    destination_id text NOT NULL REFERENCES observability_destinations(destination_id),
    content_mode text NOT NULL CHECK (content_mode IN ('metadata','redacted')),
    expected_event_ids jsonb NOT NULL DEFAULT '[]',
    sealed boolean NOT NULL DEFAULT false,
    submitted_events integer NOT NULL DEFAULT 0 CHECK (submitted_events >= 0),
    failed_events integer NOT NULL DEFAULT 0 CHECK (failed_events >= 0),
    dropped_events integer NOT NULL DEFAULT 0 CHECK (dropped_events >= 0),
    pending_events integer NOT NULL DEFAULT 0 CHECK (pending_events >= 0),
    state text NOT NULL DEFAULT 'pending' CHECK (state IN ('disabled','pending','submitted','partial','failed')),
    remote_verified boolean NOT NULL DEFAULT false,
    observed_remote_events integer CHECK (observed_remote_events >= 0),
    url text,
    trusted_origin text,
    last_checked_at timestamptz,
    last_check_error text,
    revision integer NOT NULL DEFAULT 1 CHECK (revision > 0)
);
INSERT INTO inference_schema_migrations(version) VALUES (4) ON CONFLICT DO NOTHING;
