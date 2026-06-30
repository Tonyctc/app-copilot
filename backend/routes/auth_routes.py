from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
)
from flask_login import login_user, logout_user, login_required, current_user

from backend.models import db, User
from backend.auth import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__, url_prefix='')


@auth_bp.route('/')
def index():
    """Landing page for unauthenticated users."""
    if current_user.is_authenticated:
        return redirect(url_for('project.dashboard'))
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Display login form and authenticate users."""
    if current_user.is_authenticated:
        return redirect(url_for('project.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            flash(f'Bem-vindo de volta, {user.username}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('project.dashboard'))
        else:
            flash('Email ou senha inválidos.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Display registration form and create new user accounts."""
    if current_user.is_authenticated:
        return redirect(url_for('project.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(
            'Conta criada com sucesso! Faça login para continuar.',
            'success',
        )
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/upgrade', methods=['GET', 'POST'])
@login_required
def upgrade():
    """Simulated payment flow to upgrade from free to premium."""
    if current_user.is_premium():
        flash('Sua conta já possui acesso Premium.', 'info')
        return redirect(url_for('project.dashboard'))

    if request.method == 'POST':
        # Simulated payment processing
        current_user.plan = 'premium'
        db.session.commit()
        flash(
            'Parabéns! Sua conta foi atualizada para Premium. '
            'Aproveite todos os recursos exclusivos!',
            'success',
        )
        return redirect(url_for('project.dashboard'))

    return render_template('upgrade.html')
