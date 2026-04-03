-- Migration 004: Add rarity to items identity, replace attribute text columns
-- with a JSONB field.
--
-- Changes:
--   items         — add rarity column; new unique index includes rarity
--   price_history — add attributes JSONB; drop static_attribute / random_attribute
--
-- Data migration: existing price_history rows (which carry rarity) are used to
-- split any items rows that cover multiple rarities into per-rarity rows.

BEGIN;

-- ── 1. Add rarity to items ────────────────────────────────────────────────────
ALTER TABLE items ADD COLUMN IF NOT EXISTS rarity VARCHAR(32);

-- ── 2. Split items that have price_history rows with different rarities ────────
-- For each (item_id, rarity) combination in price_history that doesn't yet
-- have its own items row, create one and re-point the price_history rows to it.
DO $$
DECLARE
  rec    RECORD;
  new_id UUID;
BEGIN
  FOR rec IN
    SELECT DISTINCT ph.item_id, ph.rarity, i.name, i.slot, i.item_type
    FROM   price_history ph
    JOIN   items i ON i.id = ph.item_id
    WHERE  ph.rarity IS NOT NULL
      AND  (i.rarity IS NULL OR i.rarity <> ph.rarity)
  LOOP
    -- Reuse an existing row for (name, rarity, slot) if one already exists
    SELECT id INTO new_id
    FROM   items
    WHERE  name              = rec.name
      AND  COALESCE(rarity,  '') = COALESCE(rec.rarity, '')
      AND  COALESCE(slot,    '') = COALESCE(rec.slot,   '');

    IF new_id IS NULL THEN
      INSERT INTO items (name, slot, item_type, rarity)
      VALUES (rec.name, rec.slot, rec.item_type, rec.rarity)
      RETURNING id INTO new_id;
    END IF;

    -- Re-point price_history rows that belong to this (item, rarity) pair
    UPDATE price_history
    SET    item_id = new_id
    WHERE  item_id = rec.item_id
      AND  COALESCE(rarity, '') = COALESCE(rec.rarity, '');
  END LOOP;
END $$;

-- ── 3. Remove orphaned items rows (no longer referenced by price_history) ─────
DELETE FROM items
WHERE rarity IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM price_history WHERE item_id = items.id
  );

-- ── 4. Swap the unique index ──────────────────────────────────────────────────
DROP INDEX IF EXISTS idx_items_name_slot;

CREATE UNIQUE INDEX IF NOT EXISTS idx_items_name_rarity_slot
  ON items (name, COALESCE(rarity, ''), COALESCE(slot, ''));

-- ── 5. Add attributes JSONB to price_history ──────────────────────────────────
ALTER TABLE price_history ADD COLUMN IF NOT EXISTS attributes JSONB;

-- Migrate existing text columns into the new JSONB field
UPDATE price_history
SET attributes = jsonb_strip_nulls(jsonb_build_object(
  'static', static_attribute,
  'random', random_attribute
))
WHERE static_attribute IS NOT NULL
   OR random_attribute IS NOT NULL;

-- Drop the old individual text columns
ALTER TABLE price_history DROP COLUMN IF EXISTS static_attribute;
ALTER TABLE price_history DROP COLUMN IF EXISTS random_attribute;

-- GIN index for attribute queries (e.g. find all items with a specific roll)
CREATE INDEX IF NOT EXISTS idx_ph_attributes
  ON price_history USING gin(attributes)
  WHERE attributes IS NOT NULL;

COMMIT;
