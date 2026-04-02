const express = require("express");
const cors = require("cors");
const path = require("path");

const runMigrations = require("./db/migrate");
const pool = require("./db/pool");
const itemsRouter = require("./routes/items");
const pricesRouter = require("./routes/prices");

const app = express();
const PORT = process.env.PORT || 3001;

app.set("trust proxy", 1);
app.use(cors({ origin: true }));
app.use(express.json());

app.use(express.static(path.join(__dirname, "dist")));

// ── Routes ─────────────────────────────────────────────────────────────────
app.use("/api/items", itemsRouter);
app.use("/api/prices", pricesRouter);

app.get("/api/collector/status", async (req, res) => {
  try {
    const { rows } = await pool.query(
      "SELECT * FROM collector_runs ORDER BY started_at DESC LIMIT 10"
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

// ── SPA fallback ────────────────────────────────────────────────────────────
app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "dist", "index.html"));
});

// ── Start ───────────────────────────────────────────────────────────────────
async function start() {
  try {
    await runMigrations();
    app.listen(PORT, "0.0.0.0", () => {
      console.log(`Dark & Darker Market API running on port ${PORT}`);
    });
  } catch (err) {
    console.error("Startup error:", err.message);
    process.exit(1);
  }
}

start();

module.exports = app;
