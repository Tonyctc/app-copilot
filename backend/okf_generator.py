""""""
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app


class OKFGenerator:
    """Generates OKF (Open Knowledge Format) markdown files with YAML frontmatter."""

    PHASE_NAMES = {
        0: 'inicio',
        1: 'descobrir',
        2: 'definir',
        3: 'desenvolver',
        4: 'entregar',
    }

    PHASE_TITLES = {
        1: 'Fase de Descoberta',
        2: 'Fase de Definição',
        3: 'Fase de Desenvolvimento',
        4: 'Fase de Entrega',
    }

    # Mapping of fields to display per phase
    PHASE_FIELDS = {
        1: {
            'title': 'Título',
            'description': 'Descrição do Projeto',
            'problem_statement': 'Declaração do Problema',
            'target_audience': 'Público-Alvo',
            'user_needs': 'Necessidades do Usuário',
            'competitors': 'Concorrentes',
            'constraints': 'Restrições',
            'research_methods': 'Métodos de Pesquisa',
            'key_findings': 'Principais Descobertas',
            'stakeholders': 'Partes Interessadas',
        },
        2: {
            'goals': 'Objetivos',
            'success_metrics': 'Métricas de Sucesso',
            'functional_requirements': 'Requisitos Funcionais',
            'non_functional_requirements': 'Requisitos Não-Funcionais',
            'user_stories': 'Histórias de Usuário',
            'use_cases': 'Casos de Uso',
            'scope': 'Escopo',
            'risks': 'Riscos',
        },
        3: {
            'architecture': 'Arquitetura',
            'technologies': 'Tecnologias',
            'data_model': 'Modelo de Dados',
            'api_endpoints': 'Endpoints da API',
            'wireframes': 'Wireframes',
            'user_flow': 'Fluxo do Usuário',
            'prototype_link': 'Link do Protótipo',
            'design_system': 'Sistema de Design',
        },
        4: {
            'deployment_plan': 'Plano de Implantação',
            'testing_strategy': 'Estratégia de Testes',
            'quality_assurance': 'Garantia de Qualidade',
            'training_plan': 'Plano de Treinamento',
            'support_plan': 'Plano de Suporte',
            'maintenance_plan': 'Plano de Manutenção',
            'budget': 'Orçamento',
            'timeline': 'Cronograma',
            'deliverables': 'Entregáveis',
        },
    }

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or current_app.config.get(
            'OKF_OUTPUT_DIR',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'okf_output'),
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Convert a project name to a safe directory name."""
        safe = ''.join(c if c.isalnum() or c in ('-', '_', ' ') else '_' for c in name)
        safe = safe.strip().replace(' ', '_').lower()
        return safe or 'projeto'

    def _get_project_dir(self, project) -> str:
        """Return the directory path for a given project's OKF files."""
        safe_name = self._sanitize_filename(project.name)
        return os.path.join(self.output_dir, f'proj_{project.id}_{safe_name}')

    def _yaml_frontmatter(self, project, phase: int, data: dict) -> str:
        """Build YAML frontmatter string for an OKF markdown file."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
        tags = data.get('tags', data.get('tags', []))
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        title_val = data.get('title', project.name)
        description_val = data.get('description', '')

        lines = [
            '---',
            f'type: "{self.PHASE_NAMES.get(phase, "desconhecido")}"',
            f'title: "{title_val}"',
            f'description: "{description_val}"',
        ]
        if tags:
            lines.append(f'tags: [{", ".join(tags)}]')
        lines.append(f'timestamp: "{now}"')
        lines.append(f'phase: {phase}')
        lines.append('---\n')
        return '\n'.join(lines)

    def _markdown_body(self, project, phase: int, data: dict) -> str:
        """Generate the markdown body for a given phase's OKF file."""
        phase_title = self.PHASE_TITLES.get(phase, f'Fase {phase}')
        lines = [
            f'# {phase_title}',
            '',
        ]

        fields = self.PHASE_FIELDS.get(phase, {})

        for key, label in fields.items():
            value = data.get(key)
            if value is None:
                continue

            # Determine heading level based on depth
            lines.append(f'## {label}')
            lines.append('')

            if isinstance(value, str):
                lines.append(value.strip())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            lines.append(f'- **{k}**: {v}')
                    else:
                        lines.append(f'- {item}')
            elif isinstance(value, dict):
                for k, v in value.items():
                    lines.append(f'- **{k}**: {v}')
            else:
                lines.append(str(value))

            lines.append('')
            lines.append('---')
            lines.append('')

        # Additional raw notes if present
        notes = data.get('notes') or data.get('observations') or data.get('additional_info')
        if notes:
            lines.append(f'## Informações Adicionais')
            lines.append('')
            if isinstance(notes, str):
                lines.append(notes)
            elif isinstance(notes, list):
                for n in notes:
                    lines.append(f'- {n}')
            lines.append('')

        return '\n'.join(lines)

    def generate_okf_file(self, project, phase: int, data: dict) -> str:
        """
        Create a single OKF markdown file for a given phase.

        Returns the full path to the created file.
        """
        proj_dir = self._get_project_dir(project)
        os.makedirs(proj_dir, exist_ok=True)

        phase_name = self.PHASE_NAMES.get(phase, 'desconhecido')
        filename = f'{phase_name}.md'
        filepath = os.path.join(proj_dir, filename)

        frontmatter = self._yaml_frontmatter(project, phase, data)
        body = self._markdown_body(project, phase, data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write('\n')
            f.write(body)
            f.write('\n')

        return filepath

    def generate_index(self, project) -> str:
        """
        Create an index.md file with navigation between all phases.

        Returns the full path to the created index file.
        """
        proj_dir = self._get_project_dir(project)
        os.makedirs(proj_dir, exist_ok=True)

        filepath = os.path.join(proj_dir, 'index.md')

        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

        lines = [
            '---',
            f'type: "index"',
            f'title: "{project.name}"',
            f'description: "Índice do projeto {project.name}"',
            f'tags: [projeto, índice]',
            f'timestamp: "{now}"',
            '---',
            '',
            f'# {project.name}',
            '',
            '## Navegação entre Fases',
            '',
        ]

        phase_entries = [
            (1, 'Descobrir', 'Fase de descoberta e pesquisa'),
            (2, 'Definir', 'Fase de definição de requisitos'),
            (3, 'Desenvolver', 'Fase de desenvolvimento e design'),
            (4, 'Entregar', 'Fase de entrega e implantação'),
        ]

        # Collect phase data to see which ones have content
        phase_data_map = {
            1: project.get_discovery_data(),
            2: project.get_definition_data(),
            3: project.get_development_data(),
            4: project.get_delivery_data(),
        }

        for phase_num, phase_name, phase_desc in phase_entries:
            status = '✓' if any(phase_data_map.get(phase_num, {})) else '○'
            filename = self.PHASE_NAMES[phase_num]
            lines.append(f'- [{status} {phase_name}]({filename}.md) — {phase_desc}')

        lines.append('')
        lines.append('---')
        lines.append('')

        # Summary section
        lines.append('## Resumo do Projeto')
        lines.append('')
        lines.append(f'- **Fase atual:** {project.phase_name}')
        lines.append(f'- **Concluído:** {"Sim" if project.completed else "Não"}')
        lines.append(f'- **Criado em:** {project.created_at.strftime("%d/%m/%Y %H:%M") if project.created_at else "N/A"}')
        lines.append(f'- **Última atualização:** {project.updated_at.strftime("%d/%m/%Y %H:%M") if project.updated_at else "N/A"}')
        lines.append('')

        # Add some metadata about the user
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            lines.append(f'> Gerado por: {current_user.username}')
        lines.append('')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return filepath

    def generate_bundle(self, project) -> list:
        """
        Generate all OKF files for a project.

        Returns a list of all created file paths.
        """
        created_files = []

        # Always generate index
        index_path = self.generate_index(project)
        created_files.append(index_path)

        # Generate files for each phase that has data
        phase_data_pairs = [
            (1, project.get_discovery_data()),
            (2, project.get_definition_data()),
            (3, project.get_development_data()),
            (4, project.get_delivery_data()),
        ]

        for phase_num, data in phase_data_pairs:
            if data and any(data.values()):
                filepath = self.generate_okf_file(project, phase_num, data)
                created_files.append(filepath)
            else:
                # Even empty phases get a placeholder file
                filepath = self.generate_okf_file(project, phase_num, data or {})
                created_files.append(filepath)

        return created_files

    def generate_build_prompt_text(self, project) -> str:
        """
        Generate a comprehensive build prompt from all project OKF data.
        Uses the ModelClient to call deepseek v4 flash via OpenCode Go.
        Falls back to local generation if API fails.
        """
        project_data = {
            'project_name': project.name,
            'discovery_data': project.get_discovery_data(),
            'definition_data': project.get_definition_data(),
            'development_data': project.get_development_data(),
            'delivery_data': project.get_delivery_data(),
        }

        from backend.model_client import ModelClient
        client = ModelClient()
        return client.generate_build_prompt(project_data)

    def export_zip(self, project) -> str:
        """
        Create a ZIP file containing all OKF files for a project.

        Returns the full path to the ZIP file.
        """
        # Ensure all files exist
        self.generate_bundle(project)

        proj_dir = self._get_project_dir(project)
        safe_name = self._sanitize_filename(project.name)
        zip_filename = f'{safe_name}_okf.zip'
        zip_path = os.path.join(self.output_dir, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(proj_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    arcname = os.path.relpath(file_path, proj_dir)
                    zf.write(file_path, arcname)

        return zip_path
