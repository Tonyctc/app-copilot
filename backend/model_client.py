"""
Model client for OpenCode Go API (deepseek v4 flash).
Used to generate the build prompt from OKF data.
"""
import os
import json
import requests
from flask import current_app


class ModelClient:
    """Client for the OpenCode Go inference API."""

    BASE_URL = "https://opencode.ai/zen/go/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENCODE_GO_API_KEY", "")
        if not self.api_key:
            # Try current_app config
            try:
                from flask import current_app
                self.api_key = current_app.config.get("OPENCODE_GO_API_KEY", "")
            except Exception:
                self.api_key = ""
        self.base_url = self.BASE_URL

    def generate_build_prompt(self, project_data: dict) -> str:
        """
        Takes all project OKF data and generates a comprehensive build prompt
        with agentification instructions.

        project_data should contain:
        - discovery_data (dict)
        - definition_data (dict)
        - development_data (dict)
        - delivery_data (dict)
        - project_name (str)

        Returns the generated build prompt text.
        """
        # First, construct the system prompt
        system_prompt = """Você é um Arquiteto de Software Sênior especializado em transformar especificações de projetos em prompts de construção detalhados para agentes de IA codificadores (como Claude Code, Codex, Hermes Agent, OpenCode).

Sua tarefa é pegar os dados de especificação de um projeto (gerados via metodologia Double Diamond) e produzir um prompt de construção completo e acionável que um agente de IA possa seguir para implementar o projeto do zero.

Estruture o prompt final com estas seções obrigatórias:

## 1. VISÃO GERAL DO PROJETO
Resumo executivo do que será construído.

## 2. ESPECIFICAÇÃO TÉCNICA
- Stack de tecnologia (frontend, backend, banco de dados)
- Arquitetura do sistema
- Modelo de dados e entidades
- Regras de negócio
- Requisitos funcionais e não funcionais

## 3. PLANO DE IMPLEMENTAÇÃO (AGENTIFICAÇÃO)
Divida a implementação em fases, cada fase deve ser implementada por um subagente ou tarefa separada:

Fase 1: Setup do Projeto
- Inicializar repositório, configurar ambiente, dependências
- Usar TDD (Test-Driven Development)

Fase 2: Modelos e Banco de Dados
- Implementar modelos/entidades com SQLAlchemy ou ORM equivalente
- Migrations, seeds

Fase 3: API e Backend
- Rotas, controllers, autenticação
- Testes de API

Fase 4: Frontend
- Componentes, páginas, formulários
- Testes E2E

Fase 5: Integração e Deploy
- Conectar frontend e backend
- Testes de integração
- Configuração de deploy

## 4. INSTRUÇÕES PARA O AGENTE
- Use subagentes para paralelizar tarefas independentes
- Sempre escreva testes antes do código (TDD)
- Faça commits frequentes com mensagens descritivas
- Use a skill test-driven-development para cada nova funcionalidade
- Use subagent-driven-development para tarefas complexas
- Execute os testes após cada mudança
- Mantenha o código limpo e modular

## 5. CRITÉRIOS DE ACEITE
Lista de verificação do que constitui uma implementação bem-sucedida.
"""

        # Construct the user prompt with project data
        user_prompt = self._build_project_prompt(project_data)

        # Try to call the API
        try:
            return self._call_api(system_prompt, user_prompt)
        except Exception as e:
            # Fallback: generate a prompt locally
            return self._build_fallback_prompt(project_data)

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call the OpenCode Go API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 8192,
            "temperature": 0.3,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API returned {response.status_code}: {response.text}")

    def _build_project_prompt(self, data: dict) -> str:
        """Build the project data string for the API call."""
        parts = [f"# PROJETO: {data.get('project_name', 'Projeto Sem Nome')}"]
        parts.append("")

        # Discovery phase
        discovery = data.get("discovery_data", {})
        if discovery:
            parts.append("## FASE 1 — DESCOBERTA")
            for key, value in discovery.items():
                if value:
                    label = key.replace("_", " ").title()
                    parts.append(f"### {label}")
                    parts.append(str(value))
                    parts.append("")

        # Definition phase
        definition = data.get("definition_data", {})
        if definition:
            parts.append("## FASE 2 — DEFINIÇÃO")
            for key, value in definition.items():
                if value:
                    label = key.replace("_", " ").title()
                    parts.append(f"### {label}")
                    parts.append(str(value))
                    parts.append("")

        # Development phase
        development = data.get("development_data", {})
        if development:
            parts.append("## FASE 3 — DESENVOLVIMENTO")
            for key, value in development.items():
                if value:
                    label = key.replace("_", " ").title()
                    parts.append(f"### {label}")
                    parts.append(str(value))
                    parts.append("")

        # Delivery phase
        delivery = data.get("delivery_data", {})
        if delivery:
            parts.append("## FASE 4 — ENTREGA")
            for key, value in delivery.items():
                if value:
                    label = key.replace("_", " ").title()
                    parts.append(f"### {label}")
                    parts.append(str(value))
                    parts.append("")

        # Final instruction
        parts.append("---")
        parts.append(
            "Com base nos dados acima, gere o prompt completo de construção do sistema "
            "conforme as seções definidas na instrução do sistema. Inclua todas as seções: "
            "Visão Geral, Especificação Técnica, Plano de Implementação (com agentificação), "
            "Instruções para o Agente e Critérios de Aceite."
        )

        return "\n".join(parts)

    def _build_fallback_prompt(self, data: dict) -> str:
        """Generate a build prompt locally without API call (fallback)."""
        name = data.get("project_name", "MeuApp")
        discovery = data.get("discovery_data", {})
        definition = data.get("definition_data", {})
        development = data.get("development_data", {})
        delivery = data.get("delivery_data", {})

        from datetime import datetime

        return f"""---
title: "Prompt de Construção: {name}"
description: "Prompt completo gerado a partir do bundle OKF para agentes de IA codificadores"
type: "build-prompt"
generated_at: "{datetime.now().isoformat()}"
---

# PROMPT DE CONSTRUÇÃO: {name}

## 1. VISÃO GERAL DO PROJETO

{discovery.get('main_goal', '') or discovery.get('description', '') or 'Aplicação web definida através da metodologia Double Diamond.'}

> Público-alvo: {discovery.get('target_audience', 'Não especificado')}
> Dores resolvidas: {discovery.get('pain_points', 'Não especificado')}

## 2. ESPECIFICAÇÃO TÉCNICA

### Stack de Tecnologia
- **Frontend:** {development.get('frontend_tech', 'A definir')}
- **Backend:** {development.get('backend_tech', 'A definir')}
- **Estilo/UX:** {development.get('visual_style', 'A definir')}

### Funcionalidades
{definition.get('functional_requirements', 'Não especificado')}

### Requisitos Não Funcionais
{definition.get('non_functional_requirements', 'Não especificado')}

### Regras de Negócio
{development.get('business_rules', 'Não especificado')}

### Modelo de Dados
**Entidades:** {development.get('database_entities', 'Não especificado')}

**Atributos e Relacionamentos:**
{development.get('attributes_relationships', 'Não especificado')}

### Fluxo de Telas
{development.get('screen_flow', 'Não especificado')}

## 3. PLANO DE IMPLEMENTAÇÃO (AGENTIFICAÇÃO)

### Fase 1: Setup e Configuração
1. Inicializar repositório git
2. Configurar ambiente de desenvolvimento (venv, dependências)
3. Configurar linting e formatação
4. Criar estrutura de diretórios
5. **Commit inicial:** `git commit -m "chore: initial project setup"`

### Fase 2: Modelos e Banco de Dados (TDD)
1. Escrever testes para modelos
2. Implementar modelos/entidades
3. Configurar migrations
4. **Commit:** `git commit -m "feat: add database models"`

### Fase 3: Backend API (TDD)
1. Escrever testes de API
2. Implementar rotas e controllers
3. Implementar autenticação/autorização
4. Implementar regras de negócio
5. **Commit:** `git commit -m "feat: implement API endpoints"`

### Fase 4: Frontend (TDD)
1. Configurar projeto frontend
2. Implementar componentes/páginas
3. Conectar com API
4. Implementar formulários e validação
5. **Commit:** `git commit -m "feat: implement frontend"`

### Fase 5: Integração e Testes
1. Testes de integração (E2E)
2. Correção de bugs
3. Otimização de performance
4. **Commit:** `git commit -m "test: add integration tests"`

## 4. INSTRUÇÕES PARA O AGENTE DE CÓDIGO

### Uso de Subagentes
- Para cada fase do plano, dispare um subagente dedicado usando `delegate_task`
- Subagentes trabalham em paralelo quando as tarefas são independentes
- Cada subagente recebe contexto completo da fase e referências às fases anteriores

### Metodologia TDD
- **SEMPRE** escreva o teste primeiro (RED)
- Implemente o código mínimo para passar (GREEN)
- Refatore mantendo os testes verdes (REFACTOR)
- Use a skill `test-driven-development` para orientação

### Boas Práticas
- Commits frequentes e descritivos (conventional commits)
- Código limpo e modular (SRP, DRY)
- Documentação de funções públicas
- Tratamento de erros em todas as camadas
- Logs estruturados para debug

### Ferramentas
- Use `terminal` para comandos shell
- Use `write_file` e `patch` para criar/editar arquivos
- Use `read_file` para inspecionar arquivos existentes
- Use `search_files` para encontrar padrões no código
- Use `browser_navigate` + `browser_snapshot` para testar UI

## 5. CRITÉRIOS DE ACEITE

- [ ] Todos os testes passam (pytest, cobertura > 80%)
- [ ] API responde corretamente em todos os endpoints
- [ ] Frontend renderiza sem erros no console
- [ ] Fluxo completo do usuário funciona (E2E)
- [ ] Código segue boas práticas (lint free)
- [ ] README com instruções de setup
- [ ] Tratamento de erros implementado
- [ ] Segurança: sem vazamento de secrets, inputs sanitizados
"""
