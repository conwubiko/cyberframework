from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.assessment import Assessment
from app.services.advisory_engine import generate_advisory, generate_roadmap

advisory_bp = Blueprint('advisory', __name__, url_prefix='/advisory')


@advisory_bp.route('/')
@login_required
def index():
    assessments = Assessment.query.filter_by(
        user_id=current_user.id, status='completed'
    ).order_by(Assessment.created_at.desc()).all()
    return render_template('advisory/index.html', assessments=assessments)


@advisory_bp.route('/<int:assessment_id>')
@login_required
def view(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('advisory.index'))
    if assessment.status != 'completed':
        flash('Assessment must be completed first.', 'warning')
        return redirect(url_for('advisory.index'))

    advisory = generate_advisory(assessment)
    roadmap = generate_roadmap(advisory['recommendations'])

    return render_template('advisory/view.html',
                           assessment=assessment,
                           advisory=advisory,
                           roadmap=roadmap)
