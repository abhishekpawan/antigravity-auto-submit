"""
Watches the calibrated screen region and clicks it automatically whenever
its content visually matches the button snapshot taken during calibration.

Run calibrate.py first (or again, any time the button's position or
appearance changes).

Why image comparison instead of just color: some IDEs reuse the same
screen slot for more than one button depending on context (e.g. an
approval "Submit" button and a chat "Send" button that turns the exact
same blue once you start typing). Matching on color alone can't tell
those apart, so this instead compares the live screen content against
the exact snapshot saved during calibration and only clicks when it's a
close visual match — not just a similar color.
"""
import json
import time

import pyautogui
from PIL import Image

import common
from common import CONFIG_PATH

# How closely the live region must match the calibrated snapshot to count
# as "the button is showing" (1.0 = pixel-identical). Lower this a little
# if genuine appearances of the button aren't being detected; raise it if
# something else is triggering false matches.
SIMILARITY_THRESHOLD = 0.92

POLL_INTERVAL = 1.0        # seconds between checks when idle
CLICK_COOLDOWN = 4.0       # seconds to wait after a click before checking again


def load_config():
    """
    Raises FileNotFoundError (never SystemExit) on any missing/invalid
    calibration data — the caller decides how to handle it, rather than the
    whole program exiting out from under a menu loop.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "No calibration found yet. Choose \"1) Calibrate button location\" from the menu first."
        )
    data = json.loads(CONFIG_PATH.read_text())
    region = tuple(data["region"])
    template_name = data.get("template")
    if not template_name:
        raise FileNotFoundError(
            "This saved calibration is from an older version of the tool (no button snapshot "
            "recorded). Please recalibrate — choose \"1) Calibrate button location\"."
        )
    template_path = CONFIG_PATH.parent / template_name
    if not template_path.exists():
        raise FileNotFoundError(
            f"Expected snapshot file {template_path} is missing. Please recalibrate."
        )
    return region, Image.open(template_path)


def button_is_showing(region, template):
    left, top, w, h = region
    current = common.grab((left, top, left + w, top + h))
    return common.image_similarity(current, template) >= SIMILARITY_THRESHOLD


def main():
    try:
        region, template = load_config()
    except FileNotFoundError as e:
        print(str(e))
        return
    left, top, w, h = region
    cx, cy = left + w / 2, top + h / 2

    print(f"Watching region {region} for a visual match against the calibrated snapshot.")
    print(f"Similarity threshold: {SIMILARITY_THRESHOLD:.0%}")
    print("Ctrl+C to stop. Drag your mouse to any screen corner to abort mid-click.\n")
    try:
        while True:
            if button_is_showing(region, template):
                print(f"Button match confirmed — clicking at ({cx:.0f}, {cy:.0f})")
                pyautogui.click(cx, cy)
                time.sleep(CLICK_COOLDOWN)
            else:
                time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()