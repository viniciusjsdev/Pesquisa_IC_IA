"""Versioned code identities, independent of the candidate and chosen routes."""
import hashlib
from pathlib import Path

VERSION = 'runtime_files_v2_recursive'
PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]


def identity(paths=None):
    if paths is None:
        paths = [*(path for path in PACKAGE.rglob('*')
                   if path.suffix in {'.py', '.json'} and '__pycache__' not in path.parts),
                 ROOT / 'BancoModeloUse/dw/fixed_queries.py',
                 ROOT / 'inference_api/requirements.txt']
        lock = ROOT / 'inference_api/requirements.lock'
        if lock.exists(): paths.append(lock)
    return {'version': VERSION, 'files': {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)}}
