import json
import os
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    send_file, current_app, jsonify,
)
from flask_login import login_required, current_user

from backend.models import db, Project
from backend.auth import login_required as custom_login_required, premium_required
from backend.okf_generator import OKFGenerator

project_bp = Blueprint('project', __name__, url_prefix='')


@project_bp.route('/dashboard')
@login_required
def dashboard():
    """Display the user's project list."""
    projects = (
        Project.query
        .filter_by(user_id=current_user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return render_template('dashboard.html', projects=projects)


@project_bp.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """Create a new project."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('O nome do projeto é obrigatório.', 'danger')
            return render_template('new_project.html')

        project = Project(
            name=name,
            user_id=current_user.id,
            current_phase=0,
        )
        db.session.add(project)
        db.session.commit()

        flash(f'Projeto "{name}" criado com sucesso!', 'success')
        return redirect(url_for('project.wizard', project_id=project.id))

    return render_template('new_project.html')


@project_bp.route('/project/<int:project_id>/wizard')
@login_required
def wizard(project_id):
    """Main wizard page showing the current phase of a project."""
    project = db.session.get(Project, project_id)
    if not project:
        flash('Projeto não encontrado.', 'danger')
        return redirect(url_for('project.dashboard'))

    if project.user_id != current_user.id and not current_user.is_admin():
        flash('Você não tem permissão para acessar este projeto.', 'danger')
        return redirect(url_for('project.dashboard'))

    # Load phase data
    phase_data = {
        1: project.get_discovery_data(),
        2: project.get_definition_data(),
        3: project.get_development_data(),
        4: project.get_delivery_data(),
    }

    return render_template(
        'wizard.html',
        project=project,
        phase_data=phase_data,
        phase_choices={
            1: 'Descobrir',
            2: 'Definir',
            3: 'Desenvolver',
            4: 'Entregar',
        },
    )


@project_bp.route('/project/<int:project_id>/save_discovery', methods=['POST'])
@login_required
def save_discovery(project_id):
    """Save phase 1 (Descobrir / Discovery) data."""
    project = db.session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        flash('Projeto não encontrado ou acesso negado.', 'danger')
        return redirect(url_for('project.dashboard'))

    data = _extract_form_data(request, [
        'app_name', 'main_goal', 'pain_points', 'target_audience',
    ])
    project.set_discovery_data(data)
    if project.current_phase < 1:
        project.current_phase = 1
    project.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True, message='Fase de Descoberta salva com sucesso!')
    flash('Fase de Descoberta salva com sucesso!', 'success')
    return redirect(url_for('project.wizard', project_id=project.id))


@project_bp.route('/project/<int:project_id>/save_definition', methods=['POST'])
@login_required
def save_definition(project_id):
    """Save phase 2 (Definir / Definition) data."""
    project = db.session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        flash('Projeto não encontrado ou acesso negado.', 'danger')
        return redirect(url_for('project.dashboard'))

    data = _extract_form_data(request, [
        'functional_requirements', 'non_functional_requirements',
    ])
    project.set_definition_data(data)
    if project.current_phase < 2:
        project.current_phase = 2
    project.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True, message='Fase de Definição salva com sucesso!')
    flash('Fase de Definição salva com sucesso!', 'success')
    return redirect(url_for('project.wizard', project_id=project.id))


@project_bp.route('/project/<int:project_id>/save_development', methods=['POST'])
@login_required
def save_development(project_id):
    """Save phase 3 (Desenvolver / Development) data."""
    project = db.session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        flash('Projeto não encontrado ou acesso negado.', 'danger')
        return redirect(url_for('project.dashboard'))

    data = _extract_form_data(request, [
        'frontend_tech', 'backend_tech', 'visual_style', 'screen_flow',
        'business_rules', 'database_entities', 'attributes_relationships',
    ])
    project.set_development_data(data)
    if project.current_phase < 3:
        project.current_phase = 3
    project.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True, message='Fase de Desenvolvimento salva com sucesso!')
    flash('Fase de Desenvolvimento salva com sucesso!', 'success')
    return redirect(url_for('project.wizard', project_id=project.id))


@project_bp.route('/project/<int:project_id>/save_delivery', methods=['POST'])
@login_required
def save_delivery(project_id):
    """Save phase 4 (Entregar / Delivery) data and complete the project."""
    project = db.session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        flash('Projeto não encontrado ou acesso negado.', 'danger')
        return redirect(url_for('project.dashboard'))

    data = _extract_form_data(request, [
        'final_summary',
    ])
    project.set_delivery_data(data)

    # Mark as completed and advance phase
    if project.current_phase < 4:
        project.current_phase = 4
    project.completed = True
    project.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    # Auto-generate OKF bundle
    try:
        generator = OKFGenerator()
        generator.generate_bundle(project)
    except Exception as e:
        current_app.logger.error(f'OKF generation error: {e}')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True, message='Projeto concluído! O bundle OKF foi gerado.')

    flash(
        'Fase de Entrega salva com sucesso! Projeto concluído! '
        'Você pode exportar o bundle OKF na página do projeto.',
        'success',
    )
    return redirect(url_for('project.wizard', project_id=project.id))


@project_bp.route('/project/<int:project_id>/export')
@login_required
@premium_required
def export_project(project_id):
    """Export the project OKF bundle as a ZIP file (premium-only)."""
    project = db.session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        flash('Projeto não encontrado ou acesso negado.', 'danger')
        return redirect(url_for('project.dashboard'))

    try:
        generator = OKFGenerator()
        zip_path = generator.export_zip(project)
        safe_name = generator._sanitize_filename(project.name)
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'{safe_name}_okf.zip',
            mimetype='application/zip',
        )
    except Exception as e:
        current_app.logger.error(f'ZIP export error: {e}')
        flash('Erro ao gerar o arquivo ZIP. Tente novamente.', 'danger')
        return redirect(url_for('project.wizard', project_id=project.id))


@project_bp.route('/project/<int:project_id>/generate-prompt')
@login_required
def generate_build_prompt(project_id):
    """Generate the build prompt using the deepseek model."""
    project = db.session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        flash('Projeto não encontrado ou acesso negado.', 'danger')
        return redirect(url_for('project.dashboard'))

    if not project.completed:
        flash('Complete todas as fases do projeto antes de gerar o prompt de construção.', 'warning')
        return redirect(url_for('project.wizard', project_id=project.id))

    try:
        generator = OKFGenerator()
        prompt_text = generator.generate_build_prompt_text(project)

        # Save the prompt to an OKF file
        proj_dir = generator._get_project_dir(project)
        os.makedirs(proj_dir, exist_ok=True)
        prompt_path = os.path.join(proj_dir, 'build-prompt.md')
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_text)

        flash('Prompt de construção gerado com sucesso!', 'success')
        return redirect(url_for('project.view_build_prompt', project_id=project.id))

    except Exception as e:
        current_app.logger.error(f'Build prompt generation error: {e}')
        flash(f'Erro ao gerar prompt: {str(e)}', 'danger')
        return redirect(url_for('project.wizard', project_id=project.id))


@project_bp.route('/project/<int:project_id>/build-prompt')
@login_required
def view_build_prompt(project_id):
    """View the generated build prompt."""
    project = db.session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        flash('Projeto não encontrado ou acesso negado.', 'danger')
        return redirect(url_for('project.dashboard'))

    if not project.completed:
        flash('Complete todas as fases do projeto primeiro.', 'warning')
        return redirect(url_for('project.wizard', project_id=project.id))

    # Read the prompt from file
    generator = OKFGenerator()
    proj_dir = generator._get_project_dir(project)
    prompt_path = os.path.join(proj_dir, 'build-prompt.md')

    prompt_text = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read()

    return render_template(
        'prompt.html',
        project=project,
        prompt_text=prompt_text,
    )


# ── Helper ──────────────────────────────────────────────────────────────────

def _extract_form_data(request, fields: list) -> dict:
    """
    Extract form fields from a request, including support for JSON list/dict
    payloads.  Simple text fields are taken as-is; any field suffixed with
    ``_json`` will be parsed from a JSON string.
    """
    data = {}
    for field in fields:
        value = request.form.get(field, '').strip()
        if not value:
            data[field] = None
            continue

        # If the field name ends with _json, attempt JSON parsing
        if field.endswith('_json') or field in ('tags', 'competitors'):
            try:
                data[field] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                data[field] = value
        else:
            data[field] = value

    return data
