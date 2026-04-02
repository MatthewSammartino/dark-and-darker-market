CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS items (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       VARCHAR(255) NOT NULL,
  slot       VARCHAR(64),
  item_type  VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_items_name_slot ON items (name, COALESCE(slot, ''));
CREATE INDEX IF NOT EXISTS idx_items_name_fts ON items USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_items_slot ON items (slot);
