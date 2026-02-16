"""Scoring engine for CROF assessments."""
from app.data.framework_controls import CROF_FUNCTIONS, get_maturity_level

ANSWER_SCORES = {
    'yes': 1.0,
    'partial': 0.5,
    'no': 0.0,
    'na': None,  # excluded from calculation
}


def calculate_control_score(answer, weight):
    """Return weighted score for a single control answer."""
    base = ANSWER_SCORES.get(answer, 0.0)
    if base is None:
        return None
    return base * weight


def calculate_function_scores(responses):
    """
    Calculate per-function percentage scores from a list of response dicts.
    responses: list of {control_id, function_id, answer}
    Returns: {function_id: {name, score_pct, answered, total, max_possible, achieved}}
    """
    control_map = {}
    for func in CROF_FUNCTIONS:
        for ctrl in func['controls']:
            control_map[ctrl['id']] = {'weight': ctrl['weight'], 'function_id': func['id']}

    func_scores = {}
    for func in CROF_FUNCTIONS:
        func_scores[func['id']] = {
            'name': func['name'],
            'achieved': 0.0,
            'max_possible': 0.0,
            'answered': 0,
            'total': len(func['controls']),
        }

    for resp in responses:
        cid = resp.get('control_id', '')
        answer = resp.get('answer', 'no')
        if cid not in control_map:
            continue
        cm = control_map[cid]
        fid = cm['function_id']
        score = calculate_control_score(answer, cm['weight'])
        if score is not None:
            func_scores[fid]['achieved'] += score
            func_scores[fid]['max_possible'] += cm['weight']
            func_scores[fid]['answered'] += 1

    for fid, fs in func_scores.items():
        if fs['max_possible'] > 0:
            fs['score_pct'] = round((fs['achieved'] / fs['max_possible']) * 100, 1)
        else:
            fs['score_pct'] = 0.0

    return func_scores


def calculate_overall_score(func_scores):
    """Calculate overall percentage from function scores."""
    total_achieved = sum(fs['achieved'] for fs in func_scores.values())
    total_possible = sum(fs['max_possible'] for fs in func_scores.values())
    if total_possible == 0:
        return 0.0
    return round((total_achieved / total_possible) * 100, 1)


def get_assessment_results(responses):
    """Full scoring pipeline: returns function_scores, overall_score, maturity_level, maturity_desc."""
    func_scores = calculate_function_scores(responses)
    overall = calculate_overall_score(func_scores)
    maturity, maturity_desc = get_maturity_level(overall)
    return {
        'function_scores': func_scores,
        'overall_score': overall,
        'maturity_level': maturity,
        'maturity_description': maturity_desc,
    }


def compare_assessments(results_a, results_b):
    """Compare two assessment results and return per-function deltas.

    Returns dict with function_id keys, each containing:
      name, score_a, score_b, delta (positive = improved)
    """
    deltas = {}
    fs_a = results_a.get('function_scores', {})
    fs_b = results_b.get('function_scores', {})

    all_funcs = set(list(fs_a.keys()) + list(fs_b.keys()))
    for fid in all_funcs:
        a = fs_a.get(fid, {})
        b = fs_b.get(fid, {})
        score_a = a.get('score_pct', 0)
        score_b = b.get('score_pct', 0)
        deltas[fid] = {
            'name': a.get('name', b.get('name', fid)),
            'score_a': score_a,
            'score_b': score_b,
            'delta': round(score_b - score_a, 1),
        }

    return {
        'function_deltas': deltas,
        'overall_a': results_a.get('overall_score', 0),
        'overall_b': results_b.get('overall_score', 0),
        'overall_delta': round(
            results_b.get('overall_score', 0) - results_a.get('overall_score', 0), 1
        ),
    }
