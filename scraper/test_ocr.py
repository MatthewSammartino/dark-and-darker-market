"""
OCR test script — runs the full pipeline against a saved full_table screenshot.
Use this to tune OCR settings without needing the game open.

Usage:
    python test_ocr.py                          # uses most recent full_table image
    python test_ocr.py test_images/full_table_20260401_213559.png
"""
import sys
import os
import glob
import numpy as np
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

from scraper import MarketplaceScraper


def load_image(path):
    img = Image.open(path)
    return np.array(img)


def main():
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Find the most recent full_table image
        pattern = os.path.join("test_images", "full_table_*.png")
        matches = sorted(glob.glob(pattern))
        if not matches:
            print("No full_table images found. Run option 2 (test screenshot) first.")
            sys.exit(1)
        image_path = matches[-1]

    print(f"Using image: {image_path}\n")
    full_table = load_image(image_path)

    scraper = MarketplaceScraper()

    for row_index in range(scraper.num_visible_rows):
        try:
            item_name, _ = scraper.extract_cell_text(row_index, "item_name", full_table)
            if not item_name:
                continue

            rarity,   _ = scraper.extract_cell_text(row_index, "rarity",    full_table)
            slot,     _ = scraper.extract_cell_text(row_index, "slot",      full_table)
            type_,    _ = scraper.extract_cell_text(row_index, "type",      full_table)
            price,    _ = scraper.extract_cell_text(row_index, "price",     full_table)
            quantity, _ = scraper.extract_cell_text(row_index, "quantity",  full_table)

            price_val = scraper.extract_price_value(price)
            qty = scraper.extract_quantity(quantity)
            unit_price = (price_val / qty) if (price_val and qty and qty > 1) else None

            stack_info = ""
            if qty and qty > 1:
                stack_info = f"  [{qty}x @ {unit_price:.1f} each = {price_val} total]"

            print(f"Row {row_index:2d}: {item_name!r:40s} | {rarity!r:12s} | price={price!r} → {price_val}{stack_info}")
            if quantity:
                print(f"         quantity raw: {quantity!r}")

        except Exception as e:
            print(f"Row {row_index:2d}: ERROR — {e}")


if __name__ == "__main__":
    main()
