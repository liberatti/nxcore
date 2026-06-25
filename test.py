#!/usr/bin/env python3
import sys
import traceback
import importlib
from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    tests_dir = base_dir / "nxcore" / "tests"
    if not tests_dir.exists():
        print(f"Error: tests directory not found at {tests_dir}", file=sys.stderr)
        sys.exit(1)

    test_files = sorted(tests_dir.glob("test_*.py"))
    if not test_files:
        print("No test files found.", file=sys.stderr)
        sys.exit(0)

    failed = False

    for test_file in test_files:
        module_name = f"nxcore.tests.{test_file.stem}"
        print("=" * 60)
        print(f"Loading test module: {module_name}")
        print("=" * 60)

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"[ERROR] Failed to import {module_name}: {e}", file=sys.stderr)
            traceback.print_exc()
            failed = True
            continue

        test_functions = [
            (name, func) for name, func in vars(module).items()
            if name.startswith("test_") and callable(func)
        ]

        if not test_functions:
            print(f"No test functions starting with 'test_' found in {module_name}.\n")
            continue

        for name, func in test_functions:
            print(f"Running: {name}")
            try:
                func()
                print(f"[PASS] {name}\n")
            except Exception as e:
                print(f"[FAIL] {name}: {e}\n", file=sys.stderr)
                traceback.print_exc()
                failed = True

    if failed:
        print("Some tests failed.")
        sys.exit(1)
    else:
        print("All tests completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
