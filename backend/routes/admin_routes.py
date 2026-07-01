from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, jsonify, current_app
from flask_login import current_user

from backend.models import db, User, Project
from backend.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('')
@admin_required
def dashboard():
    """Admin dashboard with high-level platform statistics."""
    stats = _compute_stats()
    return render_template('admin/dashboard.html', stats=stats)


@admin_bp.route('/users')
@admin_required
def users():
    """Display all registered users with their plans."""
    all_users = (
        User.query
        .order_by(User.created_at.desc())
        .all()
    )
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/projects')
@admin_required
def projects():
    """Display all projects across all users."""
    all_projects = (
        Project.query
        .order_by(Project.updated_at.desc())
        .all()
    )
    return render_template('admin/dashboard.html', stats=_compute_stats())


@admin_bp.route('/stats')
@admin_required
def stats():
    """Return platform statistics as JSON."""
    stats_data = _compute_stats()
    return jsonify(stats_data)


def _compute_stats() -> dict:
    """Compute aggregate platform statistics."""
    total_users = User.query.count()
    total_projects = Project.query.count()
    completed_projects = Project.query.filter_by(completed=True).count()

    plan_counts = {}
    for plan_name in ('free', 'premium', 'admin'):
        plan_counts[plan_name] = User.query.filter_by(plan=plan_name).count()

    # Phase distribution
    phase_counts = {}
    for phase in range(5):
        phase_counts[phase] = Project.query.filter_by(current_phase=phase).count()

    # Recent registrations (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()

    # Recent projects (last 7 days)
    new_projects_week = Project.query.filter(Project.created_at >= week_ago).count()

    return {
        'total_users': total_users,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'completion_rate': round(
            (completed_projects / total_projects * 100) if total_projects else 0, 1
        ),
        'plan_distribution': plan_counts,
        'phase_distribution': phase_counts,
        'new_users_this_week': new_users_week,
        'new_projects_this_week': new_projects_week,
    }
