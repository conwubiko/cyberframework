import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'crof-dev-secret-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'instance', 'crof.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'instance', 'reports')
    FERNET_KEY = os.environ.get('FERNET_KEY', '')
    JWT_SECRET = os.environ.get('JWT_SECRET', 'crof-jwt-secret-change-in-prod')
    JWT_EXPIRY_HOURS = 24

    # Email / SMTP (optional — falls back to console logging if not set)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', '')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'crof@localhost')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
