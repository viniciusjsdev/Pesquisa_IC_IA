import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set

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

def _failure_answer_segment(text: str) -> str:
    """Return only the answer portion, excluding generated explanations/options."""
    segment = normalize_text(text)
    for marker in ('###', 'explanation:', 'explicacao:', 'explicação:', 'justificativa:'):
        segment = segment.split(marker, 1)[0]
    return segment.strip()

def _failure_options_from_prompt(prompt: str) -> Dict[str, str]:
    """Extract the A-E option texts from the canonical FailureSensorIQ prompt."""
    text = normalize_text(prompt)
    marker = 'opções:' if 'opções:' in text else 'opcoes:'
    if marker not in text:
        return {}
    options_text = text.split(marker, 1)[1].split('### response:', 1)[0]
    matches = list(re.finditer(r'(?<![a-z0-9])([a-e])\s*\)\s*', options_text))
    options: Dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(options_text)
        option_text = options_text[start:end].strip(' .;,:-')
        if option_text:
            options[match.group(1)] = option_text
    return options

def choice_labels(text: str, prompt: str = '') -> Set[str]:
    """Extract a set of FailureSensorIQ labels without collapsing multi-label answers."""
    segment = _failure_answer_segment(text)
    labels = set(re.findall(r'(?<![a-z0-9])([a-e])\s*[\)\].:\-]', segment))
    labels.update(re.findall(r'\*\*([a-e])(?:\*\*|\s*$)', segment))

    # Handle concise forms such as "A e B", "A and B" or "options A, B".
    for match in re.finditer(r'(?<![a-z0-9])([a-e])\s*(?:,|/|&|\be\b|\band\b)\s*([a-e])(?![a-z0-9])', segment):
        labels.update(match.groups())
    for match in re.finditer(r'\b(?:option|options|alternativa|alternativas|opcao|opcoes|opção|opções)\s+([a-e])\b', segment):
        labels.add(match.group(1))
    leading = re.match(r'^\s*([a-e])(?:\s|$)', segment)
    if leading:
        labels.add(leading.group(1))

    # Some base-model answers return only the option text instead of its letter.
    if not labels and prompt:
        for label, option_text in _failure_options_from_prompt(prompt).items():
            if option_text and re.search(rf'(?<![a-z0-9]){re.escape(option_text)}(?![a-z0-9])', segment):
                labels.add(label)
    return labels

def _multilabel_scores(golds: List[Set[str]], preds: List[Set[str]]) -> Dict[str, float]:
    labels = list('abcde')
    per_label = []
    tp_total = fp_total = fn_total = 0
    for label in labels:
        tp = sum(label in g and label in p for g, p in zip(golds, preds))
        fp = sum(label not in g and label in p for g, p in zip(golds, preds))
        fn = sum(label in g and label not in p for g, p in zip(golds, preds))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label.append((precision, recall, f1))
        tp_total += tp
        fp_total += fp
        fn_total += fn

    precision_micro = tp_total / (tp_total + fp_total) if tp_total + fp_total else 0.0
    recall_micro = tp_total / (tp_total + fn_total) if tp_total + fn_total else 0.0
    f1_micro = (
        2 * precision_micro * recall_micro / (precision_micro + recall_micro)
        if precision_micro + recall_micro else 0.0
    )
    jaccard = [len(g & p) / len(g | p) if g | p else 1.0 for g, p in zip(golds, preds)]
    return {
        'precision_macro': round(sum(x[0] for x in per_label) / len(labels), 4),
        'recall_macro': round(sum(x[1] for x in per_label) / len(labels), 4),
        'f1_macro': round(sum(x[2] for x in per_label) / len(labels), 4),
        'precision_micro': round(precision_micro, 4),
        'recall_micro': round(recall_micro, 4),
        'f1_micro': round(f1_micro, 4),
        'jaccard_samples': round(sum(jaccard) / len(jaccard), 4) if jaccard else 0.0,
    }

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
    gold_labels = [choice_labels(g) for g in gold_norm]
    pred_labels = [choice_labels(p, str(r.get('prompt', ''))) for r, p in zip(rows, pred_norm)]
    n = len(rows)
    exact = sum(int(g == p) for g, p in zip(gold_norm, pred_norm))
    subset_accuracy = sum(int(g == p) for g, p in zip(gold_labels, pred_labels))
    legacy_gold = [choice_label(g) for g in gold_norm]
    legacy_pred = [choice_label(p) for p in pred_norm]
    metrics = _multilabel_scores(gold_labels, pred_labels)
    metrics.update({
        'exact_match': round(exact / n, 4) if n else 0.0,
        'accuracy': round(subset_accuracy / n, 4) if n else 0.0,
        'subset_accuracy': round(subset_accuracy / n, 4) if n else 0.0,
        'legacy_first_label_accuracy': round(
            sum(int(g == p) for g, p in zip(legacy_gold, legacy_pred)) / n, 4
        ) if n else 0.0,
        'parse_failures': sum(not labels for labels in pred_labels),
        'average_gold_labels': round(sum(len(labels) for labels in gold_labels) / n, 4) if n else 0.0,
        'average_predicted_labels': round(sum(len(labels) for labels in pred_labels) / n, 4) if n else 0.0,
        'confusion_top': confusion_pairs(
            ['+'.join(sorted(labels)) or '<none>' for labels in gold_labels],
            ['+'.join(sorted(labels)) or '<none>' for labels in pred_labels],
        ),
        'metric_definition': 'multilabel_exact_set_accuracy_and_labelwise_f1',
    })
    return metrics
