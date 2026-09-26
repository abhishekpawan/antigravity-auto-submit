"""
GUI calibration tool.

Run it, keep the small window visible (it stays on top of everything
else), then move your mouse over the button you want auto-clicked —
don't click it — and press F8. It samples the color under your cursor,
auto-detects the full extent of the button by flood-filling matching
pixels outward from that point, saves a snapshot image of exactly that
region, and records both in config.json next to this script.

The saved snapshot is what makes detection reliable: watch.py compares
the live screen against this exact image later, rather than just
checking for "something roughly this color" — so an unrelated button
that happens to share the same color and screen position (e.g. a chat
"Send" button that turns the same blue as an approval "Submit" button)
won't falsely trigger a click, since its icon/text/shape won't match
the calibrated snapshot.

Press Esc at any time to cancel without saving.

No manual pixel-coordinate math needed — this works the same way
whether the button is on your laptop screen or on a third external
monitor positioned anywhere relative to your primary display.
"""
import json
import queue
import tkinter as tk
from pathlib import Path

import keyboard
import pyautogui

import common

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
TEMPLATE_PATH = Path(__file__).resolve().parent / "button_template.png"
events: "queue.Queue" = queue.Queue()


def do_capture():
    x, y = pyautogui.position()
    color = common.sample_color(x, y)
    region = common.detect_region(x, y, color)
    events.put(("captured", color, region))


def main():
    keyboard.add_hotkey("f8", do_capture)
    keyboard.add_hotkey("esc", lambda: events.put(("cancel",)))

    root = tk.Tk()
    root.title("Auto-Submit Calibration")
    root.attributes("-topmost", True)
    root.geometry("460x170+80+80")
    root.resizable(False, False)

    tk.Label(
        root,
        text="Hover your mouse over the button\n(don't click it), then press F8.",
        font=("Segoe UI", 12),
        pady=15,
    ).pack()
    status = tk.Label(
        root,
        text="Waiting for F8   •   Esc to cancel",
        font=("Segoe UI", 10),
        fg="#555555",
        wraplength=420,
        justify="center",
    )
    status.pack()

    def poll():
        try:
            event = events.get_nowait()
        except queue.Empty:
            root.after(100, poll)
            return
        if event[0] == "captured":
            _, color, region = event
            if region is None:
                status.config(
                    text="No solid button color found there — move the mouse\n"
                         "fully onto the button's colored area and press F8 again.",
                    fg="#b00000",
                )
                root.after(100, poll)
                return
            left, top, w, h = region
            snapshot = common.grab((left, top, left + w, top + h))
            snapshot.save(TEMPLATE_PATH)
            CONFIG_PATH.write_text(
                json.dumps(
                    {"color": list(color), "region": list(region), "template": TEMPLATE_PATH.name},
                    indent=2,
                )
            )
            status.config(text=f"Saved!  region={region}\nSnapshot written to {TEMPLATE_PATH.name}", fg="#008000")
            root.after(2500, root.destroy)
        else:
            root.destroy()

    root.after(100, poll)
    root.mainloop()
    keyboard.unhook_all()


if __name__ == "__main__":
    main()