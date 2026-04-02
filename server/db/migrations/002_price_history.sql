CREATE TABLE IF NOT EXISTS price_history (
  id               BIGSERIAL PRIMARY KEY,
  item_id          UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  price            INTEGER NOT NULL,
  unit_price       INTEGER,
  quantity         SMALLINT NOT NULL DEFAULT 1,
  is_stack         BOOLEAN NOT NULL DEFAULT FALSE,
  rarity           VARCHAR(32),
  static_attribute TEXT,
  random_attribute TEXT,
  expires_at       TEXT,
  observed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_payload      JSONB
);

CREATE INDEX IF NOT EXISTS idx_ph_item_time ON price_history (item_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_ph_observed  ON price_history (observed_at DESC);
