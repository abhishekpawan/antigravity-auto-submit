"""
GUI calibration tool.

Run it, keep the small window visible (it stays on top of everything
else), then move your mouse over the button you want auto-clicked —
don't click it — and press F8. It samples the color under your cursor,
auto-detects the full extent of the button by flood-filling matching
pixels outward from that point, and shows a zoomed-in preview of exactly
what it captured. Nothing is saved yet at this point — check the preview
actually looks like your button, then press F9 to confirm and save. If
you captured the wrong thing (e.g. pressed F8 while hovering over some
other part of the screen by mistake), just hover over the real button
and press F8 again — it overwrites the preview, nothing is written to
disk until you explicitly confirm with F9.

The saved snapshot is what makes detection reliable later: watch.py
compares the live screen against this exact image, rather than just
checking for "something roughly this color" — so an unrelated button
that happens to share the same color and screen position (e.g. a chat
"Send" button that turns the same blue as an approval "Submit" button)
won't falsely trigger a click, since its icon/text/shape won't match
the calibrated snapshot.

Press Esc at any time to quit without saving.

No manual pixel-coordinate math needed — this works the same way
whether the button is on your laptop screen or on a third external
monitor positioned anywhere relative to your primary display.
"""
import json
import queue
import tkinter as tk

import keyboard
import pyautogui
from PIL import Image, ImageTk

import common
from common import CONFIG_PATH, TEMPLATE_PATH

events: "queue.Queue" = queue.Queue()

PREVIEW_MAX_DIM = 280   # px; captured region is scaled up to roughly this size in the preview


def do_capture():
    x, y = pyautogui.position()
    color = common.sample_color(x, y)
    region = common.detect_region(x, y, color)
    events.put(("captured", color, region))


def do_confirm():
    events.put(("confirm",))


def main():
    # F9 (not Enter) confirms the save — Enter is far too easy to trigger by
    # accident from some other window (e.g. sending a chat message), since
    # these hotkeys are global and fire regardless of which window has focus.
    keyboard.add_hotkey("f8", do_capture)
    keyboard.add_hotkey("f9", do_confirm)
    keyboard.add_hotkey("esc", lambda: events.put(("cancel",)))

    root = tk.Tk()
    root.title("Auto-Submit Calibration")
    root.attributes("-topmost", True)
    root.geometry("+80+80")   # position only; size auto-fits the content below
    root.resizable(False, False)

    tk.Label(
        root,
        text="Hover your mouse over the button\n(don't click it), then press F8.",
        font=("Segoe UI", 12),
        pady=15,
    ).pack()
    status = tk.Label(
        root,
        text="Waiting for F8   •   Esc to quit",
        font=("Segoe UI", 10),
        fg="#555555",
        wraplength=420,
        justify="center",
    )
    status.pack(padx=20)
    preview_label = tk.Label(root)
    preview_label.pack(pady=(6, 15))

    # Holds the most recently captured (but not yet saved) snapshot, plus a
    # reference to its PhotoImage — Tkinter needs that reference kept alive
    # or the image is garbage-collected and the preview goes blank.
    pending = {"color": None, "region": None, "snapshot": None, "photo": None}

    # Tracks the currently-scheduled root.after() job so it can be cancelled
    # cleanly if the window is closed via the OS close (X) button — without
    # this, a callback left scheduled against an already-destroyed window
    # causes Tcl to raise 'invalid command name ... ("after" script)'.
    pending_job = {"id": None}

    def schedule(delay_ms, func):
        pending_job["id"] = root.after(delay_ms, func)

    def show_preview(snapshot):
        w, h = snapshot.size
        scale = max(1, min(4, PREVIEW_MAX_DIM // max(w, h)))
        display_img = snapshot.resize((w * scale, h * scale), resample=Image.Resampling.NEAREST)
        photo = ImageTk.PhotoImage(display_img)
        pending["photo"] = photo   # keep a reference alive, or Tk drops the image
        preview_label.config(image=photo)

    def clear_preview():
        pending.update(color=None, region=None, snapshot=None, photo=None)
        preview_label.config(image="")

    def poll():
        try:
            event = events.get_nowait()
        except queue.Empty:
            schedule(100, poll)
            return

        kind = event[0]

        if kind == "captured":
            _, color, region = event
            if region is None:
                clear_preview()
                status.config(
                    text="No solid button color found there — move the mouse\n"
                         "fully onto the button's colored area and press F8 again.",
                    fg="#b00000",
                )
                schedule(100, poll)
                return
            left, top, w, h = region
            snapshot = common.grab((left, top, left + w, top + h))
            pending.update(color=color, region=region, snapshot=snapshot)
            show_preview(snapshot)
            status.config(
                text="Does this look like your Submit button?\n"
                     "Press F9 to save it, or hover elsewhere and press F8 to retry.",
                fg="#8a6d00",
            )
            schedule(100, poll)
            return

        if kind == "confirm":
            if pending["region"] is None:
                status.config(
                    text="Nothing captured yet — hover over the button and press F8 first.",
                    fg="#b00000",
                )
                schedule(100, poll)
                return
            region, color, snapshot = pending["region"], pending["color"], pending["snapshot"]
            snapshot.save(TEMPLATE_PATH)
            CONFIG_PATH.write_text(
                json.dumps(
                    {"color": list(color), "region": list(region), "template": TEMPLATE_PATH.name},
                    indent=2,
                )
            )
            status.config(text=f"Saved!  region={region}\nSnapshot written to {TEMPLATE_PATH.name}", fg="#008000")
            schedule(2000, root.destroy)
            return

        # "cancel"
        root.destroy()

    def on_close():
        if pending_job["id"] is not None:
            try:
                root.after_cancel(pending_job["id"])
            except tk.TclError:
                pass
        keyboard.unhook_all()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    schedule(100, poll)
    root.mainloop()
    keyboard.unhook_all()


if __name__ == "__main__":
    main()