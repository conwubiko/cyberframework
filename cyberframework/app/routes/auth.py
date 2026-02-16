from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.services.audit import log_action

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Account has been deactivated. Contact an administrator.', 'danger')
                return render_template('auth/login.html')
            login_user(user, remember=request.form.get('remember'))
            log_action(user, 'login', 'User', user.id)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        organisation = request.form.get('organisation', '').strip()

        if not email or not username or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html')

        user = User(email=email, username=username, organisation=organisation)
        user.set_password(password)
        # First user becomes admin
        if User.query.count() == 0:
            user.role = 'admin'
        db.session.add(user)
        db.session.commit()
        log_action(user, 'register', 'User', user.id)
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user, 'logout', 'User', current_user.id)
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))
