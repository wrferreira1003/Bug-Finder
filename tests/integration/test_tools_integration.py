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