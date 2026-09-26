# Antigravity Auto-Submit

**A zero-configuration, screen-watching auto-clicker for Antigravity IDE's recurring permission/Submit dialog — no Chrome Debug Mode, no browser extension, no DOM hooking required.**

If you use **Google's Antigravity IDE** and keep getting a **"Run command?" / "Allow?" / Submit** approval prompt for nearly every agent step — even after setting Tool Permission to **always-proceed**, adding the command to your `permissions.allow` list, and confirming the workspace is trusted — you're not alone. This is a [known, actively-discussed bug](#related-reports) that several other tools also try to fix. This one takes a different, deliberately low-tech approach: it watches your screen for the button's color and clicks it, with no integration into Antigravity itself.

## Why this exists

There are already more sophisticated community fixes for this issue — [**AntiGravity AutoAccept**](https://github.com/yazanbaker94/AntiGravity-AutoAccept) and **Anti-Remote-Pro** — which hook into Antigravity directly via Chrome DevTools Protocol (CDP) for more precise detection than pixel-matching. They require enabling **Chrome Debug Mode** as a setup step, which didn't work reliably for me, so I built this instead: zero setup beyond a one-time calibration, no debug flags, no browser internals.

## How it works

1. **Calibrate once**: run the tool, hover your mouse over the button (don't click), and press `F8`. It samples the color under your cursor, auto-detects the button's full boundary using a flood fill, and saves an actual snapshot image of that exact region — no manual coordinate entry.
2. **Watch**: it polls that small screen region roughly once a second and compares the live content against the saved snapshot. It only clicks when the region is a close visual match — not just a similar color — which is what lets it tell the real button apart from something else nearby that happens to share its color (see [Limitations](#limitations)).

This works across any monitor arrangement — a single laptop screen, or multiple external monitors, including a monitor positioned to the *left* of your primary display (negative screen coordinates). That case matters more than it sounds: the naive approach (`pyautogui.screenshot()`) silently fails to capture anything on a monitor at negative coordinates on Windows. This tool uses `PIL.ImageGrab(..., all_screens=True)` instead, which handles it correctly. See [Technical notes](#technical-notes).

## ⚠️ Safety note — please read

This tool automatically approves whatever action is behind that button, without a human looking at it first. That's the entire point, but it also means:

- **Don't leave it running unattended** while your agent might be about to do something you haven't scoped or reviewed — a destructive file operation, a risky one-off command, anything outside routine, low-stakes steps you'd have clicked through anyway.
- It has no idea *what* it's approving — only that a button of a certain color appeared in a certain spot.
- **Stop it anytime** with `Ctrl+C` in the terminal, or drag your mouse into any screen corner to trigger an emergency abort mid-click (this is `pyautogui`'s built-in failsafe).

If you wouldn't leave a real assistant unsupervised for a given task, don't leave this running for it either.

## Installation

### Option A — Prebuilt Windows executable (no Python needed)
Download `AutoSubmit.exe` from the [Releases](../../releases) page.

> **Your browser and/or Windows will very likely warn you before letting you keep this file.** That's expected for any small, unsigned, community-built `.exe` — it's a reputation check (Chrome/Edge Safe Browsing, Windows SmartScreen), not a sign that anything is actually wrong with this one. It fades as more people download it without incident; a paid code-signing certificate would suppress it immediately, but isn't worth it for a project this size yet.
>
> - **Browser download warning** (e.g. "This file isn't commonly downloaded" or "may be dangerous"): click the arrow / "⋮" next to the blocked download and choose **Keep** / **Download anyway** / **Keep dangerous file**.
> - **Windows SmartScreen** ("Windows protected your PC"): click **More info**, then **Run anyway**.
>
> If you'd rather not click through either of those, you have two more-transparent options: read the [build workflow](.github/workflows/build-windows-exe.yml) and inspect the public build logs on the [Releases](../../releases) page to see exactly how each `.exe` was produced from this source, or skip the prebuilt binary entirely and use Option B below.

### Option B — Run from source (Windows / macOS / Linux)
```
git clone https://github.com/abhishekpawan/antigravity-auto-submit.git
cd antigravity-auto-submit
pip install -r requirements.txt
python main.py
```
> If you're on a very new Python release, `Pillow` may need a moment to catch up with a compatible build — if `pip install -r requirements.txt` reports Pillow already "satisfied" but importing it fails, run `pip install Pillow` directly and try again.
>
> **Only tested on Windows so far.** The code aims to be cross-platform, but macOS/Linux haven't been verified yet — in particular, the `keyboard` library (used for the `F8`/`Esc` calibration hotkeys) typically needs elevated permissions on Linux (`sudo`) and has its own quirks on macOS (Accessibility permissions). If you try it on either, a report or PR in [Issues](../../issues) is very welcome.

## Usage

1. Run the tool (`python main.py` or `AutoSubmit.exe`) and choose **1) Calibrate**.
2. Hover over the button in your IDE, press `F8`. A small window confirms it was captured, with the detected region and a snapshot saved to `button_template.png`.
3. Choose **2) Start watching** from the menu.
4. Leave it running in the background while you work — it clicks the button whenever the region visually matches your calibrated snapshot.
5. If your IDE window moves, resizes, or the button's theme/appearance changes, just recalibrate (steps 1–2) to refresh the snapshot.

## Technical notes

- **Screen capture** uses `PIL.ImageGrab(bbox=..., all_screens=True)` rather than `pyautogui.screenshot()`. The latter does not reliably capture monitors placed at negative coordinates in a multi-monitor Windows setup — a real bug encountered and root-caused during development of this tool.
- **Region sizing** uses a flood fill from the calibrated point across matching-colored pixels, so the watched region auto-sizes to the actual button rather than requiring a manually specified box — this is what makes calibration work the same way regardless of screen size or layout.
- **Detection** compares the live screen region against the snapshot image taken during calibration (`button_template.png`), using average per-pixel RGB difference as a similarity score (`common.image_similarity`), and only clicks above `SIMILARITY_THRESHOLD` (92% by default, in `watch.py`). This is closer to "does this look like the button I calibrated" than "is this the right color," so a different button that happens to share the color and screen slot — e.g. Antigravity's chat "Send" button, which turns the same blue as the approval "Submit" button once you start typing, in nearly the same spot — scores a clearly lower match and is correctly left unclicked.
- **Config** (region + path to the snapshot image) is stored locally in `config.json`, alongside `button_template.png`. Both are git-ignored since they're specific to your own screen setup.

## Limitations

- **The IDE window must actually be visible on screen.** This tool only ever looks at what's rendered to the screen — it has no access to Antigravity's internal state. If the Antigravity window is **minimized**, or **another window is covering** the exact screen region where the button would appear, the watcher can't see it and won't click it, even though the approval dialog is genuinely sitting there waiting. Keep the IDE window visible (a second monitor works well for this) while the watcher is running.
- **Theme-sensitive**: if Antigravity's theme or accent color changes (e.g. switching light/dark mode), the saved snapshot goes stale and you'll need to recalibrate.
- **Still not infallible**: if two different buttons are genuinely pixel-identical in that exact screen region (same icon, same text, same color, same position), image comparison can't tell them apart either — nothing short of reading the IDE's actual UI state could. In practice this is rare, since most visually distinct actions render at least a different icon or label.
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