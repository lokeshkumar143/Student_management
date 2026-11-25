import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'acadverify-enterprise-secret-key-2026')
    DATABASE = os.path.join(BASE_DIR, 'student_management.db')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    TESTING = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestConfig(Config):
    DATABASE = os.path.join(BASE_DIR, 'test_student_management.db')
    TESTING = True
    WTF_CSRF_ENABLED = False
