"""Entry point — run this and pick calibrate or watch."""


def show_menu():
    print()
    print("=" * 56)
    print(" Antigravity Auto-Submit")
    print(" Auto-clicks the Submit/Allow button in Antigravity IDE")
    print("=" * 56)
    print("1) Calibrate button location")
    print("   (do this first, and again any time the button moves)")
    print("2) Start watching (auto-clicks the button when it appears)")
    print("3) Quit")
    print()


def main():
    while True:
        show_menu()
        choice = input("Choose 1, 2, or 3: ").strip()

        if choice == "1":
            import calibrate
            calibrate.main()
            print("\nCalibration finished. Back to the menu...")
        elif choice == "2":
            import watch
            watch.main()
            print("\nStopped watching. Back to the menu...")
        elif choice == "3":
            break
        else:
            print("\nPlease enter 1, 2, or 3.")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()