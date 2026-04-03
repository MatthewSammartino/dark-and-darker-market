"""
Marketplace screenshot capture with overlay UI.

A small always-on-top overlay sits in the corner of the screen while you
browse the marketplace. Press F9 to snap the current view. When you're done,
click "Finish & Process" (or press F7) to OCR all queued screenshots and
write them to the database — without going back to the terminal.

Hotkeys:
  F9  — capture current view
  F7  — open the finish dialog (same as clicking Finish & Process)
"""
import json
import os
import queue
import sys
import threading
from datetime import datetime

import keyboard
import pyautogui
import tkinter as tk
from tkinter import messagebox

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")
QUEUE_DIR        = os.path.join(os.path.dirname(__file__), "queue")


# ── Calibration ───────────────────────────────────────────────────────────────

def _load_cal() -> dict:
    try:
        with open(CALIBRATION_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ── Screenshot ────────────────────────────────────────────────────────────────

def _take_screenshot(cal: dict) -> str:
    os.makedirs(QUEUE_DIR, exist_ok=True)
    first_row_y = cal.get("first_row_y", 328)
    row_height  = cal.get("row_height",  60)
    num_rows    = cal.get("num_visible_rows", 10)
    columns     = cal.get("columns", {})
    full_height = first_row_y + row_height * num_rows + 80
    full_width  = max(c["x"] + c["width"] for c in columns.values()) + 50 if columns else 1756
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(QUEUE_DIR, f"full_table_{ts}.png")
    pyautogui.screenshot(region=(0, 0, full_width, full_height)).save(path)
    return path


# ── Overlay window ────────────────────────────────────────────────────────────

class CaptureOverlay:
    def __init__(self, cal: dict):
        self.cal      = cal
        self.count    = 0
        self._msg_q   = queue.Queue()   # thread → UI messages

        self.root = tk.Tk()
        self.root.title("D&D Capture")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        # Position: top-right corner
        sw = self.root.winfo_screenwidth()
        W, H = 300, 130
        self.root.geometry(f"{W}x{H}+{sw - W - 20}+20")

        # Title bar row
        title_row = tk.Frame(self.root, bg="#1a1a2e")
        title_row.pack(fill=tk.X, padx=12, pady=(10, 0))
        tk.Label(title_row, text="D&D Market Capture",
                 bg="#1a1a2e", fg="#c8a050",
                 font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)

        # Count
        self._count_var = tk.StringVar(value="0 screenshots queued")
        tk.Label(self.root, textvariable=self._count_var,
                 bg="#1a1a2e", fg="#e8e0d0",
                 font=("Segoe UI", 10)).pack(pady=(6, 0))

        # Status / progress line
        self._status_var = tk.StringVar(value="F9 to capture  ·  F7 to finish")
        tk.Label(self.root, textvariable=self._status_var,
                 bg="#1a1a2e", fg="#706050",
                 font=("Segoe UI", 8), wraplength=280).pack(pady=(2, 6))

        # Buttons
        btn_row = tk.Frame(self.root, bg="#1a1a2e")
        btn_row.pack()
        self._finish_btn = tk.Button(
            btn_row, text="Finish & Process",
            command=self._on_finish,
            bg="#c8a050", fg="#0f0f0f",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT, padx=10, pady=3,
        )
        self._finish_btn.pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(
            btn_row, text="Quit without processing",
            command=self._on_quit,
            bg="#2a2010", fg="#a09080",
            font=("Segoe UI", 8),
            relief=tk.FLAT, padx=8, pady=3,
        ).pack(side=tk.LEFT)

        # Global hotkeys
        keyboard.add_hotkey("f9", self._on_capture)
        keyboard.add_hotkey("f7", self._on_finish)

        # Poll for messages from processor thread
        self.root.after(200, self._poll_messages)

    # ── hotkey handlers (called from keyboard thread) ─────────────────────────

    def _on_capture(self):
        try:
            path = _take_screenshot(self.cal)
            self.count += 1
            fname = os.path.basename(path)
            self.root.after(0, self._update_count, fname)
        except Exception as e:
            self.root.after(0, self._set_status, f"Error: {e}")

    def _on_finish(self):
        self.root.after(0, self._show_finish_dialog)

    def _on_quit(self):
        keyboard.unhook_all()
        self.root.destroy()
        sys.exit(0)

    # ── UI updates (always on main thread via root.after) ─────────────────────

    def _update_count(self, fname: str):
        self._count_var.set(f"{self.count} screenshot{'s' if self.count != 1 else ''} queued")
        self._set_status(f"Last: {fname}")

    def _set_status(self, msg: str):
        self._status_var.set(msg)

    def _show_finish_dialog(self):
        if self.count == 0:
            messagebox.showinfo(
                "Nothing captured",
                "No screenshots have been taken yet.\nPress F9 to capture or quit.",
                parent=self.root,
            )
            return

        answer = messagebox.askyesno(
            "Process screenshots?",
            f"You've taken {self.count} screenshot{'s' if self.count != 1 else ''}.\n\n"
            "Run OCR and save to database now?",
            parent=self.root,
        )
        if answer:
            self._start_processing()
        else:
            self._on_quit()

    # ── Processing ────────────────────────────────────────────────────────────

    def _start_processing(self):
        """Disable UI and kick off processor in a background thread."""
        self._finish_btn.config(state=tk.DISABLED)
        self._set_status("Loading OCR model…")
        self._count_var.set("Processing — please wait")
        keyboard.unhook_all()
        t = threading.Thread(target=self._run_processor, daemon=True)
        t.start()

    def _run_processor(self):
        """Runs in a background thread. Sends updates via _msg_q."""
        try:
            self._msg_q.put(("status", "Loading OCR model…"))
            # Import here so capture starts fast (no torch on startup)
            import processor
            from scraper import MarketplaceScraper
            scraper = MarketplaceScraper()

            import glob, shutil
            import numpy as np
            from PIL import Image
            import db

            images = sorted(glob.glob(os.path.join(QUEUE_DIR, "full_table_*.png")))
            total_images = len(images)

            if total_images == 0:
                self._msg_q.put(("done", "Queue is empty."))
                return

            self._msg_q.put(("status", f"Processing 0 / {total_images}…"))

            processed_dir = os.path.join(os.path.dirname(__file__), "processed")
            os.makedirs(processed_dir, exist_ok=True)

            run_id = db.start_run()
            total_rows = 0
            error = None

            for i, path in enumerate(images, 1):
                fname = os.path.basename(path)
                self._msg_q.put(("status", f"Processing {i} / {total_images}: {fname}"))
                try:
                    full_table = np.array(Image.open(path))
                    items      = scraper.scrape_marketplace_items(full_table=full_table)
                    inserted   = db.save_items(items)
                    total_rows += inserted
                    shutil.move(path, os.path.join(processed_dir, fname))
                except Exception as e:
                    error = str(e)

            db.finish_run(run_id, total_rows, error)
            self._msg_q.put(("done", f"Done! {total_rows} row{'s' if total_rows != 1 else ''} inserted."))

        except Exception as e:
            self._msg_q.put(("error", str(e)))

    def _poll_messages(self):
        """Called on main thread every 200 ms to apply updates from processor."""
        try:
            while True:
                kind, msg = self._msg_q.get_nowait()
                if kind == "status":
                    self._set_status(msg)
                elif kind == "done":
                    self._count_var.set(msg)
                    self._set_status("All done — you can close this window.")
                    self._finish_btn.config(text="Close", state=tk.NORMAL,
                                            command=self._on_quit)
                elif kind == "error":
                    self._count_var.set("Error during processing")
                    self._set_status(msg)
        except queue.Empty:
            pass
        self.root.after(200, self._poll_messages)

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    cal = _load_cal()
    if not cal:
        print("Warning: no calibration.json found — using default screen dimensions.")
    overlay = CaptureOverlay(cal)
    overlay.run()


if __name__ == "__main__":
    main()
