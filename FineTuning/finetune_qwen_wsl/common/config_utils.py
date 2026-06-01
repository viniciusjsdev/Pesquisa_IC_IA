import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def nested_get(data: Dict[str, Any], key: str, default=None):
    cur = data
    for part in key.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def load_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f'Config não encontrada: {p}')
    if p.suffix.lower() in {'.yaml', '.yml'}:
        if yaml is None:
            raise RuntimeError('PyYAML não instalado. Instale `PyYAML>=6.0` para usar configs YAML.')
        with p.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f'Config inválida em {p}: esperado objeto YAML na raiz')
        return data
    if p.suffix.lower() == '.json':
        return json.loads(p.read_text(encoding='utf-8'))
    raise ValueError(f'Formato de config não suportado: {p.suffix}')

def save_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    rows = []
    with Path(path).open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def save_jsonl(path: str | Path, rows: Iterable[Dict[str, Any]]) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    with p.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

def count_jsonl(path: str | Path) -> int:
    c = 0
    with Path(path).open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                c += 1
    return c

def file_hashes(path: str | Path) -> Dict[str, str]:
    p = Path(path)
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with p.open('rb') as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            md5.update(chunk)
            sha256.update(chunk)
    return {'md5': md5.hexdigest(), 'sha256': sha256.hexdigest()}

def default_run_name(seed: int = 42) -> str:
    # Inclui horário para reduzir colisão de nomes em múltiplas execuções no mesmo dia.
    return f"run_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_seed{seed}"

def build_run_dirs(root_runs_dir: str | Path, experiment_id: str, run_name: str) -> Dict[str, Path]:
    root = Path(root_runs_dir)
    run_dir = root / experiment_id / run_name
    dirs = {
        'run_dir': run_dir,
        'adapter_dir': run_dir / 'adapter',
        'checkpoints_dir': run_dir / 'checkpoints',
        'logs_dir': run_dir / 'logs',
        'metrics_dir': run_dir / 'metrics',
        'predictions_dir': run_dir / 'predictions',
        'meta_dir': run_dir / 'meta',
    }
    for d in dirs.values():
        ensure_dir(d)
    return dirs

def get_git_commit(root: str | Path | None = None) -> str | None:
    root = Path(root or repo_root())
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None

def collect_system_info() -> Dict[str, Any]:
    info = {
        'python': sys.version,
        'platform': platform.platform(),
        'machine': platform.machine(),
        'processor': platform.processor(),
    }
    try:
        import torch  # type: ignore
        info['torch'] = getattr(torch, '__version__', None)
        info['cuda_available'] = bool(torch.cuda.is_available())
        info['cuda_version'] = getattr(torch.version, 'cuda', None)
        if torch.cuda.is_available():
            info['gpu_name'] = torch.cuda.get_device_name(0)
            info['gpu_vram_gb'] = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)
    except Exception:
        pass
    for lib in ['transformers', 'datasets', 'peft', 'trl', 'bitsandbytes']:
        try:
            mod = __import__(lib)
            info[lib] = getattr(mod, '__version__', 'unknown')
        except Exception:
            info[lib] = None
    return info

def load_paths_config(path: str | Path | None = None) -> Dict[str, Any]:
    candidate = Path(path) if path else (repo_root() / 'configs' / 'paths.local.yaml')
    if not candidate.is_absolute():
        candidate = repo_root() / candidate
    if not candidate.exists():
        return {}
    return load_config(candidate)

def render_string_template(value: str, variables: Dict[str, Any]) -> str:
    try:
        return value.format(**variables)
    except Exception:
        return value

def resolve_path(value: str | Path, base_dir: str | Path | None = None, variables: Dict[str, Any] | None = None) -> Path:
    if isinstance(value, Path):
        p = value
    else:
        s = str(value)
        if variables:
            s = render_string_template(s, variables)
        p = Path(s)
    if p.is_absolute():
        return p
    base = Path(base_dir) if base_dir else repo_root()
    return (base / p).resolve()
