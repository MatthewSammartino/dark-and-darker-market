const express = require("express");
const router = express.Router();
const pool = require("../db/pool");

const INTERVALS = { "1d": "1 day", "7d": "7 days", "30d": "30 days", all: null };
const BUCKETS   = { "1h": 1, "6h": 6, "1d": 24 };

// GET /api/prices/trending
router.get("/trending", async (req, res) => {
  try {
    const { rows } = await pool.query(
      `SELECT i.id, i.name, i.slot, i.item_type,
              COUNT(ph.id) AS volume_24h,
              AVG(ph.unit_price)::integer AS avg_price,
              MIN(ph.unit_price) AS low_price,
              MAX(ph.unit_price) AS high_price
       FROM items i
       JOIN price_history ph ON ph.item_id = i.id
       WHERE ph.observed_at > NOW() - INTERVAL '24 hours'
       GROUP BY i.id
       ORDER BY volume_24h DESC
       LIMIT 20`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/prices/latest
router.get("/latest", async (req, res) => {
  const limit = Math.min(Number(req.query.limit) || 20, 100);
  try {
    const { rows } = await pool.query(
      `SELECT DISTINCT ON (ph.item_id)
              i.id, i.name, i.slot, i.item_type,
              ph.price, ph.unit_price, ph.rarity, ph.observed_at
       FROM price_history ph
       JOIN items i ON i.id = ph.item_id
       ORDER BY ph.item_id, ph.observed_at DESC
       LIMIT $1`,
      [limit]
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/prices/:itemId?range=7d&bucket=6h
router.get("/:itemId", async (req, res) => {
  const { range = "7d", bucket = "6h" } = req.query;
  const intervalHours = BUCKETS[bucket] ?? 6;
  const intervalStr = INTERVALS[range];

  const params = [req.params.itemId];
  const timeFilter = intervalStr
    ? `AND observed_at > NOW() - INTERVAL '${intervalStr}'`
    : "";

  try {
    const { rows } = await pool.query(
      `SELECT
         date_trunc('hour', observed_at) -
           INTERVAL '1 hour' * (EXTRACT(HOUR FROM observed_at)::int % $2) AS bucket,
         MIN(COALESCE(unit_price, price)) AS low,
         MAX(COALESCE(unit_price, price)) AS high,
         AVG(COALESCE(unit_price, price))::integer AS avg,
         COUNT(*) AS volume
       FROM price_history
       WHERE item_id = $1 ${timeFilter}
       GROUP BY 1
       ORDER BY 1 ASC`,
      [params[0], intervalHours]
    );
    res.json({ itemId: req.params.itemId, range, bucket, data: rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
