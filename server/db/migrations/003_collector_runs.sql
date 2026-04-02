CREATE TABLE IF NOT EXISTS collector_runs (
  id            BIGSERIAL PRIMARY KEY,
  started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at   TIMESTAMPTZ,
  status        VARCHAR(20) NOT NULL DEFAULT 'running'
                  CHECK (status IN ('running', 'success', 'error')),
  rows_inserted INTEGER,
  error_message TEXT
);
