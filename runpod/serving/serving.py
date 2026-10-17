"""Validate scientific artifacts and build a static vLLM launch without a shell."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from threading import Thread
from uuid import uuid4


REPO = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("manifest.json")
ALIASES = {
    "ft-finqa-a": ("A", "FT-FinQA"),
    "ft-failure-a": ("A", "FT-Failure"),
    "ft-hibrido-a": ("A", "FT-Híbrido"),
    "ft-finqa-b": ("B", "FT-FinQA"),
    "ft-failure-b": ("B", "FT-Failure"),
    "ft-hibrido-b": ("B", "FT-Híbrido"),
}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def manifest_digest(manifest: dict) -> str:
    """Hash JSON values canonically so CRLF conversion does not change identity."""
    data = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def load_manifest(path: Path = MANIFEST) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Serving manifest must be an object")
    return manifest


def _path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError("Artifact path must be a string")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not relative.startswith("FineTuning/results/experiments/"):
        raise ValueError("Artifact path must stay under FineTuning/results/experiments")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Artifact path escapes the checkout")
    return resolved


def validate(manifest: dict, root: Path = REPO) -> dict:
    """Check the six declared artifacts and their scientific catalog entries."""
    if set(manifest) != {"schema_version", "base_model", "base_alias", "base_revision", "adapters"}:
        raise ValueError("Unexpected serving manifest fields")
    if (manifest["schema_version"] != 1 or
            manifest["base_model"] != "Qwen/Qwen2.5-7B-Instruct" or
            manifest["base_alias"] != "qwen-base" or
            manifest["base_revision"] is not None):
        raise ValueError("Unexpected base model or versioned base revision")
    rendered = json.dumps(manifest, ensure_ascii=False).lower()
    if re.search(r'"(?:api[_-]?key|password|secret|token|authorization)"\s*:', rendered) or \
            "bearer " in rendered or "://user:" in rendered:
        raise ValueError("Serving manifest must not contain credentials")
    adapters = manifest["adapters"]
    if not isinstance(adapters, list) or len(adapters) != 6:
        raise ValueError("Serving manifest requires exactly six adapters")
    aliases = [item.get("alias") for item in adapters if isinstance(item, dict)]
    if len(aliases) != 6 or set(aliases) != set(ALIASES):
        raise ValueError("Adapter aliases are missing or duplicated")
    catalog_path = root / "FineTuning/docs/modelos_disponiveis.md"
    catalog = catalog_path.read_text(encoding="utf-8")
    checked = []
    for item in adapters:
        if set(item) != {"alias", "battery", "adapter_dir", "run_manifest", "run",
                         "weight_sha256", "config_sha256"}:
            raise ValueError("Unexpected adapter manifest fields")
        alias = item["alias"]
        battery, label = ALIASES[alias]
        if item["battery"] != battery:
            raise ValueError(f"Battery mismatch for {alias}")
        for key in ("weight_sha256", "config_sha256"):
            if not isinstance(item[key], str) or not SHA256.fullmatch(item[key]):
                raise ValueError(f"Invalid {key} for {alias}")
        directory = _path(root, item["adapter_dir"])
        run_path = _path(root, item["run_manifest"])
        if directory.name != "adapter" or run_path != directory.parent / "meta/run_manifest.json":
            raise ValueError(f"Run path mismatch for {alias}")
        if not isinstance(item["run"], str) or not directory.parent.name.endswith(item["run"]):
            raise ValueError(f"Run identity mismatch for {alias}")
        catalog_row = f"| {battery} / {label} | `{item['weight_sha256']}` | `{item['config_sha256']}` |"
        if f"`{item['adapter_dir']}/`" not in catalog or catalog_row not in catalog:
            raise ValueError(f"Scientific catalog mismatch for {alias}")
        weight = directory / "adapter_model.safetensors"
        config = directory / "adapter_config.json"
        for path, expected in ((weight, item["weight_sha256"]), (config, item["config_sha256"])):
            if not path.is_file() or _digest(path) != expected:
                raise ValueError(f"Missing or invalid {path.name} for {alias}")
        adapter_config = json.loads(config.read_text(encoding="utf-8"))
        if (adapter_config.get("base_model_name_or_path") != manifest["base_model"] or
                adapter_config.get("peft_type") != "LORA"):
            raise ValueError(f"Incompatible base or PEFT type for {alias}")
        run = json.loads(run_path.read_text(encoding="utf-8"))
        if (run.get("run_name") != item["run"] or
                run.get("resolved_config_snapshot", {}).get("model", {}).get("base_model") !=
                manifest["base_model"]):
            raise ValueError(f"Run provenance mismatch for {alias}")
        checked.append(alias)
    return {"manifest_sha256": manifest_digest(manifest), "aliases": [manifest["base_alias"], *checked],
            "adapter_count": len(checked)}


def command(manifest: dict, root: Path, base_revision: str) -> list[str]:
    if not isinstance(base_revision, str) or not REVISION.fullmatch(base_revision):
        raise ValueError("An exact 40-character lowercase base commit is required")
    validate(manifest, root)
    argv = [
        "vllm", "serve", manifest["base_model"],
        "--revision", base_revision,
        "--tokenizer-revision", base_revision,
        "--served-model-name", manifest["base_alias"],
        "--host", "127.0.0.1", "--port", "8001",
        "--max-model-len", "4096",
        "--enable-auto-tool-choice", "--tool-call-parser", "hermes",
        "--enable-lora", "--max-lora-rank", "8", "--max-cpu-loras", "6",
        "--lora-modules",
    ]
    for item in manifest["adapters"]:
        argv.append(json.dumps({
            "name": item["alias"],
            "path": str(_path(root, item["adapter_dir"])),
            "base_model_name": manifest["base_model"],
        }, separators=(",", ":")))
    return argv


def start(manifest: dict, root: Path, revision: str) -> None:
    argv = command(manifest, root, revision)
    aliases = [manifest["base_alias"], *(item["alias"] for item in manifest["adapters"])]
    token = os.environ.get("INFERENCE_VLLM_TOKEN", "")
    if len(token) < 32:
        raise ValueError("INFERENCE_VLLM_TOKEN must contain at least 32 characters")
    if not shutil.which("vllm"):
        raise ValueError("vLLM executable is unavailable")
    import gateway
    session = {
        "schema_version": 1,
        "session_id": str(uuid4()),
        "manifest_sha256": manifest_digest(manifest),
        "base_revision": revision,
        "vllm_version": importlib.metadata.version("vllm"),
        "aliases": aliases,
    }
    local_dir = Path(__file__).with_name(".local")
    local_dir.mkdir(mode=0o700, exist_ok=True)
    session_path = local_dir / "session.json"
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    try:
        session_path.chmod(0o600)
    except OSError:
        pass
    server = gateway.make_server(token, session)
    process = subprocess.Popen(argv, cwd=root)
    try:
        Thread(target=lambda: (process.wait(), server.shutdown()), daemon=True).start()
        server.serve_forever()
    finally:
        server.server_close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "command", "start"))
    parser.add_argument("--checkout", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--base-revision")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.action == "validate":
            print(json.dumps(validate(manifest, args.checkout), indent=2))
        elif args.action == "command":
            print(json.dumps(command(manifest, args.checkout, args.base_revision), indent=2))
        else:
            start(manifest, args.checkout, args.base_revision)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Serving preflight failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
