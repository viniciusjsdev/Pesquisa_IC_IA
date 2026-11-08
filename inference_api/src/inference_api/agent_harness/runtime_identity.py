"""Versioned code identities, independent of the candidate and chosen routes."""
import hashlib
from pathlib import Path

VERSION = 'runtime_files_v1'
PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]


def identity(paths=None):
    if paths is None:
        paths = [*PACKAGE.glob('*.py'), *PACKAGE.joinpath('agent_harness').glob('*.py'),
                 *PACKAGE.joinpath('agent_harness').glob('*.json'),
                 *PACKAGE.joinpath('model_service').glob('*.py'),
                 *(path for group in ('api', 'identity', 'executions', 'data_access', 'evidence', 'persistence')
                   for path in PACKAGE.joinpath(group).glob('*.py')),
                 ROOT / 'BancoModeloUse/dw/fixed_queries.py']
    return {'version': VERSION, 'files': {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)}}
