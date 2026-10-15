CREATE TABLE researchers (
    id uuid PRIMARY KEY,
    username text NOT NULL UNIQUE CHECK (username IN ('Nicoli', 'Vinicius')),
    password_salt bytea NOT NULL,
    password_digest bytea NOT NULL,
    active boolean NOT NULL DEFAULT true,
    failed_attempts integer NOT NULL DEFAULT 0,
    locked_until timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE researcher_sessions (
    id uuid PRIMARY KEY,
    researcher_id uuid NOT NULL REFERENCES researchers(id) ON DELETE CASCADE,
    token_salt bytea NOT NULL,
    token_digest bytea NOT NULL,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX researcher_sessions_researcher_idx
    ON researcher_sessions (researcher_id);

CREATE TABLE inference_usage (
    usage_day date NOT NULL,
    researcher_id uuid REFERENCES researchers(id) ON DELETE CASCADE,
    attempts integer NOT NULL CHECK (attempts >= 0)
);

CREATE UNIQUE INDEX inference_usage_global_unique
    ON inference_usage (usage_day) WHERE researcher_id IS NULL;
CREATE UNIQUE INDEX inference_usage_user_unique
    ON inference_usage (usage_day, researcher_id) WHERE researcher_id IS NOT NULL;

CREATE TABLE inference_schema_migrations (
    version integer PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO inference_schema_migrations (version) VALUES (1);
