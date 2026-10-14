"""Entrypoint: python inference_api/run.py init-db | serve."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from inference_api import storage  # noqa: E402
from inference_api.server import serve  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("init-db", "serve"))
    args = parser.parse_args()
    if args.action == "init-db":
        storage.initialize()
        print("db_inference_app schema ready")
    else:
        serve()


if __name__ == "__main__":
    main()
