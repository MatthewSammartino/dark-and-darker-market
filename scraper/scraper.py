"""
OCR pipeline for the Dark and Darker marketplace.
Ported from marketdatascraper.py — core OCR logic is unchanged.
Column positions and Tesseract path now come from config.py.
"""
import os
import copy
import time
import numpy as np
import cv2
import pyautogui
import pytesseract
import keyboard
from datetime import datetime
from PIL import Image

import config

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH


class MarketplaceScraper:
    def __init__(self):
        self.columns = copy.deepcopy(config.COLUMNS)
        self.first_row_y = config.FIRST_ROW_Y
        self.row_height = config.ROW_HEIGHT
        self.num_visible_rows = config.NUM_VISIBLE_ROWS
        self.rarity_colors = config.RARITY_COLORS
        self.debug_folder = config.DEBUG_FOLDER

        os.makedirs(self.debug_folder, exist_ok=True)

    # ── Screen capture ─────────────────────────────────────────────────────

    def capture_screen_region(self, region):
        x, y, width, height = region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return np.array(screenshot)

    def capture_full_table(self, save_debug=True):
        print("Capturing marketplace table...")
        full_height = self.first_row_y + (self.row_height * self.num_visible_rows) + 10
        full_width = 1400
        full_table = pyautogui.screenshot(region=(0, 0, full_width, full_height))
        if save_debug:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_table.save(os.path.join(self.debug_folder, f"full_table_{ts}.png"))
        return np.array(full_table)

    # ── OCR ────────────────────────────────────────────────────────────────

    def extract_text_from_image(self, image, is_numeric=False, debug_name=None):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        if debug_name:
            cv2.imwrite(os.path.join(self.debug_folder, f"{debug_name}_original.png"), image)
            cv2.imwrite(os.path.join(self.debug_folder, f"{debug_name}_processed.png"), thresh)

        custom_config = "--psm 7 --oem 3"
        if is_numeric:
            custom_config += ' -c tessedit_char_whitelist="0123456789,.x"'
        return pytesseract.image_to_string(thresh, config=custom_config).strip()

    def extract_cell_text(self, row_index, column_name, full_table=None):
        x = self.columns[column_name]["x"]
        width = self.columns[column_name]["width"]
        y = self.first_row_y + (row_index * self.row_height)
        height = self.row_height - 5

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
        clean = "".join(c for c in price_text if c.isdigit() or c in ".,")\
                  .replace(",", "")
        try:
            return float(clean)
        except ValueError:
            return None

    def extract_quantity(self, quantity_text):
        if not quantity_text or "x" not in quantity_text.lower():
            return None, None
        parts = quantity_text.lower().split("x")
        if len(parts) != 2:
            return None, None
        try:
            unit_price = float(
                "".join(c for c in parts[0] if c.isdigit() or c in ".,").replace(",", "")
            )
            quantity = int("".join(c for c in parts[1] if c.isdigit()))
            return unit_price, quantity
        except ValueError:
            return None, None

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
                unit_price, quantity = self.extract_quantity(quantity_text)

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
                    "is_stack":        bool(unit_price and quantity),
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
        print("Table Layout Calibration")
        print("------------------------")
        if wait_for_key:
            print("Switch to your game window.")
            self.wait_for_trigger_key("space")

        print("\nMove mouse to the top of the FIRST item row and press 'C'")
        keyboard.wait("c")
        self.first_row_y = pyautogui.position().y
        print(f"First row Y = {self.first_row_y}")

        print("\nFor each column: move to LEFT edge and press 'L', then RIGHT edge and press 'R'")
        for col_name in self.columns:
            print(f"\n  Column: {col_name}")
            print("  Left edge → press 'L'")
            keyboard.wait("l")
            left_x = pyautogui.position().x
            print("  Right edge → press 'R'")
            keyboard.wait("r")
            right_x = pyautogui.position().x
            self.columns[col_name]["x"] = left_x
            self.columns[col_name]["width"] = right_x - left_x
            print(f"  Set: x={left_x}, width={right_x - left_x}")

        print("\nMove to top of FIRST row → press 'T'")
        keyboard.wait("t")
        top_y = pyautogui.position().y
        print("Move to top of SECOND row → press 'B'")
        keyboard.wait("b")
        bottom_y = pyautogui.position().y
        self.row_height = bottom_y - top_y
        print(f"Row height = {self.row_height}")

        try:
            n = int(input("How many rows are visible? (default 10): ") or "10")
            if n > 0:
                self.num_visible_rows = n
        except ValueError:
            pass

        print("\nCalibration complete:")
        print(f"  first_row_y={self.first_row_y}, row_height={self.row_height}, rows={self.num_visible_rows}")
        for col_name, dims in self.columns.items():
            print(f"  {col_name}: x={dims['x']}, width={dims['width']}")
