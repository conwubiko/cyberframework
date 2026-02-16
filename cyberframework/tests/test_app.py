"""Basic tests for the CROF application."""
import os
import sys
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.data.framework_controls import CROF_FUNCTIONS, get_all_controls, get_maturity_level
from app.services.scoring import get_assessment_results, calculate_function_scores, compare_assessments


@pytest.fixture
def app():
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Client with a logged-in user."""
    with app.app_context():
        user = User(email='test@test.com', username='tester', organisation='Test Org')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'email': 'test@test.com', 'password': 'password123'})
    return client


@pytest.fixture
def admin_client(app, client):
    """Client with a logged-in admin user."""
    with app.app_context():
        user = User(email='admin@test.com', username='admin', organisation='Test Org', role='admin')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'email': 'admin@test.com', 'password': 'password123'})
    return client


# --- Framework Data Tests ---

def test_framework_has_8_functions():
    assert len(CROF_FUNCTIONS) == 8


def test_framework_total_controls():
    controls = get_all_controls()
    assert len(controls) >= 49


def test_maturity_levels():
    assert get_maturity_level(0) == ('Initial', get_maturity_level(0)[1])
    assert get_maturity_level(25)[0] == 'Developing'
    assert get_maturity_level(50)[0] == 'Defined'
    assert get_maturity_level(70)[0] == 'Managed'
    assert get_maturity_level(90)[0] == 'Optimising'


# --- Scoring Tests ---

def test_scoring_all_yes():
    controls = get_all_controls()
    responses = [{'control_id': c['id'], 'function_id': c['function_id'], 'answer': 'yes'} for c in controls]
    results = get_assessment_results(responses)
    assert results['overall_score'] == 100.0
    assert results['maturity_level'] == 'Optimising'


def test_scoring_all_no():
    controls = get_all_controls()
    responses = [{'control_id': c['id'], 'function_id': c['function_id'], 'answer': 'no'} for c in controls]
    results = get_assessment_results(responses)
    assert results['overall_score'] == 0.0
    assert results['maturity_level'] == 'Initial'


def test_scoring_all_partial():
    controls = get_all_controls()
    responses = [{'control_id': c['id'], 'function_id': c['function_id'], 'answer': 'partial'} for c in controls]
    results = get_assessment_results(responses)
    assert results['overall_score'] == 50.0


# --- Auth Tests ---

def test_login_page(client):
    r = client.get('/login')
    assert r.status_code == 200
    assert b'Sign In' in r.data


def test_register_page(client):
    r = client.get('/register')
    assert r.status_code == 200
    assert b'Register' in r.data


def test_register_and_login(client, app):
    r = client.post('/register', data={
        'email': 'new@test.com', 'username': 'newuser',
        'password': 'password123', 'organisation': 'Org'
    }, follow_redirects=True)
    assert r.status_code == 200

    r = client.post('/login', data={'email': 'new@test.com', 'password': 'password123'}, follow_redirects=True)
    assert r.status_code == 200
    assert b'Dashboard' in r.data


def test_dashboard_requires_auth(client):
    r = client.get('/dashboard', follow_redirects=True)
    assert b'Sign In' in r.data


# --- Assessment Tests ---

def test_create_assessment(auth_client):
    r = auth_client.post('/assessment/new', data={'title': 'Test Assessment'}, follow_redirects=True)
    assert r.status_code == 200


# --- API Tests ---

def test_api_framework(client):
    r = client.get('/api/v1/framework')
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 8


def test_api_token(client, app):
    with app.app_context():
        user = User(email='api@test.com', username='apiuser')
        user.set_password('apipass123')
        db.session.add(user)
        db.session.commit()
    r = client.post('/api/v1/token', json={'email': 'api@test.com', 'password': 'apipass123'})
    assert r.status_code == 200
    assert 'token' in r.get_json()


def test_api_assessments_requires_auth(client):
    r = client.get('/api/v1/assessments')
    assert r.status_code == 401


# --- Feature 1: Audit Log Tests ---

def test_audit_log_on_login(app, client):
    from app.models.audit import AuditLog
    with app.app_context():
        user = User(email='audit@test.com', username='auditor')
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'email': 'audit@test.com', 'password': 'pass123'})
    with app.app_context():
        logs = AuditLog.query.filter_by(action='login').all()
        assert len(logs) >= 1


def test_audit_log_page_requires_admin(auth_client):
    r = auth_client.get('/admin/audit', follow_redirects=True)
    assert r.status_code == 200
    # Non-admin should be redirected
    assert b'Admin access required' in r.data or b'Dashboard' in r.data


def test_audit_log_page_admin(admin_client):
    r = admin_client.get('/admin/audit')
    assert r.status_code == 200
    assert b'Audit Log' in r.data


# --- Feature 2: User Management Tests ---

def test_user_management_page(admin_client):
    r = admin_client.get('/admin/users')
    assert r.status_code == 200
    assert b'User Management' in r.data


def test_user_toggle(admin_client, app):
    with app.app_context():
        user = User(email='toggle@test.com', username='toggleuser')
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
        uid = user.id
    r = admin_client.post(f'/admin/users/{uid}/toggle', follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        user = db.session.get(User, uid)
        assert user.is_active is False


def test_deactivated_user_cannot_login(app, client):
    with app.app_context():
        user = User(email='inactive@test.com', username='inactive', is_active=False)
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
    r = client.post('/login', data={'email': 'inactive@test.com', 'password': 'pass123'}, follow_redirects=True)
    assert b'deactivated' in r.data


# --- Feature 3: Multi-Tenancy Tests ---

def test_organisation_crud(admin_client, app):
    # Create org
    r = admin_client.post('/admin/organisations/new', data={'name': 'Acme Corp'}, follow_redirects=True)
    assert r.status_code == 200
    assert b'Acme Corp' in r.data

    # Verify org was created
    from app.models.organisation import Organisation
    with app.app_context():
        org = Organisation.query.filter_by(name='Acme Corp').first()
        assert org is not None
        assert org.slug == 'acme-corp'

        # Delete org
        r = admin_client.post(f'/admin/organisations/{org.id}/delete', follow_redirects=True)
        assert r.status_code == 200


# --- Feature 4: Email Notification Tests ---

def test_notification_preferences_page(auth_client):
    r = auth_client.get('/settings/notifications')
    assert r.status_code == 200
    assert b'Notification Preferences' in r.data


def test_save_notification_preferences(auth_client, app):
    r = auth_client.post('/settings/notifications', data={
        'scan_complete': 'on',
        # backup_result and assessment_complete not checked
    }, follow_redirects=True)
    assert r.status_code == 200
    from app.models.notification import NotificationPreference
    with app.app_context():
        prefs = NotificationPreference.query.all()
        pref_map = {p.event_type: p.email_enabled for p in prefs}
        assert pref_map.get('scan_complete') is True
        assert pref_map.get('backup_result') is False


# --- Feature 5: Export Tests ---

def test_export_assessment_csv(auth_client, app):
    from app.models.assessment import Assessment
    with app.app_context():
        user = User.query.filter_by(email='test@test.com').first()
        a = Assessment(user_id=user.id, title='Export Test', status='completed')
        db.session.add(a)
        db.session.commit()
        aid = a.id
    r = auth_client.get(f'/export/assessment/{aid}/csv')
    assert r.status_code == 200
    assert r.content_type == 'text/csv; charset=utf-8'


def test_export_scan_csv(auth_client, app):
    from app.models.scan import ScanJob
    with app.app_context():
        user = User.query.filter_by(email='test@test.com').first()
        s = ScanJob(user_id=user.id, scan_type='full', target='localhost', status='completed')
        db.session.add(s)
        db.session.commit()
        sid = s.id
    r = auth_client.get(f'/export/scan/{sid}/csv')
    assert r.status_code == 200
    assert r.content_type == 'text/csv; charset=utf-8'


# --- Feature 6: Scheduled Scan Tests ---

def test_schedule_list_page(auth_client):
    r = auth_client.get('/schedule/')
    assert r.status_code == 200
    assert b'Scheduled Scans' in r.data


def test_create_schedule(auth_client, app):
    r = auth_client.post('/schedule/new', data={
        'name': 'Daily Scan',
        'target': 'localhost',
        'scan_type': 'full',
        'frequency': 'daily',
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'Daily Scan' in r.data

    from app.models.schedule import ScanSchedule
    with app.app_context():
        s = ScanSchedule.query.filter_by(name='Daily Scan').first()
        assert s is not None
        assert s.frequency == 'daily'
        assert s.is_active is True


def test_toggle_schedule(auth_client, app):
    # Create first
    auth_client.post('/schedule/new', data={
        'name': 'Toggle Test',
        'target': 'localhost',
        'scan_type': 'full',
        'frequency': 'weekly',
    })
    from app.models.schedule import ScanSchedule
    with app.app_context():
        s = ScanSchedule.query.filter_by(name='Toggle Test').first()
        sid = s.id
    r = auth_client.post(f'/schedule/{sid}/toggle', follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        s = db.session.get(ScanSchedule, sid)
        assert s.is_active is False


# --- Feature 7: Comparison Tests ---

def test_compare_select_page(auth_client):
    r = auth_client.get('/compare/')
    assert r.status_code == 200
    assert b'Compare' in r.data


def test_compare_assessments_function():
    controls = get_all_controls()
    resp_a = [{'control_id': c['id'], 'function_id': c['function_id'], 'answer': 'no'} for c in controls]
    resp_b = [{'control_id': c['id'], 'function_id': c['function_id'], 'answer': 'yes'} for c in controls]
    results_a = get_assessment_results(resp_a)
    results_b = get_assessment_results(resp_b)
    comparison = compare_assessments(results_a, results_b)
    assert comparison['overall_delta'] == 100.0
    assert comparison['overall_a'] == 0.0
    assert comparison['overall_b'] == 100.0
    # All function deltas should be positive
    for fid, delta in comparison['function_deltas'].items():
        assert delta['delta'] == 100.0


def test_compare_view(auth_client, app):
    from app.models.assessment import Assessment, AssessmentResponse
    from app.data.framework_controls import CROF_FUNCTIONS
    with app.app_context():
        user = User.query.filter_by(email='test@test.com').first()
        a1 = Assessment(user_id=user.id, title='Compare A', status='completed', overall_score=30)
        a2 = Assessment(user_id=user.id, title='Compare B', status='completed', overall_score=70)
        db.session.add_all([a1, a2])
        db.session.flush()

        # Add minimal responses
        for func in CROF_FUNCTIONS:
            for ctrl in func['controls']:
                db.session.add(AssessmentResponse(
                    assessment_id=a1.id, control_id=ctrl['id'],
                    function_id=func['id'], answer='no'))
                db.session.add(AssessmentResponse(
                    assessment_id=a2.id, control_id=ctrl['id'],
                    function_id=func['id'], answer='yes'))
        db.session.commit()
        id1, id2 = a1.id, a2.id

    r = auth_client.get(f'/compare/{id1}/{id2}')
    assert r.status_code == 200
    assert b'Comparison' in r.data
