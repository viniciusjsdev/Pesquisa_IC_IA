"""Capture the exact Git baseline in an isolated source tree, never call external APIs."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'e93b816ef6df667992f3bfd0f632aaf7875f78e2'
with tempfile.TemporaryDirectory(prefix='spec015-baseline-') as tmp:
    archive = Path(tmp) / 'baseline.zip'
    subprocess.run(['git', 'archive', '--format=zip', '-o', str(archive), BASELINE,
                    'inference_api/src', 'runpod/serving/manifest.json'], cwd=ROOT, check=True)
    with zipfile.ZipFile(archive) as z: z.extractall(tmp)
    sys.path[:0] = [str(Path(tmp)/'inference_api/src'), str(ROOT/'inference_api/tests')]
    from inference_api.agent_harness import scenarios
    from spec015_cases import execute, normalize, CASES
    outputs = {}
    for scenario in ('fixed_evidence', 'data_access'):
        for adapter in ('openai_responses', 'groq_chat', 'chat_completions'):
            for case in CASES:
                outputs['/'.join((scenario, adapter, case))] = normalize(execute(scenarios, scenario, adapter, case))
    target = ROOT/'specs/active/SPEC-015/evidence/differential-baseline.json'
    if target.exists(): raise SystemExit('Refusing to overwrite captured baseline')
    target.write_text(json.dumps({'baseline': BASELINE, 'synthetic': True, 'cases': outputs},
                                 ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Captured {len(outputs)} synthetic baseline cases')
