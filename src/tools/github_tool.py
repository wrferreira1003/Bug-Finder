import os
import requests
from typing import Dict, Any, Optional
from github import Github
from dataclasses import dataclass
from src.models.issue_model import IssueModel

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
        self.client = Github(self.config.token)
        self.repo = None
        
    def _ensure_repo(self):
        """Garante que o repositório está inicializado"""
        if self.repo is None:
            self.repo = self.client.get_repo(self.config.repository)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com GitHub sem acessar repositório específico.
        
        Returns:
            Dict com resultado do teste
        """
        try:
            # Testa apenas a autenticação
            user = self.client.get_user()
            return {
                "success": True,
                "message": f"Conectado como: {user.login}",
                "user": user.login
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro de conexão: {str(e)}"
            }

    # Cria uma nova issue
    def create_issue(self, issue_data: IssueModel) -> None:
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
            self._ensure_repo()
            github_issue = self.repo.create_issue(
                title=issue_data.title,
                body=issue_data.github_body,
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
        
    # Atualiza uma issue existente
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
            self._ensure_repo()
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

    # Adiciona um comentário a uma issue
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
            self._ensure_repo()
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
        
    # Recupera informações de uma issue específica
    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Recupera informações de uma issue específica.
        
        Args:
            issue_number: Número da issue
            
        Returns:
            Dict com dados da issue
        """
        try:
            self._ensure_repo()
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

    # Lista issues do repositório
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
            self._ensure_repo()
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
