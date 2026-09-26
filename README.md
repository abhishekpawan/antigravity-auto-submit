# Antigravity Auto-Submit

**A zero-configuration, screen-watching auto-clicker for Antigravity IDE's recurring permission/Submit dialog — no Chrome Debug Mode, no browser extension, no DOM hooking required.**

If you use **Google's Antigravity IDE** and keep getting a **"Run command?" / "Allow?" / Submit** approval prompt for nearly every agent step — even after setting Tool Permission to **always-proceed**, adding the command to your `permissions.allow` list, and confirming the workspace is trusted — you're not alone. This is a [known, actively-discussed bug](#related-reports) that several other tools also try to fix. This one takes a different, deliberately low-tech approach: it watches your screen for the button's color and clicks it, with no integration into Antigravity itself.

## Is this the right tool for you?

There are already more sophisticated community fixes for this issue — [**AntiGravity AutoAccept**](https://github.com/yazanbaker94/AntiGravity-AutoAccept) and **Anti-Remote-Pro**, which hook into Antigravity via its native VS Code commands and Chrome DevTools Protocol (CDP). Those are more precise (no reliance on pixel colors, no theme sensitivity), but they require enabling **Chrome Debug Mode** as a setup step, which is an extra bit of configuration that can be fiddly, and didn't work reliably for everyone (including the author of this repo).

**Use this tool if:**
- You want something that works without touching debug flags or browser internals.
- The CDP-based extensions didn't work for you, or felt like more setup than you wanted.
- You're comfortable with the trade-off: this clicks based on color and position, so it needs a one-time calibration and can, in principle, misfire if something else on screen matches.

**Use one of the CDP-based tools instead if:**
- You want a more precise, screen-layout-independent fix and don't mind the Debug Mode setup.

## How it works

1. **Calibrate once**: run the tool, hover your mouse over the button (don't click), and press `F8`. It samples the color under your cursor and auto-detects the button's full boundary using a flood fill — no manual coordinate entry.
2. **Watch**: it polls that small screen region roughly once a second. When the button's color appears there, it clicks the center of it.

This works across any monitor arrangement — a single laptop screen, or multiple external monitors, including a monitor positioned to the *left* of your primary display (negative screen coordinates). That case matters more than it sounds: the naive approach (`pyautogui.screenshot()`) silently fails to capture anything on a monitor at negative coordinates on Windows. This tool uses `PIL.ImageGrab(..., all_screens=True)` instead, which handles it correctly. See [Technical notes](#technical-notes).

## ⚠️ Safety note — please read

This tool automatically approves whatever action is behind that button, without a human looking at it first. That's the entire point, but it also means:

- **Don't leave it running unattended** while your agent might be about to do something you haven't scoped or reviewed — a destructive file operation, a risky one-off command, anything outside routine, low-stakes steps you'd have clicked through anyway.
- It has no idea *what* it's approving — only that a button of a certain color appeared in a certain spot.
- **Stop it anytime** with `Ctrl+C` in the terminal, or drag your mouse into any screen corner to trigger an emergency abort mid-click (this is `pyautogui`'s built-in failsafe).

If you wouldn't leave a real assistant unsupervised for a given task, don't leave this running for it either.

## Installation

### Option A — Prebuilt Windows executable (no Python needed)
Download `AutoSubmit.exe` from the [Releases](../../releases) page and run it directly.

### Option B — Run from source (Windows / macOS / Linux)
```
git clone https://github.com/abhishekpawan/antigravity-auto-submit.git
cd antigravity-auto-submit
pip install -r requirements.txt
python main.py
```
> If you're on a very new Python release, `Pillow` may need a moment to catch up with a compatible build — if `pip install -r requirements.txt` reports Pillow already "satisfied" but importing it fails, run `pip install Pillow` directly and try again.

## Usage

1. Run the tool (`python main.py` or `AutoSubmit.exe`) and choose **1) Calibrate**.
2. Hover over the button in your IDE, press `F8`. A small window confirms it was captured, with the detected color and region.
3. Run the tool again and choose **2) Start watching**.
4. Leave it running in the background while you work — it clicks the button whenever it appears.
5. If your IDE window moves, resizes, or the button's theme/color changes, just recalibrate (steps 1–2).

## Technical notes

- **Screen capture** uses `PIL.ImageGrab(bbox=..., all_screens=True)` rather than `pyautogui.screenshot()`. The latter does not reliably capture monitors placed at negative coordinates in a multi-monitor Windows setup — a real bug encountered and root-caused during development of this tool.
- **Button detection** uses a flood fill from the calibrated point across matching-colored pixels, so the watched region auto-sizes to the actual button rather than requiring a manually specified box — this is what makes calibration work the same way regardless of screen size or layout.
- **Config** (calibrated color + region) is stored locally in `config.json`, which is git-ignored since it's specific to your own screen setup.

## Limitations

- **Theme-sensitive**: if Antigravity's theme or accent color changes (e.g. switching light/dark mode), you'll need to recalibrate.
- **Color-collision risk**: if something else in the watched region happens to share the button's color, it could misfire — the flood-fill detection keeps the watched box tight around just the button to minimize this.
- **Not affiliated with or endorsed by Google or the Antigravity team** — this is an independent, community workaround for a bug others have also reported publicly.

## Related reports

This isn't an isolated report — for reference:
- Google AI Developers Forum: ["Antigravity always asks for permission"](https://discuss.ai.google.dev/t/antigravity-always-asks-for-permission/173114)
- Google AI Developers Forum: ["\[Bug\] Antigravity still ask permission even command is already on allowed list"](https://discuss.ai.google.dev/t/bug-antigravity-still-ask-permission-even-command-is-already-on-allowed-list/118636)
- GitHub issue: [google-antigravity/antigravity-cli#565](https://github.com/google-antigravity/antigravity-cli/issues/565)

## Contributing

Issues and PRs welcome — especially if you hit a different multi-monitor/DPI edge case, or want to add support for other IDEs with the same "won't stop asking for permission" pattern.

## License

MIT — see [LICENSE](LICENSE).
