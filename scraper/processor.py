"""
Offline OCR processor — reads all screenshots from queue/, runs the full
OCR + database pipeline on each, then moves them to processed/.

Usage:
  python processor.py

Run this after a capture session. EasyOCR is loaded once and all queued
images are processed in timestamp order. Processed images are moved to
processed/ so they won't be picked up again on the next run.
"""
import glob
import os
import shutil

import numpy as np
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

import db
from scraper import MarketplaceScraper

QUEUE_DIR     = os.path.join(os.path.dirname(__file__), "queue")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "processed")


def process_queue(scraper: MarketplaceScraper) -> int:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    images = sorted(glob.glob(os.path.join(QUEUE_DIR, "full_table_*.png")))
    if not images:
        print("Queue is empty — nothing to process.")
        return 0

    print(f"Found {len(images)} image(s) to process.\n")
    run_id = db.start_run()
    total  = 0
    error  = None

    for path in images:
        fname = os.path.basename(path)
        print(f"→ {fname}")
        try:
            full_table = np.array(Image.open(path))
            items      = scraper.scrape_marketplace_items(full_table=full_table)
            inserted   = db.save_items(items)
            total     += inserted
            print(f"   {inserted} row(s) inserted")
            shutil.move(path, os.path.join(PROCESSED_DIR, fname))
        except Exception as e:
            print(f"   ERROR: {e}")
            error = str(e)

    db.finish_run(run_id, total, error)
    print(f"\nDone — {total} total row(s) inserted.")
    return total


def main():
    print("Initialising OCR model…")
    scraper = MarketplaceScraper()
    os.makedirs(QUEUE_DIR, exist_ok=True)
    process_queue(scraper)


if __name__ == "__main__":
    main()
