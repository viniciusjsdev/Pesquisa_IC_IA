CREATE TABLE verification_criteria_revisions (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    author text NOT NULL,
    config jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (name, revision)
);
INSERT INTO inference_schema_migrations (version) VALUES (2);
