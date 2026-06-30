from datetime import datetime, timezone

from flask import current_app
from flask_login import LoginManager, current_user
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from backend.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id: str):
    """Flask-Login callback: reload user from session ID."""
    return db.session.get(User, int(user_id))


# ── Decorators ──────────────────────────────────────────────────────────────

def login_required(f):
    """Require an authenticated user.  Redirects to login if not authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('auth.login', next=url_for(
                f.__name__ if hasattr(f, '__name__') else 'dashboard',
                **kwargs
            )))
        return f(*args, **kwargs)
    return decorated_function


def premium_required(f):
    """Require an authenticated user with a premium or admin plan."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_premium():
            flash('Esta funcionalidade requer uma conta Premium.', 'info')
            return redirect(url_for('auth.upgrade'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require an authenticated user with admin plan."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ── Forms ───────────────────────────────────────────────────────────────────

class LoginForm(FlaskForm):
    email = EmailField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={'placeholder': 'seu@email.com', 'class': 'form-control'},
    )
    password = PasswordField(
        'Senha',
        validators=[DataRequired(), Length(min=4, max=200)],
        render_kw={'placeholder': 'Sua senha', 'class': 'form-control'},
    )
    submit = SubmitField('Entrar', render_kw={'class': 'btn btn-primary btn-lg w-100'})


class RegisterForm(FlaskForm):
    username = StringField(
        'Nome de usuário',
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={'placeholder': 'Seu nome de usuário', 'class': 'form-control'},
    )
    email = EmailField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={'placeholder': 'seu@email.com', 'class': 'form-control'},
    )
    password = PasswordField(
        'Senha',
        validators=[DataRequired(), Length(min=6, max=200)],
        render_kw={'placeholder': 'Crie uma senha forte', 'class': 'form-control'},
    )
    confirm_password = PasswordField(
        'Confirmar senha',
        validators=[DataRequired(), EqualTo('password', message='As senhas não conferem.')],
        render_kw={'placeholder': 'Repita a senha', 'class': 'form-control'},
    )
    submit = SubmitField('Criar conta', render_kw={'class': 'btn btn-primary btn-lg w-100'})

    def validate_username(self, field):
        """Ensure the username is not already taken."""
        existing = User.query.filter_by(username=field.data.strip()).first()
        if existing:
            raise ValidationError('Este nome de usuário já está em uso.')

    def validate_email(self, field):
        """Ensure the email is not already registered."""
        existing = User.query.filter_by(email=field.data.strip().lower()).first()
        if existing:
            raise ValidationError('Este email já está cadastrado.')
