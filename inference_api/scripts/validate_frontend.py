"""Run the checked-in frontend tools with Node, without requiring npm on PATH."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess


FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
COMMANDS = {
    "typecheck": ("typescript/bin/tsc", "-b", "--pretty", "false"),
    "lint": ("eslint/bin/eslint.js", "."),
    "test": ("vitest/vitest.mjs", "run"),
    "build": ("vite/bin/vite.js", "build"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", choices=sorted(COMMANDS))
    args = parser.parse_args()
    node = shutil.which("node")
    if node is None:
        parser.error("Node 24 is required on PATH")
    script, *arguments = COMMANDS[args.gate]
    target = FRONTEND / "node_modules" / script
    if not target.is_file():
        parser.error(f"Local frontend dependency missing: {script}")
    return subprocess.run([node, str(target), *arguments], cwd=FRONTEND,
                          timeout=180, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
