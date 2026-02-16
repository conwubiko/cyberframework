"""Comparison view routes — side-by-side assessment comparison."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.assessment import Assessment
from app.services.scoring import get_assessment_results, compare_assessments
from app.data.framework_controls import CROF_FUNCTIONS

compare_bp = Blueprint('compare', __name__, url_prefix='/compare')


@compare_bp.route('/')
@login_required
def select():
    assessments = Assessment.query.filter_by(
        user_id=current_user.id, status='completed'
    ).order_by(Assessment.created_at.desc()).all()
    return render_template('compare/select.html', assessments=assessments)


@compare_bp.route('/<int:id1>/<int:id2>')
@login_required
def view(id1, id2):
    a1 = Assessment.query.get_or_404(id1)
    a2 = Assessment.query.get_or_404(id2)

    if a1.user_id != current_user.id or a2.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('compare.select'))

    if a1.status != 'completed' or a2.status != 'completed':
        flash('Both assessments must be completed.', 'warning')
        return redirect(url_for('compare.select'))

    responses_a = [
        {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
        for r in a1.responses.all()
    ]
    responses_b = [
        {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
        for r in a2.responses.all()
    ]

    results_a = get_assessment_results(responses_a)
    results_b = get_assessment_results(responses_b)
    comparison = compare_assessments(results_a, results_b)

    # Build per-control diff
    resp_map_a = {r.control_id: r for r in a1.responses.all()}
    resp_map_b = {r.control_id: r for r in a2.responses.all()}

    return render_template('compare/view.html',
                           a1=a1, a2=a2,
                           results_a=results_a, results_b=results_b,
                           comparison=comparison,
                           resp_map_a=resp_map_a, resp_map_b=resp_map_b,
                           functions=CROF_FUNCTIONS)
