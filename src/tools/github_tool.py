import os
from typing import Optional, Dict, Any, List
from github import Github, GithubException
from github.Repository import Repository
from github.Issue import Issue
import logging

from ..models.creation_model import GitHubIssueCreation, CreationAttempt


class GitHubTool:
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("GITHUB_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("GitHub access token is required. Set GITHUB_ACCESS_TOKEN environment variable.")
        
        self.github = Github(self.access_token)
        self.logger = logging.getLogger(__name__)
    
    def get_repository(self, owner: str, repo_name: str) -> Repository:
        try:
            return self.github.get_repo(f"{owner}/{repo_name}")
        except GithubException as e:
            self.logger.error(f"Failed to get repository {owner}/{repo_name}: {e}")
            raise
    
    def create_issue(self, creation_data: GitHubIssueCreation, attempt: CreationAttempt) -> bool:
        attempt.start_attempt()
        
        try:
            # Obter repositório
            repo = self.get_repository(creation_data.repository_owner, creation_data.repository_name)
            
            # Preparar dados para criação
            payload = creation_data.get_github_payload()
            self.logger.info(f"Creating GitHub issue: {payload['title']}")
            
            # Criar issue
            issue = repo.create_issue(**payload)
            
            # Atualizar dados de criação com resposta
            response_data = {
                "number": issue.number,
                "url": issue.url,
                "html_url": issue.html_url,
                "id": issue.id,
                "state": issue.state,
                "created_at": issue.created_at.isoformat() if issue.created_at else None
            }
            
            creation_data.update_from_response(response_data)
            
            # Completar tentativa com sucesso
            attempt.complete_attempt(
                success=True,
                response_status_code=201
            )
            
            self.logger.info(f"Successfully created GitHub issue #{issue.number}: {issue.html_url}")
            return True
            
        except GithubException as e:
            error_message = f"GitHub API error: {e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}"
            error_code = str(e.status) if hasattr(e, 'status') else "unknown"
            
            attempt.complete_attempt(
                success=False,
                error_message=error_message,
                error_code=error_code,
                response_status_code=e.status if hasattr(e, 'status') else None
            )
            
            self.logger.error(f"Failed to create GitHub issue: {error_message}")
            return False
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            
            attempt.complete_attempt(
                success=False,
                error_message=error_message,
                error_code="unexpected_error"
            )
            
            self.logger.error(f"Unexpected error creating GitHub issue: {error_message}")
            return False
    
    def get_issue(self, owner: str, repo_name: str, issue_number: int) -> Optional[Issue]:
        try:
            repo = self.get_repository(owner, repo_name)
            return repo.get_issue(issue_number)
        except GithubException as e:
            self.logger.error(f"Failed to get issue #{issue_number}: {e}")
            return None
    
    def update_issue(self, owner: str, repo_name: str, issue_number: int, 
                    title: Optional[str] = None, body: Optional[str] = None, 
                    state: Optional[str] = None, labels: Optional[List[str]] = None,
                    assignees: Optional[List[str]] = None) -> bool:
        try:
            repo = self.get_repository(owner, repo_name)
            issue = repo.get_issue(issue_number)
            
            # Preparar argumentos para atualização
            update_kwargs = {}
            if title is not None:
                update_kwargs['title'] = title
            if body is not None:
                update_kwargs['body'] = body
            if state is not None:
                update_kwargs['state'] = state
            if labels is not None:
                update_kwargs['labels'] = labels
            if assignees is not None:
                update_kwargs['assignees'] = assignees
            
            # Atualizar issue
            issue.edit(**update_kwargs)
            
            self.logger.info(f"Successfully updated GitHub issue #{issue_number}")
            return True
            
        except GithubException as e:
            self.logger.error(f"Failed to update GitHub issue #{issue_number}: {e}")
            return False
    
    def add_comment(self, owner: str, repo_name: str, issue_number: int, comment: str) -> bool:
        try:
            repo = self.get_repository(owner, repo_name)
            issue = repo.get_issue(issue_number)
            issue.create_comment(comment)
            
            self.logger.info(f"Successfully added comment to GitHub issue #{issue_number}")
            return True
            
        except GithubException as e:
            self.logger.error(f"Failed to add comment to GitHub issue #{issue_number}: {e}")
            return False
    
    def search_issues(self, owner: str, repo_name: str, query: str, 
                     state: str = "open", sort: str = "created", 
                     order: str = "desc", per_page: int = 30) -> List[Dict[str, Any]]:
        try:
            # Construir query de busca
            search_query = f"repo:{owner}/{repo_name} is:issue state:{state} {query}"
            
            # Realizar busca
            issues = self.github.search_issues(
                query=search_query,
                sort=sort,
                order=order
            )
            
            # Converter para lista de dicionários
            results = []
            for issue in issues[:per_page]:  # Limitar resultados
                results.append({
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "html_url": issue.html_url,
                    "labels": [label.name for label in issue.labels],
                    "assignees": [assignee.login for assignee in issue.assignees]
                })
            
            self.logger.info(f"Found {len(results)} issues matching query: {query}")
            return results
            
        except GithubException as e:
            self.logger.error(f"Failed to search issues: {e}")
            return []
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        try:
            rate_limit = self.github.get_rate_limit()
            return {
                "core": {
                    "limit": rate_limit.core.limit,
                    "remaining": rate_limit.core.remaining,
                    "reset": rate_limit.core.reset.isoformat() if rate_limit.core.reset else None
                },
                "search": {
                    "limit": rate_limit.search.limit,
                    "remaining": rate_limit.search.remaining,
                    "reset": rate_limit.search.reset.isoformat() if rate_limit.search.reset else None
                }
            }
        except GithubException as e:
            self.logger.error(f"Failed to get rate limit info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        try:
            user = self.github.get_user()
            self.logger.info(f"GitHub connection test successful. Authenticated as: {user.login}")
            return True
        except GithubException as e:
            self.logger.error(f"GitHub connection test failed: {e}")
            return False
    
    def validate_repository_access(self, owner: str, repo_name: str) -> Dict[str, Any]:
        try:
            repo = self.get_repository(owner, repo_name)
            
            # Verificar permissões
            permissions = repo.permissions
            
            return {
                "exists": True,
                "has_issues": repo.has_issues,
                "permissions": {
                    "admin": permissions.admin if permissions else False,
                    "push": permissions.push if permissions else False,
                    "pull": permissions.pull if permissions else False
                },
                "can_create_issues": repo.has_issues and (permissions.push if permissions else False)
            }
            
        except GithubException as e:
            return {
                "exists": False,
                "error": str(e),
                "can_create_issues": False
            }