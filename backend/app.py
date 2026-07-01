import os
import logging

from flask import Flask, render_template, request, current_app
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from backend.config import Config
from backend.models import db
from backend.auth import login_manager
from backend.routes.auth_routes import auth_bp
from backend.routes.project_routes import project_bp
from backend.routes.admin_routes import admin_bp

migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config) -> Flask:
    """
    Application factory.  Creates and configures the Flask app, registers
    blueprints, initializes extensions, sets up error handlers, and injects
    template globals.
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
    )
    app.config.from_object(config_class)

    # ── Initialize extensions ────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # ── Register blueprints ──────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(admin_bp)

    # ── Create tables on first request (development convenience) ─────────
    with app.app_context():
        db.create_all()

    # ── Configure logging ────────────────────────────────────────────────
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)

    # ── Error handlers ───────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors."""
        return render_template('errors/404.html', error=e), 404

    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 Forbidden errors."""
        return render_template('errors/403.html', error=e), 403

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 Internal Server errors."""
        db.session.rollback()
        current_app.logger.error(f'Internal server error: {e}')
        return render_template('errors/500.html', error=e), 500

    # ── Context processor: inject plan info and ad status ────────────────
    @app.context_processor
    def inject_globals():
        """Inject variables available in every template."""
        from flask_login import current_user
        show_ads = False
        plan = 'free'
        is_premium = False
        is_admin = False
        if current_user.is_authenticated:
            plan = current_user.plan
            is_premium = current_user.is_premium()
            is_admin = current_user.is_admin()
            if plan == 'free':
                show_ads = True
        return dict(
            show_ads=show_ads,
            user_plan=plan,
            is_premium=is_premium,
            is_admin=is_admin,
            app_name='App Copilot',
            current_year=__import__('datetime').datetime.now().year,
        )

    # ── Before-request: set permanent session lifetime ───────────────────
    @app.before_request
    def before_request():
        from flask import session
        session.permanent = True

    return app
