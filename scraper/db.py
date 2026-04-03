"""
PostgreSQL integration for the Dark and Darker market scraper.
Replaces the CSV output from the original marketdatascraper.py.
"""
import json
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

import config


def _connect():
    if not config.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to scraper/.env or set the environment variable."
        )
    return psycopg2.connect(config.DATABASE_URL, sslmode="require")


def start_run():
    """Insert a collector_runs row and return its id."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO collector_runs (started_at, status) VALUES (NOW(), 'running') RETURNING id"
            )
            return cur.fetchone()[0]


def finish_run(run_id, rows_inserted, error_message=None):
    """Update the collector_runs row when a scan completes."""
    status = "error" if error_message else "success"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE collector_runs
                   SET finished_at = NOW(), status = %s,
                       rows_inserted = %s, error_message = %s
                   WHERE id = %s""",
                (status, rows_inserted, error_message, run_id),
            )


def _upsert_item(cur, item_name, rarity, slot, item_type):
    """
    Ensure an items row exists for (name, rarity, slot) and return its UUID.
    Uses INSERT ... ON CONFLICT DO NOTHING then SELECT to avoid a race.
    """
    cur.execute(
        """INSERT INTO items (name, rarity, slot, item_type)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (name, COALESCE(rarity, ''), COALESCE(slot, '')) DO NOTHING""",
        (item_name, rarity or None, slot or None, item_type or None),
    )
    cur.execute(
        """SELECT id FROM items
           WHERE name = %s
             AND COALESCE(rarity, '') = %s
             AND COALESCE(slot,   '') = %s""",
        (item_name, rarity or "", slot or ""),
    )
    row = cur.fetchone()
    return row[0] if row else None


def save_items(items):
    """
    Persist a list of scraped item dicts to PostgreSQL.
    Each dict matches the shape produced by scraper.py:
      item_name, rarity, slot, type, static_attribute, random_attribute,
      expires, price, is_stack, unit_price, quantity, timestamp
    Returns the number of rows inserted.
    """
    if not items:
        return 0

    def _trunc(val, length):
        if val is None:
            return None
        return str(val).strip()[:length] or None

    inserted = 0
    with _connect() as conn:
        with conn.cursor() as cur:
            for item in items:
                item_name = (item.get("item_name") or "").strip()[:255]
                if not item_name:
                    continue

                rarity = _trunc(item.get("rarity"), 32)
                item_id = _upsert_item(
                    cur,
                    item_name,
                    rarity,
                    _trunc(item.get("slot"), 64),
                    _trunc(item.get("type"), 64),
                )
                if item_id is None:
                    continue

                price = item.get("price")
                unit_price = item.get("unit_price")
                if price is None:
                    continue

                # Build attributes JSONB from OCR'd attribute columns
                static_attr = _trunc(item.get("static_attribute"), 500)
                random_attr = _trunc(item.get("random_attribute"), 500)
                attributes = None
                if static_attr or random_attr:
                    attributes = json.dumps({
                        k: v for k, v in {
                            "static": static_attr,
                            "random": random_attr,
                        }.items() if v
                    })

                cur.execute(
                    """INSERT INTO price_history
                         (item_id, price, unit_price, quantity, is_stack,
                          rarity, attributes, expires_at, observed_at, raw_payload)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        item_id,
                        int(price),
                        int(unit_price) if unit_price is not None else None,
                        item.get("quantity") or 1,
                        bool(item.get("is_stack")),
                        rarity,
                        attributes,
                        item.get("expires") or None,
                        item.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                        json.dumps(item),
                    ),
                )
                inserted += 1

    return inserted
