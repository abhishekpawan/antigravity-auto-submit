"""
Shared screen-capture helpers used by calibrate.py and watch.py.

Uses PIL's ImageGrab with all_screens=True rather than pyautogui's
screenshot() wrapper, because pyautogui's screenshot does not reliably
capture monitors positioned at negative coordinates in a multi-monitor
Windows setup (confirmed during development of this tool — see README
"Technical notes"). ImageGrab(all_screens=True) handles this correctly.
"""
from PIL import ImageChops, ImageGrab, ImageStat

SAMPLE_RADIUS = 4         # px around the cursor to average when sampling a color
SEARCH_HALF_SIZE = 250    # how far out (in px) to look for a button's edges from a click point
COLOR_TOLERANCE = 25      # how close an RGB value must be to count as a match
PADDING = 6               # extra px added around an auto-detected button region


def grab(bbox):
    """Screenshot an absolute-screen-coordinate box (left, top, right, bottom)."""
    return ImageGrab.grab(bbox=bbox, all_screens=True)


def color_close(c1, c2, tol=COLOR_TOLERANCE):
    return all(abs(a - b) <= tol for a, b in zip(c1, c2))


def image_similarity(img_a, img_b):
    """
    Return a 0.0-1.0 score for how visually alike two same-region screenshots
    are (1.0 = pixel-identical), by averaging the per-pixel RGB difference.

    This is what actually identifies "the calibrated button, specifically" —
    rather than just "something the same color" — since two different UI
    elements that happen to share a color (e.g. an IDE's approval "Submit"
    button and an unrelated "Send" button that turns the same blue) will
    still differ in their icon, text, or shape and so score a clearly lower
    similarity than a real repeat sighting of the same button.
    """
    a = img_a.convert("RGB")
    b = img_b.convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    mean_diff = sum(ImageStat.Stat(diff).mean) / 3   # average over R, G, B (each 0-255)
    return 1.0 - (mean_diff / 255.0)


def sample_color(x, y, radius=SAMPLE_RADIUS):
    """Average the color in a small box around (x, y) to reduce sensitivity to
    a single anti-aliased pixel."""
    img = grab((x - radius, y - radius, x + radius + 1, y + radius + 1))
    px = list(img.getdata())
    n = len(px)
    return tuple(sum(p[i] for p in px) // n for i in range(3))


def detect_region(cx, cy, target_color, half_size=SEARCH_HALF_SIZE,
                   tol=COLOR_TOLERANCE, padding=PADDING):
    """
    Flood-fill outward from (cx, cy) across pixels matching target_color, and
    return the bounding box of that connected region as
    (left, top, width, height) in absolute screen coordinates.

    Returns None if the starting point doesn't actually match target_color
    (e.g. the cursor drifted off the button between sampling and detecting).
    """
    left, top = cx - half_size, cy - half_size
    img = grab((left, top, cx + half_size, cy + half_size))
    pixels = img.load()
    w, h = img.size
    sx, sy = cx - left, cy - top

    if not (0 <= sx < w and 0 <= sy < h) or not color_close(pixels[sx, sy][:3], target_color, tol):
        return None

    visited = bytearray(w * h)
    stack = [(sx, sy)]
    visited[sy * w + sx] = 1
    min_x = max_x = sx
    min_y = max_y = sy

    while stack:
        x, y = stack.pop()
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[ny * w + nx]:
                if color_close(pixels[nx, ny][:3], target_color, tol):
                    visited[ny * w + nx] = 1
                    stack.append((nx, ny))

    return (
        left + min_x - padding,
        top + min_y - padding,
        (max_x - min_x) + 1 + padding * 2,
        (max_y - min_y) + 1 + padding * 2,
    )