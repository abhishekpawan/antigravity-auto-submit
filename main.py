"""Entry point — run this and pick calibrate or watch."""
import sys


def main():
    print("=" * 56)
    print(" Antigravity Auto-Submit")
    print(" Auto-clicks the Submit/Allow button in Antigravity IDE")
    print("=" * 56)
    print("1) Calibrate button location")
    print("   (do this first, and again any time the button moves)")
    print("2) Start watching (auto-clicks the button when it appears)")
    print()
    choice = input("Choose 1 or 2: ").strip()

    if choice == "1":
        import calibrate
        calibrate.main()
    elif choice == "2":
        import watch
        watch.main()
    else:
        print("Please enter 1 or 2.")
        sys.exit(1)


if __name__ == "__main__":
    main()
