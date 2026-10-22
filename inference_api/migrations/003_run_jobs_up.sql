CREATE TABLE run_jobs (
    id uuid PRIMARY KEY,
    researcher_id uuid NOT NULL REFERENCES researchers(id),
    request_key uuid NOT NULL,
    request jsonb NOT NULL,
    status text NOT NULL CHECK (status IN ('accepted', 'running', 'completed', 'failed', 'interrupted', 'busy')),
    run_id uuid REFERENCES runs(id),
    error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz,
    UNIQUE (researcher_id, request_key)
);
CREATE UNIQUE INDEX run_jobs_one_active ON run_jobs ((1))
    WHERE status IN ('accepted', 'running');
INSERT INTO inference_schema_migrations (version) VALUES (3);
