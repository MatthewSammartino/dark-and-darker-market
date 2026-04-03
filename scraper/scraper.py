"""
OCR pipeline for the Dark and Darker marketplace.
Ported from marketdatascraper.py — uses EasyOCR instead of Tesseract.
Column positions now come from config.py.
"""
import os
import copy
import json
import time
import numpy as np
import cv2
import pyautogui
import keyboard
from datetime import datetime
from PIL import Image

import easyocr

import config

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")


class MarketplaceScraper:
    def __init__(self):
        self.columns = copy.deepcopy(config.COLUMNS)
        self.first_row_y = config.FIRST_ROW_Y
        self.row_height = config.ROW_HEIGHT
        self.num_visible_rows = config.NUM_VISIBLE_ROWS
        self.rarity_colors = config.RARITY_COLORS
        self.debug_folder = config.DEBUG_FOLDER
        self.test_images_folder = os.path.join(os.path.dirname(__file__), "test_images")

        os.makedirs(self.debug_folder, exist_ok=True)
        os.makedirs(self.test_images_folder, exist_ok=True)
        self._load_calibration()
        self.reader = easyocr.Reader(['en'], gpu=False)

    def _load_calibration(self):
        if not os.path.exists(CALIBRATION_FILE):
            return
        with open(CALIBRATION_FILE) as f:
            data = json.load(f)
        self.columns = data.get("columns", self.columns)
        self.first_row_y = data.get("first_row_y", self.first_row_y)
        self.row_height = data.get("row_height", self.row_height)
        self.num_visible_rows = data.get("num_visible_rows", self.num_visible_rows)
        print(f"Loaded calibration from {CALIBRATION_FILE}")

    def _save_calibration(self):
        data = {
            "columns": self.columns,
            "first_row_y": self.first_row_y,
            "row_height": self.row_height,
            "num_visible_rows": self.num_visible_rows,
        }
        with open(CALIBRATION_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Calibration saved to {CALIBRATION_FILE}")

    # ── Screen capture ─────────────────────────────────────────────────────

    def capture_screen_region(self, region):
        x, y, width, height = region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return np.array(screenshot)

    def capture_full_table(self, save_debug=True):
        print("Capturing marketplace table...")
        full_height = self.first_row_y + (self.row_height * self.num_visible_rows) + 80
        rightmost = max(c["x"] + c["width"] for c in self.columns.values())
        full_width = rightmost + 50
        full_table = pyautogui.screenshot(region=(0, 0, full_width, full_height))
        if save_debug:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_table.save(os.path.join(self.test_images_folder, f"full_table_{ts}.png"))
        return np.array(full_table)

    # ── OCR ────────────────────────────────────────────────────────────────

    def extract_text_from_image(self, image, is_numeric=False, debug_name=None):
        if debug_name:
            cv2.imwrite(os.path.join(self.debug_folder, f"{debug_name}_original.png"), image)

        # Upscale so CRAFT can resolve small cell text
        scale = 3
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        results = self.reader.readtext(image, detail=1, text_threshold=0.4, low_text=0.3)
        # Sort left-to-right by bounding box x so multi-word names read in order
        results.sort(key=lambda r: r[0][0][0])
        # results: list of ([bbox], text, confidence)
        text = " ".join(r[1] for r in results if r[2] >= config.OCR_MIN_CONFIDENCE).strip()

        if is_numeric:
            text = "".join(c for c in text if c.isdigit() or c in ".,x")
        else:
            text = text.lstrip('|/\\!@#$%^&*()[]{}<>~`\' \t')
        return text

    def extract_cell_text(self, row_index, column_name, full_table=None):
        x = self.columns[column_name]["x"]
        width = self.columns[column_name]["width"]
        y = self.first_row_y + (row_index * self.row_height)
        # Use full row height — EasyOCR ignores separator lines, unlike Tesseract.
        # Small top pad to avoid bleed from the row above.
        top_pad = 4
        y = y + top_pad
        height = self.row_height - top_pad

        if full_table is not None:
            cell_image = full_table[y:y+height, x:x+width]
        else:
            cell_image = self.capture_screen_region((x, y, width, height))

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_name = f"row{row_index}_{column_name}_{ts}"
        is_numeric = column_name in ("price", "quantity")
        text = self.extract_text_from_image(cell_image, is_numeric, debug_name)
        return text, cell_image

    # ── Rarity / price helpers ─────────────────────────────────────────────

    def detect_rarity_from_color(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 50, 50])
        upper = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        if cv2.countNonZero(mask) == 0:
            return None
        mean_color = cv2.mean(image, mask=mask)[:3]
        closest, min_dist = None, float("inf")
        for rarity, color in self.rarity_colors.items():
            dist = np.sqrt(sum((a - b) ** 2 for a, b in zip(mean_color, color)))
            if dist < min_dist:
                min_dist = dist
                closest = rarity
        return closest

    def extract_price_value(self, price_text):
        if not price_text:
            return None
        # D&D prices are whole numbers; strip both . and , (OCR may read
        # "7,000" as "7.000" depending on font/rendering)
        clean = "".join(c for c in price_text if c.isdigit())
        try:
            return float(clean)
        except ValueError:
            return None

    def extract_quantity(self, quantity_text):
        if not quantity_text or "x" not in quantity_text.lower():
            return None
        # Format: "103.3x3" — left side is the game's display unit price (total/qty,
        # often non-integer), right side is the stack count.
        # We only take the count here; unit_price is computed from the actual total.
        parts = quantity_text.lower().split("x")
        if len(parts) != 2:
            return None
        try:
            quantity = int("".join(c for c in parts[1] if c.isdigit()))
            return quantity
        except ValueError:
            return None

    # ── Main scrape ────────────────────────────────────────────────────────

    def scrape_marketplace_items(self, save_images=True):
        print("Scraping marketplace items...")
        full_table = self.capture_full_table(save_debug=save_images)
        items = []

        for row_index in range(self.num_visible_rows):
            try:
                item_name_text, item_name_img = self.extract_cell_text(row_index, "item_name", full_table)
                if not item_name_text:
                    continue

                rarity_text,      rarity_img = self.extract_cell_text(row_index, "rarity",           full_table)
                slot_text,        _          = self.extract_cell_text(row_index, "slot",              full_table)
                type_text,        _          = self.extract_cell_text(row_index, "type",              full_table)
                static_attr_text, _          = self.extract_cell_text(row_index, "static_attribute",  full_table)
                random_attr_text, _          = self.extract_cell_text(row_index, "random_attribute",  full_table)
                expires_text,     _          = self.extract_cell_text(row_index, "expires",           full_table)
                price_text,       _          = self.extract_cell_text(row_index, "price",             full_table)
                quantity_text,    _          = self.extract_cell_text(row_index, "quantity",          full_table)

                price_value = self.extract_price_value(price_text)
                quantity = self.extract_quantity(quantity_text)
                # Compute unit price from total rather than the OCR'd display value
                # (the game shows a rounded decimal like "103.3" which isn't reliable)
                unit_price = (price_value / quantity) if (price_value and quantity and quantity > 1) else None

                if not rarity_text or rarity_text not in self.rarity_colors:
                    detected = self.detect_rarity_from_color(item_name_img)
                    if detected:
                        rarity_text = detected

                item = {
                    "item_name":       item_name_text,
                    "rarity":          rarity_text,
                    "slot":            slot_text,
                    "type":            type_text,
                    "static_attribute": static_attr_text,
                    "random_attribute": random_attr_text,
                    "expires":         expires_text,
                    "price":           price_value,
                    "price_text":      price_text,
                    "is_stack":        bool(quantity and quantity > 1),
                    "unit_price":      unit_price,
                    "quantity":        quantity,
                    "timestamp":       datetime.now().isoformat(),
                }
                print(f"  Row {row_index}: {item_name_text} — {rarity_text} — {price_text}")
                items.append(item)

            except Exception as e:
                print(f"  Error processing row {row_index}: {e}")

        return items

    def click_refresh_button(self):
        pyautogui.click(config.REFRESH_BUTTON_X, config.REFRESH_BUTTON_Y)
        print("Clicked refresh button")
        time.sleep(2)

    # ── Calibration helpers ────────────────────────────────────────────────

    def wait_for_trigger_key(self, key="space"):
        print(f"Press '{key}' when ready...")
        keyboard.wait(key)
        print(f"'{key}' pressed. Continuing...")
        time.sleep(0.5)

    def capture_test_screenshot(self, wait_for_key=True):
        if wait_for_key:
            print("Switch to your game window.")
            self.wait_for_trigger_key("space")
        full_table = self.capture_full_table(save_debug=True)
        print("Test image saved to debug_images/")
        return full_table

    def calibrate_table_layout(self, wait_for_key=True):
        from calibration_ui import run_calibration
        result = run_calibration(countdown=5 if wait_for_key else 0)
        if result:
            self.columns = result["columns"]
            self.first_row_y = result["first_row_y"]
            self.row_height = result["row_height"]
            self.num_visible_rows = result["num_visible_rows"]
