"""
Interactive calibration UI for the Dark and Darker marketplace scraper.

Workflow
--------
1. A small always-on-top countdown window gives you time to switch to the game.
2. A full screenshot is taken automatically.
3. The screenshot is displayed in a resizable window.
4. You draw one box per step by clicking and dragging:
     - First: draw around the FIRST ROW (full width, full row height).
     - Then:  draw around one cell in each column (only left/right edges matter).
5. A small dialog asks how many rows are visible.
6. Everything is saved to calibration.json.
"""
import json
import os
import tkinter as tk
from tkinter import simpledialog
import numpy as np
import pyautogui
from PIL import Image, ImageTk

import config

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")

# One distinct colour per step
_PALETTE = [
    "#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF", "#FF922B",
    "#CC5DE8", "#20C997", "#F06595", "#74C0FC", "#A9E34B",
    "#FFA94D", "#63E6BE",
]

_STEPS = (
    [{"key": "_row", "label": 'Draw a box around the FIRST ROW (full width, full height of one row)'}]
    + [{"key": col, "label": f'Draw a box around any cell in the "{col}" column'} for col in config.COLUMNS]
    + [{"key": "_refresh", "label": 'Draw a box around the REFRESH button'}]
)


# ── Countdown window ──────────────────────────────────────────────────────────

def _show_countdown(seconds: int = 5):
    """Show a small always-on-top countdown, then destroy it."""
    root = tk.Tk()
    root.title("Calibration")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#1a1a2e")

    # Centre on screen
    w, h = 340, 100
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    lbl = tk.Label(
        root,
        text="",
        font=("Segoe UI", 14, "bold"),
        bg="#1a1a2e",
        fg="white",
        pady=10,
    )
    lbl.pack(fill=tk.BOTH, expand=True)

    remaining = [seconds]

    def _tick():
        if remaining[0] <= 0:
            root.destroy()
            return
        lbl.config(text=f"Switch to the game window…\nTaking screenshot in {remaining[0]}s")
        remaining[0] -= 1
        root.after(1000, _tick)

    _tick()
    root.mainloop()


# ── Main calibration window ───────────────────────────────────────────────────

class _CalibrationWindow:
    """Displays a screenshot and walks the user through drawing calibration boxes."""

    def __init__(self, screenshot: np.ndarray):
        self._raw = screenshot          # RGB numpy array
        self._scale = 1.0
        self._drawn: dict = {}          # step key → (x1, y1, x2, y2) in screen coords
        self._start = None
        self._drag_id = None
        self._step = 0
        self._cancelled = False

    # ── public ───────────────────────────────────────────────────────────

    def run(self) -> dict | None:
        """Open the window, block until done, return calibration dict or None."""
        self._root = tk.Tk()
        self._root.title("Marketplace Calibration — draw boxes to set column positions")
        self._root.configure(bg="#1a1a2e")
        self._root.attributes("-topmost", True)

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        ih, iw = self._raw.shape[:2]
        self._scale = min((sw - 20) / iw, (sh - 140) / ih)
        cw = int(iw * self._scale)
        ch = int(ih * self._scale)
        self._root.geometry(f"{cw}x{ch + 100}+{(sw - cw) // 2}+{(sh - ch - 100) // 2}")

        # Instruction bar
        self._lbl = tk.Label(
            self._root,
            text="",
            wraplength=cw - 20,
            justify="center",
            font=("Segoe UI", 12, "bold"),
            bg="#1a1a2e",
            fg="white",
            pady=8,
        )
        self._lbl.pack(fill=tk.X)

        # Screenshot canvas
        img = Image.fromarray(self._raw).resize((cw, ch), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)
        self._canvas = tk.Canvas(
            self._root, width=cw, height=ch,
            cursor="crosshair", highlightthickness=0,
        )
        self._canvas.pack()
        self._canvas.create_image(0, 0, anchor=tk.NW, image=self._photo)

        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._root.bind("<Escape>", lambda _e: self._cancel())

        self._set_step(0)
        self._root.mainloop()

        if self._cancelled:
            return None
        return self._build_result()

    # ── step management ──────────────────────────────────────────────────

    def _set_step(self, idx: int):
        self._step = idx
        if idx >= len(_STEPS):
            self._ask_row_count()
            return
        total = len(_STEPS)
        step = _STEPS[idx]
        color = _PALETTE[idx % len(_PALETTE)]
        self._lbl.config(
            text=f"Step {idx + 1} of {total}:  {step['label']}",
            fg=color,
        )

    def _ask_row_count(self):
        """Ask for the number of visible rows, then close."""
        # Bring root to front for the dialog
        self._root.lift()
        n = simpledialog.askinteger(
            "Row count",
            "How many item rows are visible in the marketplace?\n(default 10)",
            parent=self._root,
            initialvalue=10,
            minvalue=1,
            maxvalue=30,
        )
        self._num_rows = n if n else 10
        self._root.destroy()

    def _cancel(self):
        self._cancelled = True
        self._root.destroy()

    # ── mouse events ─────────────────────────────────────────────────────

    def _on_press(self, event):
        self._start = (event.x, event.y)
        if self._drag_id:
            self._canvas.delete(self._drag_id)
            self._drag_id = None

    def _on_drag(self, event):
        if not self._start:
            return
        if self._drag_id:
            self._canvas.delete(self._drag_id)
        color = _PALETTE[self._step % len(_PALETTE)]
        self._drag_id = self._canvas.create_rectangle(
            self._start[0], self._start[1], event.x, event.y,
            outline=color, width=2, dash=(6, 3),
        )

    def _on_release(self, event):
        if not self._start:
            return
        x1c = min(self._start[0], event.x)
        y1c = min(self._start[1], event.y)
        x2c = max(self._start[0], event.x)
        y2c = max(self._start[1], event.y)

        if abs(x2c - x1c) < 5 or abs(y2c - y1c) < 5:
            return  # accidental click — ignore

        if self._drag_id:
            self._canvas.delete(self._drag_id)
            self._drag_id = None

        # Save in screen coordinates
        key = _STEPS[self._step]["key"]
        color = _PALETTE[self._step % len(_PALETTE)]
        self._drawn[key] = (
            int(x1c / self._scale), int(y1c / self._scale),
            int(x2c / self._scale), int(y2c / self._scale),
        )

        # Draw permanent box + label
        self._canvas.create_rectangle(x1c, y1c, x2c, y2c, outline=color, width=2)
        self._canvas.create_text(
            x1c + 4, y1c + 4, anchor=tk.NW,
            text=key, fill=color,
            font=("Segoe UI", 9, "bold"),
        )

        self._start = None
        self._set_step(self._step + 1)

    # ── result ───────────────────────────────────────────────────────────

    def _build_result(self) -> dict:
        row_box = self._drawn.get("_row")
        if not row_box:
            return {}

        x1r, y1r, x2r, y2r = row_box
        first_row_y = y1r
        row_height = max(y2r - y1r, 1)

        # Load current calibration so undrawn columns keep their existing values
        current_columns = dict(config.COLUMNS)
        try:
            with open(CALIBRATION_FILE) as f:
                current_columns = json.load(f).get("columns", current_columns)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        columns = {}
        for col in config.COLUMNS:
            box = self._drawn.get(col)
            if box:
                bx1, _, bx2, _ = box
                columns[col] = {"x": bx1, "width": max(bx2 - bx1, 1)}
            else:
                columns[col] = current_columns.get(col, dict(config.COLUMNS[col]))

        # Refresh button — use center of drawn box
        refresh_box = self._drawn.get("_refresh")
        if refresh_box:
            rx1, ry1, rx2, ry2 = refresh_box
            refresh_x = (rx1 + rx2) // 2
            refresh_y = (ry1 + ry2) // 2
        else:
            refresh_x = config.REFRESH_BUTTON_X
            refresh_y = config.REFRESH_BUTTON_Y

        return {
            "columns": columns,
            "first_row_y": first_row_y,
            "row_height": row_height,
            "num_visible_rows": getattr(self, "_num_rows", 10),
            "refresh_button_x": refresh_x,
            "refresh_button_y": refresh_y,
        }


# ── Public entry point ────────────────────────────────────────────────────────

def run_calibration(countdown: int = 5) -> dict | None:
    """
    Show countdown → take screenshot → open calibration UI → save result.
    Returns the saved calibration dict, or None if the user cancelled.
    """
    _show_countdown(countdown)

    print("Taking screenshot…")
    screenshot = np.array(pyautogui.screenshot())

    win = _CalibrationWindow(screenshot)
    result = win.run()

    if result is None:
        print("Calibration cancelled.")
        return None

    with open(CALIBRATION_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Calibration saved to {CALIBRATION_FILE}")
    print(f"  first_row_y={result['first_row_y']}, row_height={result['row_height']}, "
          f"rows={result['num_visible_rows']}")
    for col, dims in result["columns"].items():
        print(f"  {col}: x={dims['x']}, width={dims['width']}")

    return result
