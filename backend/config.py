import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'app-copilot-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(basedir), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OKF_OUTPUT_DIR = os.path.join(os.path.dirname(basedir), 'okf_output')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(basedir), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7
    OPENCODE_GO_API_KEY = os.environ.get('OPENCODE_GO_API_KEY', '')
    OPENCODE_GO_BASE_URL = os.environ.get('OPENCODE_GO_BASE_URL', 'https://opencode.ai/zen/go/v1')
