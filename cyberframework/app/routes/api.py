"""REST API with JWT authentication."""
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Blueprint, jsonify, request, current_app, render_template
from app.extensions import db
from app.models.user import User
from app.models.assessment import Assessment
from app.services.scoring import get_assessment_results
from app.data.framework_controls import CROF_FUNCTIONS

api_bp = Blueprint('api', __name__)


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
        if not token:
            return jsonify({'error': 'Token required'}), 401
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
            current_api_user = db.session.get(User, data['user_id'])
            if not current_api_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(current_api_user, *args, **kwargs)
    return decorated


@api_bp.route('/token', methods=['POST'])
def get_token():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '')
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    exp = datetime.now(timezone.utc) + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS'])
    token = jwt.encode(
        {'user_id': user.id, 'exp': exp},
        current_app.config['JWT_SECRET'],
        algorithm='HS256'
    )
    return jsonify({'token': token, 'expires': exp.isoformat()})


@api_bp.route('/assessments')
@jwt_required
def list_assessments(current_api_user):
    assessments = Assessment.query.filter_by(user_id=current_api_user.id).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'type': a.type,
        'status': a.status,
        'overall_score': a.overall_score,
        'maturity_level': a.maturity_level,
        'created_at': a.created_at.isoformat(),
    } for a in assessments])


@api_bp.route('/assessments/<int:assessment_id>')
@jwt_required
def get_assessment(current_api_user, assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_api_user.id:
        return jsonify({'error': 'Access denied'}), 403
    responses = [
        {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
        for r in assessment.responses.all()
    ]
    results = get_assessment_results(responses)
    return jsonify({
        'id': assessment.id,
        'title': assessment.title,
        'type': assessment.type,
        'status': assessment.status,
        'overall_score': assessment.overall_score,
        'maturity_level': assessment.maturity_level,
        **results,
    })


@api_bp.route('/assessments/<int:assessment_id>/scores')
def get_assessment_scores(assessment_id):
    """Public endpoint used by dashboard charts (session auth via cookie)."""
    from flask_login import current_user
    assessment = Assessment.query.get_or_404(assessment_id)
    # Allow access if the user is logged in and owns the assessment
    if not current_user.is_authenticated or assessment.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    responses = [
        {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
        for r in assessment.responses.all()
    ]
    results = get_assessment_results(responses)
    return jsonify(results)


@api_bp.route('/framework')
def get_framework():
    """Public endpoint returning the CROF framework structure."""
    return jsonify(CROF_FUNCTIONS)


@api_bp.route('/docs')
def docs():
    return render_template('api_docs.html')
