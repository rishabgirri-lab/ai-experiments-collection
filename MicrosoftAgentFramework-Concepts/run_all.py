"""
run_all.py — convenience smoke runner.

Runs every example in order. Examples 13–16 need NO API key (pure code) and will
always run; the rest call Groq and need GROQ_API_KEY to be set.

Usage:
    python run_all.py            # run everything (LLM ones skipped if no key)
    python run_all.py 03 08      # run only the examples whose number you list
"""

import os
import subprocess
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent / "examples"
OFFLINE = {"13", "14", "15", "16"}  # run without an API key


def main() -> None:
    wanted = set(sys.argv[1:])
    files = sorted(p for p in EXAMPLES_DIR.glob("[0-9][0-9]_*.py"))
    have_key = bool(os.environ.get("GROQ_API_KEY"))

    for path in files:
        num = path.name[:2]
        if wanted and num not in wanted:
            continue
        if num not in OFFLINE and not have_key:
            print(f"\n=== {path.name}: SKIPPED (set GROQ_API_KEY to run) ===")
            continue
        print(f"\n=== Running {path.name} ===")
        result = subprocess.run([sys.executable, str(path)], cwd=str(EXAMPLES_DIR))
        if result.returncode != 0:
            print(f"!!! {path.name} exited with code {result.returncode}")


if __name__ == "__main__":
    main()
