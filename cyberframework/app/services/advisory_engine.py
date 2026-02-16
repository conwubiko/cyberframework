"""Advisory engine — generates prioritised recommendations and remediation roadmap."""
from app.data.framework_controls import CROF_FUNCTIONS
from app.services.scoring import get_assessment_results


def generate_advisory(assessment):
    """Generate recommendations for a completed assessment.
    Returns list of recommendations sorted by priority (highest gap first).
    """
    responses = [
        {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
        for r in assessment.responses.all()
    ]
    results = get_assessment_results(responses)
    response_map = {r.control_id: r for r in assessment.responses.all()}

    recommendations = []
    for func in CROF_FUNCTIONS:
        for ctrl in func['controls']:
            resp = response_map.get(ctrl['id'])
            answer = resp.answer if resp else 'no'
            if answer in ('no', 'partial'):
                gap = ctrl['weight'] if answer == 'no' else ctrl['weight'] * 0.5
                recommendations.append({
                    'control_id': ctrl['id'],
                    'function_id': func['id'],
                    'function_name': func['name'],
                    'title': ctrl['title'],
                    'question': ctrl['question'],
                    'guidance': ctrl['guidance'],
                    'current_answer': answer,
                    'weight': ctrl['weight'],
                    'gap_score': gap,
                    'priority': 'Critical' if gap >= 3 else 'High' if gap >= 2 else 'Medium' if gap >= 1 else 'Low',
                })

    recommendations.sort(key=lambda x: x['gap_score'], reverse=True)
    return {
        'recommendations': recommendations,
        'results': results,
        'total_gaps': len(recommendations),
        'critical_gaps': len([r for r in recommendations if r['priority'] == 'Critical']),
        'high_gaps': len([r for r in recommendations if r['priority'] == 'High']),
    }


def generate_roadmap(recommendations):
    """Group recommendations into phased roadmap by function."""
    phases = {}
    for rec in recommendations:
        fid = rec['function_id']
        if fid not in phases:
            phases[fid] = {
                'function_id': fid,
                'function_name': rec['function_name'],
                'items': [],
            }
        phases[fid]['items'].append(rec)

    # Sort phases by total gap score (worst first)
    phase_list = sorted(phases.values(),
                        key=lambda p: sum(i['gap_score'] for i in p['items']),
                        reverse=True)

    for i, phase in enumerate(phase_list):
        phase['phase_number'] = i + 1
        phase['total_gap'] = sum(item['gap_score'] for item in phase['items'])

    return phase_list
