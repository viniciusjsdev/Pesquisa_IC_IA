-- Non-destructive rollback: keep receipts/destinations and all immutable runs.
-- Older application versions ignore these additive tables.
DELETE FROM inference_schema_migrations WHERE version = 4;
