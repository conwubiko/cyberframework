import os
from flask import Flask
from config import Config, config_by_name
from app.extensions import db, login_manager, migrate


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    os.makedirs(app.config.get('UPLOAD_FOLDER', 'instance/reports'), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        if user and not user.is_active:
            return None
        return user

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.assessment import assessment_bp
    from app.routes.scanner import scanner_bp
    from app.routes.report import report_bp
    from app.routes.backup import backup_bp
    from app.routes.advisory import advisory_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    from app.routes.settings import settings_bp
    from app.routes.export import export_bp
    from app.routes.schedule import schedule_bp
    from app.routes.compare import compare_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(scanner_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(advisory_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(compare_bp)

    from app.routes.errors import register_error_handlers
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    # Start the scan scheduler
    from app.services.scheduler import start_scheduler
    start_scheduler(app)

    return app
