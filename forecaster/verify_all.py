#!/usr/bin/env python3
import subprocess
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TESTS = [
    ("audio", ROOT / "tests" / "test_audio_synoptyk.py"),
    ("synoptyk", ROOT / "tests" / "test_synoptyk.py"),
    ("edge", ROOT / "tests" / "test_edge_cases.py"),
]

def run_test(name, path):
    print(f"\n=== [{name.upper()}] ===")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(path)],
            capture_output=True,
            text=True
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip())
            return False
        return True
    except Exception as e:
        print(f"ERROR running {name}: {e}")
        return False

def main():
    print("=== FULL PIPELINE VERIFICATION ===")
    results = {}

    for name, path in TESTS:
        ok = run_test(name, path)
        results[name] = ok

    print("\n=== SUMMARY ===")
    for name, ok in results.items():
        print(f"{name:10} : {'PASS' if ok else 'FAIL'}")

    if all(results.values()):
        print("\nALL TESTS PASS ✔️")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()
