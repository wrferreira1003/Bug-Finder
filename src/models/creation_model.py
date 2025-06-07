from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CreationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY_REQUIRED = "retry_required"


class GitHubIssueCreation(BaseModel):
    repository_owner: str = Field(..., description="Proprietário do repositório")
    repository_name: str = Field(..., description="Nome do repositório")
    title: str = Field(..., description="Título da issue")
    body: str = Field(..., description="Corpo da issue em Markdown")
    labels: List[str] = Field(default_factory=list, description="Labels da issue")
    assignees: List[str] = Field(default_factory=list, description="Usuários assignados")
    milestone: Optional[int] = Field(None, description="Milestone da issue")
    
    # Dados de resposta do GitHub
    issue_number: Optional[int] = Field(None, description="Número da issue criada")
    issue_url: Optional[str] = Field(None, description="URL da issue criada")
    html_url: Optional[str] = Field(None, description="URL HTML da issue")
    api_response: Optional[Dict[str, Any]] = Field(None, description="Resposta completa da API")
    
    def get_github_payload(self) -> Dict[str, Any]:
        payload = {
            "title": self.title,
            "body": self.body
        }
        
        if self.labels:
            payload["labels"] = self.labels
        if self.assignees:
            payload["assignees"] = self.assignees
        if self.milestone:
            payload["milestone"] = self.milestone
            
        return payload
    
    def update_from_response(self, response: Dict[str, Any]) -> None:
        self.issue_number = response.get("number")
        self.issue_url = response.get("url")
        self.html_url = response.get("html_url")
        self.api_response = response


class CreationAttempt(BaseModel):
    attempt_number: int = Field(..., description="Número da tentativa")
    started_at: datetime = Field(default_factory=datetime.now, description="Timestamp de início")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de conclusão")
    status: CreationStatus = Field(CreationStatus.PENDING, description="Status da tentativa")
    
    # Dados da tentativa
    github_data: Optional[GitHubIssueCreation] = Field(None, description="Dados para criação no GitHub")
    
    # Resultado
    success: bool = Field(False, description="Se a tentativa foi bem-sucedida")
    error_message: Optional[str] = Field(None, description="Mensagem de erro")
    error_code: Optional[str] = Field(None, description="Código do erro")
    response_status_code: Optional[int] = Field(None, description="Código de status HTTP")
    
    # Métricas
    duration_ms: Optional[float] = Field(None, description="Duração da tentativa em milissegundos")
    rate_limit_remaining: Optional[int] = Field(None, description="Rate limit restante após a tentativa")
    
    def start_attempt(self) -> None:
        self.status = CreationStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def complete_attempt(self, success: bool, error_message: Optional[str] = None, error_code: Optional[str] = None, response_status_code: Optional[int] = None) -> None:
        self.completed_at = datetime.now()
        self.success = success
        self.status = CreationStatus.SUCCESS if success else CreationStatus.FAILED
        
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        
        if error_message:
            self.error_message = error_message
        if error_code:
            self.error_code = error_code
        if response_status_code:
            self.response_status_code = response_status_code
    
    def should_retry(self) -> bool:
        if self.success:
            return False
            
        # Retry para erros temporários
        retry_codes = [500, 502, 503, 504, 429]  # Server errors e rate limiting
        return self.response_status_code in retry_codes if self.response_status_code else True


class IssueCreationRequest(BaseModel):
    request_id: str = Field(..., description="ID único da solicitação")
    issue_id: str = Field(..., description="ID da issue interna")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp de criação")
    
    # Configuração
    max_attempts: int = Field(3, description="Máximo de tentativas")
    retry_delay_seconds: int = Field(5, description="Delay entre tentativas em segundos")
    
    # Status geral
    status: CreationStatus = Field(CreationStatus.PENDING, description="Status geral da criação")
    current_attempt: int = Field(0, description="Tentativa atual")
    
    # Tentativas
    attempts: List[CreationAttempt] = Field(default_factory=list, description="Lista de tentativas")
    
    # Resultado final
    final_issue_number: Optional[int] = Field(None, description="Número final da issue criada")
    final_issue_url: Optional[str] = Field(None, description="URL final da issue criada")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de conclusão")
    
    def create_attempt(self, github_data: GitHubIssueCreation) -> CreationAttempt:
        self.current_attempt += 1
        attempt = CreationAttempt(
            attempt_number=self.current_attempt,
            github_data=github_data
        )
        self.attempts.append(attempt)
        return attempt
    
    def get_last_attempt(self) -> Optional[CreationAttempt]:
        return self.attempts[-1] if self.attempts else None
    
    def mark_success(self, issue_number: int, issue_url: str) -> None:
        self.status = CreationStatus.SUCCESS
        self.final_issue_number = issue_number
        self.final_issue_url = issue_url
        self.completed_at = datetime.now()
    
    def mark_failed(self) -> None:
        self.status = CreationStatus.FAILED
        self.completed_at = datetime.now()
    
    def can_retry(self) -> bool:
        return (
            self.current_attempt < self.max_attempts and
            self.status != CreationStatus.SUCCESS and
            (not self.attempts or self.attempts[-1].should_retry())
        )
    
    def get_creation_summary(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "issue_id": self.issue_id,
            "status": self.status,
            "attempts_made": len(self.attempts),
            "max_attempts": self.max_attempts,
            "final_issue_number": self.final_issue_number,
            "final_issue_url": self.final_issue_url,
            "total_duration_ms": self._calculate_total_duration(),
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }
    
    def _calculate_total_duration(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds() * 1000
        return None
    
    def get_error_summary(self) -> Optional[Dict[str, Any]]:
        if self.status == CreationStatus.SUCCESS:
            return None
        
        failed_attempts = [attempt for attempt in self.attempts if not attempt.success]
        if not failed_attempts:
            return None
        
        error_counts = {}
        for attempt in failed_attempts:
            error_key = f"{attempt.error_code or 'unknown'}_{attempt.response_status_code or 'unknown'}"
            error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        return {
            "total_failed_attempts": len(failed_attempts),
            "error_distribution": error_counts,
            "last_error": {
                "message": failed_attempts[-1].error_message,
                "code": failed_attempts[-1].error_code,
                "status_code": failed_attempts[-1].response_status_code
            }
        }