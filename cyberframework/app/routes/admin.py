"""Admin routes — audit log, user management, organisation CRUD."""
import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.audit import AuditLog
from app.models.user import User
from app.models.organisation import Organisation
from app.services.audit import log_action

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator that restricts access to admin users."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


# --- Audit Log ---

@admin_bp.route('/audit')
@login_required
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    user_filter = request.args.get('user_id', '', type=str)

    query = AuditLog.query.order_by(AuditLog.created_at.desc())

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))
    if user_filter:
        query = query.filter(AuditLog.user_id == int(user_filter))

    pagination = query.paginate(page=page, per_page=50, error_out=False)
    users = User.query.order_by(User.username).all()

    return render_template('admin/audit_log.html',
                           logs=pagination.items,
                           pagination=pagination,
                           action_filter=action_filter,
                           user_filter=user_filter,
                           users=users)


# --- User Management ---

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    orgs = Organisation.query.order_by(Organisation.name).all()

    if request.method == 'POST':
        user.role = request.form.get('role', user.role)
        user.organisation = request.form.get('organisation', user.organisation)
        org_id = request.form.get('organisation_id', '')
        user.organisation_id = int(org_id) if org_id else None
        user.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        log_action(current_user, 'user_edit', 'User', user.id,
                   f'Role={user.role}, Active={user.is_active}')
        flash(f'User {user.username} updated.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_edit.html', user=user, orgs=orgs)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself.', 'warning')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    log_action(current_user, f'user_{status}', 'User', user.id)
    flash(f'User {user.username} {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot delete yourself.', 'warning')
        return redirect(url_for('admin.users'))
    username = user.username
    log_action(current_user, 'user_delete', 'User', user.id, f'Deleted user {username}')
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} deleted.', 'info')
    return redirect(url_for('admin.users'))


# --- Organisation Management ---

@admin_bp.route('/organisations')
@login_required
@admin_required
def organisations():
    orgs = Organisation.query.order_by(Organisation.name).all()
    return render_template('admin/organisations.html', orgs=orgs)


@admin_bp.route('/organisations/new', methods=['POST'])
@login_required
@admin_required
def organisation_new():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Organisation name is required.', 'danger')
        return redirect(url_for('admin.organisations'))

    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    if Organisation.query.filter_by(slug=slug).first():
        flash('Organisation with this name already exists.', 'danger')
        return redirect(url_for('admin.organisations'))

    org = Organisation(name=name, slug=slug)
    db.session.add(org)
    db.session.commit()
    log_action(current_user, 'org_create', 'Organisation', org.id, name)
    flash(f'Organisation "{name}" created.', 'success')
    return redirect(url_for('admin.organisations'))


@admin_bp.route('/organisations/<int:org_id>/delete', methods=['POST'])
@login_required
@admin_required
def organisation_delete(org_id):
    org = Organisation.query.get_or_404(org_id)
    # Unassign users from this org
    User.query.filter_by(organisation_id=org.id).update({'organisation_id': None})
    name = org.name
    log_action(current_user, 'org_delete', 'Organisation', org.id, name)
    db.session.delete(org)
    db.session.commit()
    flash(f'Organisation "{name}" deleted.', 'info')
    return redirect(url_for('admin.organisations'))
