"""Entry point — run this and pick calibrate or watch."""
import json

import common


def calibrated_region():
    """Returns the saved (left, top, width, height) region if a valid
    calibration exists, or None otherwise. Used to make the menu aware of
    whether setup has already been done, instead of asking every time."""
    if not common.CONFIG_PATH.exists():
        return None
    try:
        data = json.loads(common.CONFIG_PATH.read_text())
        region = data.get("region")
        return tuple(region) if region else None
    except (json.JSONDecodeError, OSError):
        return None


def confirmed(prompt):
    return input(prompt).strip().lower() in ("", "y", "yes")


def show_menu(region):
    print()
    print("=" * 56)
    print(" Antigravity Auto-Submit")
    print(" Auto-clicks the Submit/Allow button in Antigravity IDE")
    print("=" * 56)
    if region:
        print(f"✓ Calibrated — watching region {region}")
    else:
        print("✗ Not calibrated yet — start with option 1")
    print()
    print("1) Calibrate button location" + ("" if region else "  (do this first)"))
    print("2) Start watching (auto-clicks the button when it appears)")
    print("3) Quit")
    print()


def run_watch(region):
    if region and not confirmed(f"Using calibrated region {region} — start watching? [Y/n]: "):
        print("Back to the menu...")
        return
    import watch
    watch.main()
    print("\nStopped watching. Back to the menu...")


def main():
    while True:
        region = calibrated_region()
        show_menu(region)
        choice = input("Choose 1, 2, or 3: ").strip()

        if choice == "1":
            import calibrate
            calibrate.main()
            new_region = calibrated_region()
            if new_region and new_region != region:
                print(f"\nCalibration saved for region {new_region}.")
                if confirmed("Start watching now? [Y/n]: "):
                    run_watch(new_region)
                else:
                    print("Back to the menu...")
            else:
                print("\nBack to the menu...")
        elif choice == "2":
            run_watch(region)
        elif choice == "3":
            break
        else:
            print("\nPlease enter 1, 2, or 3.")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()