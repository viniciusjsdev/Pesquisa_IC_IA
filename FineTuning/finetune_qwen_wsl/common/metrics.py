import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

_NUM_RE = re.compile(r'[-+]?\d+(?:[\.,]\d+)?')

def normalize_text(text: str) -> str:
    text = '' if text is None else str(text)
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text

def parse_numeric(text: str) -> Optional[float]:
    t = normalize_text(text).replace(',', '.')
    m = _NUM_RE.search(t)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None

def numeric_match(gold: Any, pred: Any, abs_tol: float = 1e-3, rel_tol: float = 1e-3) -> bool:
    g = parse_numeric(str(gold))
    p = parse_numeric(str(pred))
    if g is None or p is None:
        return False
    return math.isclose(g, p, rel_tol=rel_tol, abs_tol=abs_tol)

def choice_label(text: str) -> str:
    t = normalize_text(text)
    m = re.match(r'^([a-e])([\)\].:\-]|\s|$)', t)
    if m:
        return m.group(1)
    return t

def macro_f1_from_labels(golds: List[str], preds: List[str]) -> float:
    labels = sorted(set(golds) | set(preds))
    if not labels:
        return 0.0
    f1s = []
    for lab in labels:
        tp = sum(1 for g, p in zip(golds, preds) if g == lab and p == lab)
        fp = sum(1 for g, p in zip(golds, preds) if g != lab and p == lab)
        fn = sum(1 for g, p in zip(golds, preds) if g == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s)

def confusion_pairs(golds: List[str], preds: List[str], limit: int = 20):
    cnt = Counter()
    for g, p in zip(golds, preds):
        if g != p:
            cnt[(g, p)] += 1
    return [{'gold': g, 'pred': p, 'count': c} for (g, p), c in cnt.most_common(limit)]

def evaluate_finqa(rows: List[Dict[str, Any]], preds: List[str], abs_tol: float, rel_tol: float) -> Dict[str, Any]:
    exact = 0
    numeric_ok = 0
    numeric_total = 0
    abs_errors = []
    rel_errors = []
    by_op = defaultdict(lambda: {'n': 0, 'exact': 0, 'numeric_match': 0})
    error_types = Counter()
    for row, pred in zip(rows, preds):
        gold = row.get('resposta', '')
        g_norm = normalize_text(gold)
        p_norm = normalize_text(pred)
        is_exact = g_norm == p_norm
        exact += int(is_exact)
        g_num = parse_numeric(gold)
        p_num = parse_numeric(pred)
        is_num = False
        if g_num is not None:
            numeric_total += 1
            if p_num is None:
                error_types['numeric_parse_fail'] += 1
            else:
                err_abs = abs(p_num - g_num)
                abs_errors.append(err_abs)
                rel_errors.append(err_abs / (abs(g_num) if g_num != 0 else 1.0))
                is_num = math.isclose(g_num, p_num, rel_tol=rel_tol, abs_tol=abs_tol)
                numeric_ok += int(is_num)
        elif not is_exact:
            error_types['non_numeric_mismatch'] += 1
        op = str(((row.get('meta') or {}).get('program') or 'unknown')).split('(')[0]
        b = by_op[op]
        b['n'] += 1
        b['exact'] += int(is_exact)
        b['numeric_match'] += int(is_num)
    n = len(rows)
    by_operation = {}
    for op, b in sorted(by_op.items()):
        by_operation[op] = {
            'n': b['n'],
            'exact_match': round(b['exact'] / b['n'], 4) if b['n'] else 0.0,
            'numeric_match': round(b['numeric_match'] / b['n'], 4) if b['n'] else 0.0,
        }
    return {
        'exact_match': round(exact / n, 4) if n else 0.0,
        'numeric_accuracy': round(numeric_ok / numeric_total, 4) if numeric_total else 0.0,
        'numeric_total': numeric_total,
        'mae_numeric_parseable': round(sum(abs_errors) / len(abs_errors), 6) if abs_errors else None,
        'mre_numeric_parseable': round(sum(rel_errors) / len(rel_errors), 6) if rel_errors else None,
        'by_operation': by_operation,
        'error_types': dict(error_types),
    }

def evaluate_failure(rows: List[Dict[str, Any]], preds: List[str]) -> Dict[str, Any]:
    gold_norm = [normalize_text(r.get('resposta', '')) for r in rows]
    pred_norm = [normalize_text(p) for p in preds]
    gold_labels = [choice_label(g) for g in gold_norm]
    pred_labels = [choice_label(p) for p in pred_norm]
    n = len(rows)
    exact = sum(int(g == p) for g, p in zip(gold_norm, pred_norm))
    acc = sum(int(g == p) for g, p in zip(gold_labels, pred_labels))
    return {
        'exact_match': round(exact / n, 4) if n else 0.0,
        'accuracy': round(acc / n, 4) if n else 0.0,
        'f1_macro': round(macro_f1_from_labels(gold_labels, pred_labels), 4),
        'confusion_top': confusion_pairs(gold_labels, pred_labels),
    }
