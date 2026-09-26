"""
Watches the calibrated screen region for the calibrated button color,
and clicks it automatically whenever it appears.

Run calibrate.py first (or again, any time the button's position or
appearance changes).
"""
import json
import time
from pathlib import Path

import pyautogui

import common

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
MIN_MATCHING_PIXELS = 15   # how many matching pixels = "button is visible"
POLL_INTERVAL = 1.0        # seconds between checks when idle
CLICK_COOLDOWN = 4.0       # seconds to wait after a click before checking again


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit("No config.json found yet. Run calibrate.py first.")
    data = json.loads(CONFIG_PATH.read_text())
    return tuple(data["color"]), tuple(data["region"])


def find_button(color, region):
    left, top, w, h = region
    shot = common.grab((left, top, left + w, top + h))
    pixels = shot.load()
    sw, sh = shot.size
    matches = []
    for y in range(0, sh, 2):          # step by 2 to keep the scan fast
        for x in range(0, sw, 2):
            if common.color_close(pixels[x, y][:3], color):
                matches.append((x, y))
    if len(matches) < MIN_MATCHING_PIXELS:
        return None
    avg_x = sum(p[0] for p in matches) / len(matches)
    avg_y = sum(p[1] for p in matches) / len(matches)
    return (left + avg_x, top + avg_y)


def main():
    color, region = load_config()
    print(f"Watching region {region} for color {color}.")
    print("Ctrl+C to stop. Drag your mouse to any screen corner to abort mid-click.\n")
    try:
        while True:
            spot = find_button(color, region)
            if spot:
                print(f"Button detected — clicking at ({spot[0]:.0f}, {spot[1]:.0f})")
                pyautogui.click(*spot)
                time.sleep(CLICK_COOLDOWN)
            else:
                time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
