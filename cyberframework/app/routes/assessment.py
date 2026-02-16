from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.assessment import Assessment, AssessmentResponse
from app.data.framework_controls import CROF_FUNCTIONS
from app.services.scoring import calculate_control_score, get_assessment_results
from app.services.audit import log_action
from app.services.email import notify_assessment_complete

assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessment')


@assessment_bp.route('/')
@login_required
def list_assessments():
    assessments = Assessment.query.filter_by(
        user_id=current_user.id, type='questionnaire'
    ).order_by(Assessment.created_at.desc()).all()
    return render_template('assessment/list.html', assessments=assessments)


@assessment_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_assessment():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            title = f"Assessment {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        assessment = Assessment(
            user_id=current_user.id,
            organisation_id=current_user.organisation_id,
            title=title,
            type='questionnaire',
        )
        db.session.add(assessment)
        db.session.commit()
        log_action(current_user, 'assessment_create', 'Assessment', assessment.id, title)
        return redirect(url_for('assessment.wizard', assessment_id=assessment.id, step=0))
    return render_template('assessment/new.html')


@assessment_bp.route('/<int:assessment_id>/wizard/<int:step>', methods=['GET', 'POST'])
@login_required
def wizard(assessment_id, step):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('assessment.list_assessments'))

    if step < 0 or step >= len(CROF_FUNCTIONS):
        return redirect(url_for('assessment.wizard', assessment_id=assessment_id, step=0))

    current_function = CROF_FUNCTIONS[step]

    if request.method == 'POST':
        # Save responses for this function
        for ctrl in current_function['controls']:
            answer = request.form.get(f"answer_{ctrl['id']}", 'no')
            evidence = request.form.get(f"evidence_{ctrl['id']}", '').strip()
            score = calculate_control_score(answer, ctrl['weight'])

            existing = AssessmentResponse.query.filter_by(
                assessment_id=assessment.id, control_id=ctrl['id']
            ).first()

            if existing:
                existing.answer = answer
                existing.score = score if score is not None else 0.0
                existing.evidence_notes = evidence
            else:
                resp = AssessmentResponse(
                    assessment_id=assessment.id,
                    control_id=ctrl['id'],
                    function_id=current_function['id'],
                    answer=answer,
                    score=score if score is not None else 0.0,
                    evidence_notes=evidence,
                )
                db.session.add(resp)

        db.session.commit()

        # Navigate to next step or complete
        if step + 1 < len(CROF_FUNCTIONS):
            return redirect(url_for('assessment.wizard', assessment_id=assessment_id, step=step + 1))
        else:
            # Complete the assessment
            responses = [
                {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
                for r in assessment.responses.all()
            ]
            results = get_assessment_results(responses)
            assessment.overall_score = results['overall_score']
            assessment.maturity_level = results['maturity_level']
            assessment.status = 'completed'
            assessment.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            log_action(current_user, 'assessment_complete', 'Assessment', assessment.id,
                       f'Score: {results["overall_score"]}%')
            notify_assessment_complete(current_user, assessment)
            flash('Assessment completed!', 'success')
            return redirect(url_for('assessment.view_assessment', assessment_id=assessment_id))

    # Load existing answers for this step
    existing_responses = {}
    for r in AssessmentResponse.query.filter_by(
        assessment_id=assessment.id, function_id=current_function['id']
    ).all():
        existing_responses[r.control_id] = {'answer': r.answer, 'evidence_notes': r.evidence_notes}

    return render_template('assessment/wizard.html',
                           assessment=assessment,
                           function=current_function,
                           step=step,
                           total_steps=len(CROF_FUNCTIONS),
                           all_functions=CROF_FUNCTIONS,
                           existing=existing_responses)


@assessment_bp.route('/<int:assessment_id>')
@login_required
def view_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('assessment.list_assessments'))

    responses = [
        {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
        for r in assessment.responses.all()
    ]
    results = get_assessment_results(responses)

    # Build per-control detail
    response_map = {r.control_id: r for r in assessment.responses.all()}

    return render_template('assessment/view.html',
                           assessment=assessment,
                           results=results,
                           response_map=response_map,
                           functions=CROF_FUNCTIONS)


@assessment_bp.route('/<int:assessment_id>/delete', methods=['POST'])
@login_required
def delete_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('assessment.list_assessments'))
    log_action(current_user, 'assessment_delete', 'Assessment', assessment.id, assessment.title)
    db.session.delete(assessment)
    db.session.commit()
    flash('Assessment deleted.', 'info')
    return redirect(url_for('assessment.list_assessments'))
