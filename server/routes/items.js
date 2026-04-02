const express = require("express");
const router = express.Router();
const pool = require("../db/pool");

// GET /api/items/search?q=
router.get("/search", async (req, res) => {
  const { q } = req.query;
  if (!q || q.trim().length === 0) return res.json([]);
  try {
    const { rows } = await pool.query(
      `SELECT id, name, slot, item_type
       FROM items
       WHERE to_tsvector('english', name) @@ plainto_tsquery('english', $1)
          OR name ILIKE $2
       LIMIT 20`,
      [q, `%${q}%`]
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/items?q=&slot=&rarity=&limit=50&offset=0
router.get("/", async (req, res) => {
  const { q, slot, limit = 50, offset = 0 } = req.query;
  const conditions = [];
  const params = [];

  if (q) {
    params.push(`%${q}%`);
    conditions.push(`i.name ILIKE $${params.length}`);
  }
  if (slot) {
    params.push(slot);
    conditions.push(`i.slot = $${params.length}`);
  }

  const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
  params.push(Number(limit), Number(offset));

  try {
    const { rows } = await pool.query(
      `SELECT i.id, i.name, i.slot, i.item_type,
              ph.price AS latest_price,
              ph.rarity AS latest_rarity,
              ph.observed_at AS last_seen
       FROM items i
       LEFT JOIN LATERAL (
         SELECT price, rarity, observed_at
         FROM price_history
         WHERE item_id = i.id
         ORDER BY observed_at DESC
         LIMIT 1
       ) ph ON true
       ${where}
       ORDER BY ph.observed_at DESC NULLS LAST
       LIMIT $${params.length - 1} OFFSET $${params.length}`,
      params
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/items/:id
router.get("/:id", async (req, res) => {
  try {
    const { rows: itemRows } = await pool.query(
      "SELECT * FROM items WHERE id = $1",
      [req.params.id]
    );
    if (!itemRows.length) return res.status(404).json({ error: "Not found" });

    const { rows: statsRows } = await pool.query(
      `SELECT
         MIN(unit_price) FILTER (WHERE observed_at > NOW() - INTERVAL '7 days') AS price_7d_low,
         MAX(unit_price) FILTER (WHERE observed_at > NOW() - INTERVAL '7 days') AS price_7d_high,
         AVG(unit_price) FILTER (WHERE observed_at > NOW() - INTERVAL '24 hours')::integer AS price_24h_avg,
         COUNT(*)        FILTER (WHERE observed_at > NOW() - INTERVAL '24 hours') AS volume_24h
       FROM price_history
       WHERE item_id = $1`,
      [req.params.id]
    );

    res.json({ ...itemRows[0], ...statsRows[0] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
