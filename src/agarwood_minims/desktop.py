"""Entry point for the standalone Windows application."""
import multiprocessing
import sys


def main():
    multiprocessing.freeze_support()
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="AgarwoodMiniMS desktop diagnostics")
        parser.add_argument("--self-test", required=True, metavar="NEW_OUTPUT_DIRECTORY")
        args = parser.parse_args()
        from .selftest import run
        run(args.self_test)
        return
    from .gui import launch
    launch()


if __name__ == "__main__":
    main()
