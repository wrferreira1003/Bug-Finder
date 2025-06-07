# Bug Finder - Fase 3: Desenvolvimento das Ferramentas

## 📋 Índice da Fase 3

1. [Conceitos Fundamentais das Ferramentas](#conceitos-fundamentais-das-ferramentas)
2. [Preparação do Ambiente](#preparação-do-ambiente)
3. [Ferramenta do GitHub](#ferramenta-do-github)
4. [Ferramenta do Discord](#ferramenta-do-discord)
5. [Testes de Integração](#testes-de-integração)
6. [Implementação Prática](#implementação-prática)

---

## 🔧 Conceitos Fundamentais das Ferramentas

### O que são Tools (Ferramentas) para Agentes?

Imagine que os agentes de IA são como **pessoas muito inteligentes**, mas que vivem apenas no mundo digital. Eles podem pensar, analisar e tomar decisões, mas não podem **agir diretamente** no mundo real.

As **ferramentas** são como "braços e pernas" digitais que permitem aos agentes:

- Criar issues no GitHub
- Enviar mensagens no Discord
- Acessar bancos de dados
- Fazer requisições HTTP
- Interagir com qualquer API externa

### Analogia Prática

```
Agente de IA = Cérebro brilhante
Ferramentas = Mãos para executar ações
API Externa = Mundo real onde as ações acontecem
```

### Como os Agentes Usam Ferramentas?

1. **Agente decide**: "Preciso criar uma issue no GitHub"
2. **Agente chama ferramenta**: `github_tool.create_issue(dados)`
3. **Ferramenta executa**: Faz requisição HTTP para API do GitHub
4. **Ferramenta retorna resultado**: Sucesso ou erro para o agente
5. **Agente processa resultado**: Decide próxima ação

### MCP (Model Context Protocol)

O **MCP** é um protocolo que padroniza como agentes de IA se comunicam com ferramentas externas. Pense nele como um "tradutor universal":

- **Antes do MCP**: Cada ferramenta tinha sua própria linguagem
- **Com MCP**: Todas as ferramentas "falam" a mesma linguagem
- **Benefício**: Agentes podem usar qualquer ferramenta facilmente

---

## 🛠️ Preparação do Ambiente

### Dependências Necessárias

Vamos adicionar as bibliotecas necessárias ao nosso `requirements.txt`:

```txt
# Dependências da Fase 3
requests>=2.31.0          # Para requisições HTTP
python-dotenv>=1.0.0      # Para variáveis de ambiente
PyGithub>=1.59.0          # Cliente Python para GitHub API
discord.py>=2.3.0         # Cliente Python para Discord API
pytest>=7.4.0            # Para testes
pytest-asyncio>=0.21.0   # Para testes assíncronos
mcp>=0.1.0               # Model Context Protocol
```

### Variáveis de Ambiente

Criaremos um arquivo `.env` para guardar nossas credenciais de forma segura:

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPOSITORY=seu-usuario/seu-repositorio

# Discord Configuration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxxxxxx/xxxxxxxx
DISCORD_CHANNEL_ID=123456789012345678

# API Configuration
API_RATE_LIMIT=60  # Requisições por minuto
API_TIMEOUT=30     # Timeout em segundos
```

### Como Obter as Credenciais

**GitHub Token:**

1. Acesse GitHub → Settings → Developer settings → Personal access tokens
2. Clique em "Generate new token (classic)"
3. Selecione scopes: `repo` (para criar issues)
4. Copie o token gerado

**Discord Webhook:**

1. No seu servidor Discord → Configurações do Canal
2. Integrações → Webhooks → Novo Webhook
3. Copie a URL do webhook

---

## 🐙 Ferramenta do GitHub

### Estrutura da Ferramenta GitHub

```python
# src/tools/github_tool.py

import os
import requests
from typing import Dict, Any, Optional
from github import Github
from dataclasses import dataclass
from src.models.issue_model import Issue

@dataclass
class GitHubConfig:
    """Configuração para integração com GitHub"""
    token: str
    repository: str
    base_url: str = "https://api.github.com"
    timeout: int = 30

class GitHubTool:
    """
    Ferramenta para interação com a API do GitHub.

    Esta classe encapsula todas as operações relacionadas ao GitHub,
    como criar issues, comentários, etc.
    """

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.client = Github(config.token)
        self.repo = self.client.get_repo(config.repository)

    def create_issue(self, issue_data: Issue) -> Dict[str, Any]:
        """
        Cria uma nova issue no GitHub.

        Args:
            issue_data: Dados estruturados da issue

        Returns:
            Dict contendo informações da issue criada

        Raises:
            GitHubAPIError: Se houver erro na criação
        """
        try:
            # Preparar dados da issue
            github_issue = self.repo.create_issue(
                title=issue_data.title,
                body=issue_data.description,
                labels=issue_data.labels or [],
                assignees=issue_data.assignees or []
            )

            return {
                "success": True,
                "issue_number": github_issue.number,
                "issue_url": github_issue.html_url,
                "issue_id": github_issue.id,
                "created_at": github_issue.created_at.isoformat(),
                "message": f"Issue #{github_issue.number} criada com sucesso"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao criar issue: {str(e)}"
            }

    def update_issue(self, issue_number: int, **kwargs) -> Dict[str, Any]:
        """
        Atualiza uma issue existente.

        Args:
            issue_number: Número da issue no GitHub
            **kwargs: Campos a serem atualizados

        Returns:
            Dict com resultado da operação
        """
        try:
            issue = self.repo.get_issue(issue_number)

            if 'title' in kwargs:
                issue.edit(title=kwargs['title'])
            if 'body' in kwargs:
                issue.edit(body=kwargs['body'])
            if 'state' in kwargs:
                issue.edit(state=kwargs['state'])
            if 'labels' in kwargs:
                issue.edit(labels=kwargs['labels'])

            return {
                "success": True,
                "message": f"Issue #{issue_number} atualizada com sucesso"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao atualizar issue: {str(e)}"
            }

    def add_comment(self, issue_number: int, comment: str) -> Dict[str, Any]:
        """
        Adiciona um comentário a uma issue.

        Args:
            issue_number: Número da issue
            comment: Texto do comentário

        Returns:
            Dict com resultado da operação
        """
        try:
            issue = self.repo.get_issue(issue_number)
            github_comment = issue.create_comment(comment)

            return {
                "success": True,
                "comment_id": github_comment.id,
                "comment_url": github_comment.html_url,
                "message": "Comentário adicionado com sucesso"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao adicionar comentário: {str(e)}"
            }

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Recupera informações de uma issue específica.

        Args:
            issue_number: Número da issue

        Returns:
            Dict com dados da issue
        """
        try:
            issue = self.repo.get_issue(issue_number)

            return {
                "success": True,
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "url": issue.html_url,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "labels": [label.name for label in issue.labels],
                    "assignees": [assignee.login for assignee in issue.assignees]
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao recuperar issue: {str(e)}"
            }

    def list_issues(self, state: str = "open", limit: int = 10) -> Dict[str, Any]:
        """
        Lista issues do repositório.

        Args:
            state: Estado das issues ('open', 'closed', 'all')
            limit: Número máximo de issues a retornar

        Returns:
            Dict com lista de issues
        """
        try:
            issues = self.repo.get_issues(state=state)
            issue_list = []

            for i, issue in enumerate(issues):
                if i >= limit:
                    break

                issue_list.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "url": issue.html_url,
                    "created_at": issue.created_at.isoformat(),
                    "labels": [label.name for label in issue.labels]
                })

            return {
                "success": True,
                "issues": issue_list,
                "total_count": len(issue_list)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao listar issues: {str(e)}"
            }

class GitHubAPIError(Exception):
    """Exceção personalizada para erros da API do GitHub"""
    pass
```

### Como a Ferramenta Funciona

1. **Configuração**: Recebe token e repositório
2. **Cliente**: Cria conexão com API do GitHub
3. **Métodos**: Cada ação (criar, atualizar, comentar) é um método
4. **Tratamento de Erros**: Sempre retorna sucesso/erro de forma estruturada
5. **Flexibilidade**: Aceita diferentes tipos de dados de entrada

---

## 💬 Ferramenta do Discord

### Estrutura da Ferramenta Discord

```python
# src/tools/discord_tool.py

import os
import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DiscordConfig:
    """Configuração para integração com Discord"""
    webhook_url: str
    channel_id: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3

class DiscordTool:
    """
    Ferramenta para envio de notificações via Discord.

    Suporta mensagens simples, embeds ricos e diferentes tipos
    de notificação para a equipe de desenvolvimento.
    """

    def __init__(self, config: DiscordConfig):
        self.config = config

    def send_bug_notification(
        self,
        issue_url: str,
        issue_title: str,
        severity: str,
        description: str,
        additional_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Envia notificação de bug para o Discord.

        Args:
            issue_url: URL da issue criada no GitHub
            issue_title: Título da issue
            severity: Criticidade do bug (high, medium, low)
            description: Descrição resumida do problema
            additional_info: Informações adicionais opcionais

        Returns:
            Dict com resultado da operação
        """

        # Cores baseadas na severidade
        color_map = {
            "high": 0xFF0000,    # Vermelho
            "medium": 0xFFA500,  # Laranja
            "low": 0xFFFF00      # Amarelo
        }

        # Emojis baseados na severidade
        emoji_map = {
            "high": "🚨",
            "medium": "⚠️",
            "low": "⚡"
        }

        embed = {
            "title": f"{emoji_map.get(severity, '🐛')} Novo Bug Detectado",
            "description": f"**{issue_title}**\n\n{description}",
            "color": color_map.get(severity, 0x808080),
            "fields": [
                {
                    "name": "Severidade",
                    "value": severity.upper(),
                    "inline": True
                },
                {
                    "name": "Issue GitHub",
                    "value": f"[Clique aqui para ver]({issue_url})",
                    "inline": True
                },
                {
                    "name": "Detectado em",
                    "value": datetime.now().strftime("%d/%m/%Y às %H:%M"),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Bug Finder System",
                "icon_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
            }
        }

        # Adicionar informações extras se fornecidas
        if additional_info:
            for key, value in additional_info.items():
                embed["fields"].append({
                    "name": key.replace('_', ' ').title(),
                    "value": str(value),
                    "inline": True
                })

        payload = {
            "embeds": [embed],
            "username": "Bug Finder Bot"
        }

        return self._send_webhook(payload)

    def send_simple_message(self, message: str, mention_users: List[str] = None) -> Dict[str, Any]:
        """
        Envia uma mensagem simples para o Discord.

        Args:
            message: Texto da mensagem
            mention_users: Lista de IDs de usuários para mencionar

        Returns:
            Dict com resultado da operação
        """
        content = message

        # Adicionar menções se especificadas
        if mention_users:
            mentions = " ".join([f"<@{user_id}>" for user_id in mention_users])
            content = f"{mentions}\n\n{message}"

        payload = {
            "content": content,
            "username": "Bug Finder Bot"
        }

        return self._send_webhook(payload)

    def send_status_update(self, status: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envia atualização de status do sistema.

        Args:
            status: Status atual (success, warning, error)
            details: Detalhes do status

        Returns:
            Dict com resultado da operação
        """

        status_config = {
            "success": {
                "color": 0x00FF00,
                "emoji": "✅",
                "title": "Sistema Funcionando"
            },
            "warning": {
                "color": 0xFFA500,
                "emoji": "⚠️",
                "title": "Atenção Necessária"
            },
            "error": {
                "color": 0xFF0000,
                "emoji": "❌",
                "title": "Erro no Sistema"
            }
        }

        config = status_config.get(status, status_config["warning"])

        embed = {
            "title": f"{config['emoji']} {config['title']}",
            "color": config["color"],
            "fields": [],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Bug Finder System Status"
            }
        }

        # Adicionar detalhes como campos
        for key, value in details.items():
            embed["fields"].append({
                "name": key.replace('_', ' ').title(),
                "value": str(value),
                "inline": True
            })

        payload = {
            "embeds": [embed],
            "username": "Bug Finder Bot"
        }

        return self._send_webhook(payload)

    def _send_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método interno para enviar webhook para o Discord.

        Args:
            payload: Dados da mensagem

        Returns:
            Dict com resultado da operação
        """
        headers = {
            "Content-Type": "application/json"
        }

        for attempt in range(self.config.retry_attempts):
            try:
                response = requests.post(
                    self.config.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout
                )

                if response.status_code == 204:
                    return {
                        "success": True,
                        "message": "Mensagem enviada com sucesso para o Discord",
                        "attempt": attempt + 1
                    }
                elif response.status_code == 429:
                    # Rate limit - tentar novamente
                    retry_after = response.json().get("retry_after", 1)
                    if attempt < self.config.retry_attempts - 1:
                        import time
                        time.sleep(retry_after)
                        continue
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "message": f"Erro ao enviar mensagem: {response.text}",
                        "attempt": attempt + 1
                    }

            except requests.exceptions.Timeout:
                if attempt < self.config.retry_attempts - 1:
                    continue
                return {
                    "success": False,
                    "error": "timeout",
                    "message": "Timeout ao enviar mensagem para Discord"
                }

            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Erro de rede: {str(e)}"
                }

        return {
            "success": False,
            "error": "max_retries_exceeded",
            "message": f"Falha após {self.config.retry_attempts} tentativas"
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com o Discord enviando mensagem de teste.

        Returns:
            Dict com resultado do teste
        """
        test_message = {
            "content": "🧪 Teste de conexão do Bug Finder - Sistema operacional!",
            "username": "Bug Finder Bot"
        }

        result = self._send_webhook(test_message)

        if result["success"]:
            result["message"] = "Conexão com Discord funcionando corretamente"

        return result

class DiscordAPIError(Exception):
    """Exceção personalizada para erros da API do Discord"""
    pass
```

---

## 🧪 Testes de Integração

### Estrutura dos Testes

```python
# tests/integration/test_tools_integration.py

import pytest
import os
from unittest.mock import Mock, patch
from src.tools.github_tool import GitHubTool, GitHubConfig
from src.tools.discord_tool import DiscordTool, DiscordConfig
from src.models.issue_model import Issue

class TestGitHubToolIntegration:
    """Testes de integração para a ferramenta GitHub"""

    @pytest.fixture
    def github_config(self):
        """Configuração de teste para GitHub"""
        return GitHubConfig(
            token="fake_token_for_testing",
            repository="test/repo"
        )

    @pytest.fixture
    def github_tool(self, github_config):
        """Instância da ferramenta GitHub para testes"""
        return GitHubTool(github_config)

    @pytest.fixture
    def sample_issue(self):
        """Issue de exemplo para testes"""
        return Issue(
            title="Bug de Teste",
            description="Descrição do bug de teste",
            labels=["bug", "high-priority"],
            assignees=["developer1"]
        )

    def test_github_tool_initialization(self, github_tool):
        """Testa se a ferramenta GitHub é inicializada corretamente"""
        assert github_tool.config.token == "fake_token_for_testing"
        assert github_tool.config.repository == "test/repo"

    @patch('github.Github')
    def test_create_issue_success(self, mock_github, github_tool, sample_issue):
        """Testa criação bem-sucedida de issue"""
        # Configurar mock
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.id = 456
        mock_issue.created_at.isoformat.return_value = "2025-01-01T10:00:00"

        mock_repo = Mock()
        mock_repo.create_issue.return_value = mock_issue

        mock_github.return_value.get_repo.return_value = mock_repo

        # Executar teste
        result = github_tool.create_issue(sample_issue)

        # Verificar resultado
        assert result["success"] is True
        assert result["issue_number"] == 123
        assert "github.com" in result["issue_url"]

    @patch('github.Github')
    def test_create_issue_failure(self, mock_github, github_tool, sample_issue):
        """Testa falha na criação de issue"""
        # Configurar mock para falhar
        mock_repo = Mock()
        mock_repo.create_issue.side_effect = Exception("API Error")

        mock_github.return_value.get_repo.return_value = mock_repo

        # Executar teste
        result = github_tool.create_issue(sample_issue)

        # Verificar resultado
        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["message"]

class TestDiscordToolIntegration:
    """Testes de integração para a ferramenta Discord"""

    @pytest.fixture
    def discord_config(self):
        """Configuração de teste para Discord"""
        return DiscordConfig(
            webhook_url="https://discord.com/api/webhooks/test/webhook"
        )

    @pytest.fixture
    def discord_tool(self, discord_config):
        """Instância da ferramenta Discord para testes"""
        return DiscordTool(discord_config)

    def test_discord_tool_initialization(self, discord_tool):
        """Testa se a ferramenta Discord é inicializada corretamente"""
        assert "discord.com" in discord_tool.config.webhook_url
        assert discord_tool.config.timeout == 30

    @patch('requests.post')
    def test_send_bug_notification_success(self, mock_post, discord_tool):
        """Testa envio bem-sucedido de notificação"""
        # Configurar mock para sucesso (Discord retorna 204)
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        # Executar teste
        result = discord_tool.send_bug_notification(
            issue_url="https://github.com/test/repo/issues/123",
            issue_title="Bug de Teste",
            severity="high",
            description="Descrição do bug"
        )

        # Verificar resultado
        assert result["success"] is True
        assert "sucesso" in result["message"]

        # Verificar se foi chamado corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "json" in call_args[1]
        assert "embeds" in call_args[1]["json"]

    @patch('requests.post')
    def test_send_notification_failure(self, mock_post, discord_tool):
        """Testa falha no envio de notificação"""
        # Configurar mock para falhar
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # Executar teste
        result = discord_tool.send_simple_message("Teste")

        # Verificar resultado
        assert result["success"] is False
        assert "error" in result

    @patch('requests.post')
    def test_rate_limit_handling(self, mock_post, discord_tool):
        """Testa tratamento de rate limit"""
        # Configurar mock para rate limit
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"retry_after": 0.1}
        mock_post.return_value = mock_response

        # Executar teste
        result = discord_tool.send_simple_message("Teste")

        # Verificar que tentou múltiplas vezes
        assert mock_post.call_count > 1
        assert result["success"] is False

class TestToolsInteraction:
    """Testa interação entre as ferramentas"""

    @pytest.fixture
    def tools_setup(self):
        """Configuração completa das ferramentas"""
        github_config = GitHubConfig(
            token="fake_token",
            repository="test/repo"
        )

        discord_config = DiscordConfig(
            webhook_url="https://discord.com/api/webhooks/test/webhook"
        )

        return {
            "github": GitHubTool(github_config),
            "discord": DiscordTool(discord_config)
        }

    @patch('github.Github')
    @patch('requests.post')
    def test_complete_workflow(self, mock_discord, mock_github, tools_setup):
        """Testa fluxo completo: criar issue + notificar Discord"""

        # Configurar mocks
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.id = 456
        mock_issue.created_at.isoformat.return_value = "2025-01-01T10:00:00"

        mock_repo = Mock()
        mock_repo.create_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        mock_discord_response = Mock()
        mock_discord_response.status_code = 204
        mock_discord.return_value = mock_discord_response

        # Criar issue
        sample_issue = Issue(
            title="Bug Completo",
            description="Teste de fluxo completo",
            labels=["bug"]
        )

        github_result = tools_setup["github"].create_issue(sample_issue)

        # Verificar sucesso na criação
        assert github_result["success"] is True
        issue_url = github_result["issue_url"]

        # Notificar Discord
        discord_result = tools_setup["discord"].send_bug_notification(
            issue_url=issue_url,
            issue_title=sample_issue.title,
            severity="medium",
            description=sample_issue.description
        )

        # Verificar sucesso na notificação
        assert discord_result["success"] is True

        # Verificar que ambas as APIs foram chamadas
        mock_repo.create_issue.assert_called_once()
        mock_discord.assert_called_once()

# Script para executar testes manualmente
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Testes Manuais

```python
# scripts/test_tools_manual.py

"""
Script para testar as ferramentas manualmente com APIs reais.
Use apenas em ambiente de desenvolvimento!
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.github_tool import GitHubTool, GitHubConfig
from tools.discord_tool import DiscordTool, DiscordConfig
from models.issue_model import Issue

def test_github_connection():
    """Testa conexão real com GitHub"""
    print("🔧 Testando conexão com GitHub...")

    config = GitHubConfig(
        token=os.getenv("GITHUB_TOKEN"),
        repository=os.getenv("GITHUB_REPOSITORY")
    )

    tool = GitHubTool(config)

    # Testar listagem de issues
    result = tool.list_issues(limit=5)

    if result["success"]:
        print(f"✅ Conexão OK! Encontradas {result['total_count']} issues")
        for issue in result["issues"]:
            print(f"  - #{issue['number']}: {issue['title']}")
    else:
        print(f"❌ Erro: {result['message']}")

    return result["success"]

def test_discord_connection():
    """Testa conexão real com Discord"""
    print("\n💬 Testando conexão com Discord...")

    config = DiscordConfig(
        webhook_url=os.getenv("DISCORD_WEBHOOK_URL")
    )

    tool = DiscordTool(config)

    # Testar conexão
    result = tool.test_connection()

    if result["success"]:
        print("✅ Conexão OK! Mensagem enviada para Discord")
    else:
        print(f"❌ Erro: {result['message']}")

    return result["success"]

def test_create_test_issue():
    """Cria uma issue de teste (cuidado - isso é real!)"""
    print("\n🐛 Criando issue de teste...")

    # Confirmar antes de criar
    confirm = input("Isso criará uma issue REAL no GitHub. Continuar? (y/N): ")
    if confirm.lower() != 'y':
        print("Teste cancelado.")
        return False

    config = GitHubConfig(
        token=os.getenv("GITHUB_TOKEN"),
        repository=os.getenv("GITHUB_REPOSITORY")
    )

    tool = GitHubTool(config)

    # Criar issue de teste
    test_issue = Issue(
        title="[TESTE] Bug Finder - Teste de Integração",
        description="""
## 🧪 Issue de Teste

Esta é uma issue criada automaticamente pelo sistema Bug Finder para testar a integração com GitHub.

### Detalhes do Teste
- **Sistema**: Bug Finder
- **Módulo**: Ferramenta GitHub
- **Objetivo**: Validar criação automática de issues

### ⚠️ Ação Necessária
Esta issue pode ser fechada imediatamente, pois é apenas um teste.

---
*Issue criada automaticamente pelo Bug Finder System*
        """,
        labels=["test", "bug-finder", "automation"]
    )

    result = tool.create_issue(test_issue)

    if result["success"]:
        print(f"✅ Issue criada: {result['issue_url']}")
        return result["issue_url"]
    else:
        print(f"❌ Erro: {result['message']}")
        return False

def test_full_workflow():
    """Testa fluxo completo: GitHub + Discord"""
    print("\n🔄 Testando fluxo completo...")

    # Criar issue
    issue_url = test_create_test_issue()
    if not issue_url:
        return False

    # Notificar Discord
    config = DiscordConfig(
        webhook_url=os.getenv("DISCORD_WEBHOOK_URL")
    )

    tool = DiscordTool(config)

    result = tool.send_bug_notification(
        issue_url=issue_url,
        issue_title="[TESTE] Bug Finder - Teste de Integração",
        severity="low",
        description="Esta é uma notificação de teste do sistema Bug Finder",
        additional_info={
            "sistema": "Bug Finder",
            "ambiente": "Desenvolvimento",
            "modulo": "Testes de Integração"
        }
    )

    if result["success"]:
        print("✅ Fluxo completo executado com sucesso!")
        print(f"   - Issue: {issue_url}")
        print("   - Discord: Notificação enviada")
        return True
    else:
        print(f"❌ Erro no Discord: {result['message']}")
        return False

def main():
    """Função principal do script de teste"""
    print("🚀 Bug Finder - Teste Manual das Ferramentas")
    print("=" * 50)

    # Carregar variáveis de ambiente
    load_dotenv()

    # Verificar se as variáveis estão configuradas
    required_vars = ["GITHUB_TOKEN", "GITHUB_REPOSITORY", "DISCORD_WEBHOOK_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("Configure o arquivo .env antes de executar os testes.")
        return

    # Executar testes
    github_ok = test_github_connection()
    discord_ok = test_discord_connection()

    if github_ok and discord_ok:
        print("\n🎉 Todas as conexões estão funcionando!")

        test_full = input("\nExecutar teste completo (criar issue + notificar)? (y/N): ")
        if test_full.lower() == 'y':
            test_full_workflow()
    else:
        print("\n❌ Algumas conexões falharam. Verifique as configurações.")

if __name__ == "__main__":
    main()
```

---

## 🎯 Implementação Prática

### Roteiro de Implementação

**Passo 1: Criar Estrutura Base**

```bash
mkdir -p src/tools
touch src/tools/__init__.py
touch src/tools/github_tool.py
touch src/tools/discord_tool.py
```

**Passo 2: Configurar Ambiente**

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env com suas credenciais
```

**Passo 3: Implementar GitHub Tool**

- Copiar código da GitHubTool
- Configurar credenciais
- Testar conexão

**Passo 4: Implementar Discord Tool**

- Copiar código da DiscordTool
- Configurar webhook
- Testar notificações

**Passo 5: Executar Testes**

```bash
python scripts/test_tools_manual.py
pytest tests/integration/test_tools_integration.py -v
```

### Próximos Passos

Com as ferramentas prontas, estaremos preparados para a **Fase 4: Desenvolvimento dos Agentes**, onde os agentes de IA utilizarão essas ferramentas para executar suas tarefas automaticamente.

### Conceitos Aprendidos

✅ **APIs e Integrações**: Como conectar Python com serviços externos  
✅ **Tratamento de Erros**: Como lidar com falhas de rede e API  
✅ **Configuração Segura**: Como gerenciar credenciais e variáveis de ambiente  
✅ **Testes de Integração**: Como validar conexões com serviços reais  
✅ **Estrutura de Dados**: Como organizar inputs e outputs das ferramentas  
✅ **Rate Limiting**: Como lidar com limites de requisições das APIs

---

_Na próxima fase, nossos agentes ganharão vida e começarão a usar essas ferramentas para automatizar o processo completo de tratamento de bugs!_
