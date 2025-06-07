"""
Modelo para representar o resultado da criação de issues no GitHub.
Define estruturas para tracking do processo de criação e metadados.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class CreationStatus(Enum):
    """Status possíveis da criação da issue"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    GITHUB_ERROR = "github_error"


class IssueState(Enum):
    """Estados da issue no GitHub"""
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class GitHubIssueData:
    """Dados específicos da issue criada no GitHub"""
    issue_id: int
    issue_number: int
    issue_url: str
    html_url: str
    state: IssueState
    created_at: str
    updated_at: str
    
    # Dados do repositório
    repository_name: str
    repository_owner: str
    repository_full_name: str
    
    # Metadados adicionais
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    milestone: Optional[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.assignees is None:
            self.assignees = []


@dataclass
class CreationAttempt:
    """Registro de uma tentativa de criação"""
    attempt_number: int
    timestamp: str
    status: CreationStatus
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = None


@dataclass
class IssueCreationResult:
    """Resultado completo da criação de uma issue"""
    # Status da operação
    status: CreationStatus
    success: bool
    
    # Dados da issue (se criada com sucesso)
    github_data: Optional[GitHubIssueData] = None
    github_issue: Optional[GitHubIssueData] = None  # Compatibility alias
    
    # Compatibility fields for existing agent code
    issue_draft_id: Optional[str] = None
    created_at: Optional[str] = None
    message: Optional[str] = None
    
    # Histórico de tentativas
    attempts: Optional[List[CreationAttempt]] = None
    
    # Metadados do processo
    creator_agent: str = "IssueCreatorAgent"
    creation_timestamp: Optional[str] = None
    total_attempts: int = 0
    
    # Informações de erro (se houver)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Dados originais da issue
    original_title: str = ""
    original_body: str = ""
    original_labels: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []
        if self.original_labels is None:
            self.original_labels = []
        if self.creation_timestamp is None:
            self.creation_timestamp = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = self.creation_timestamp
        if self.github_issue is None:
            self.github_issue = self.github_data
        self.success = self.status == CreationStatus.SUCCESS
    
    def add_attempt(self, attempt: CreationAttempt):
        """Adiciona uma nova tentativa ao histórico"""
        self.attempts.append(attempt)
        self.total_attempts = len(self.attempts)
        self.status = attempt.status
        
        if attempt.status == CreationStatus.SUCCESS:
            self.success = True
        elif attempt.status == CreationStatus.FAILED:
            self.error_message = attempt.error_message
    
    def get_issue_url(self) -> Optional[str]:
        """Retorna a URL da issue se criada com sucesso"""
        if self.github_data:
            return self.github_data.html_url
        return None
    
    def get_creation_summary(self) -> str:
        """Retorna um resumo da criação"""
        if self.success:
            return f"✅ Issue criada com sucesso: {self.get_issue_url()}"
        else:
            return f"❌ Falha na criação: {self.error_message}"
    
    def is_retryable(self) -> bool:
        """Verifica se a operação pode ser tentada novamente"""
        retryable_statuses = [
            CreationStatus.RATE_LIMITED,
            CreationStatus.FAILED
        ]
        return self.status in retryable_statuses and self.total_attempts < 3


@dataclass
class CreationConfig:
    """Configurações para criação de issues"""
    # Configurações do repositório
    repository_owner: str
    repository_name: str
    
    # Configurações de retry
    max_attempts: int = 3
    retry_delay_seconds: int = 60
    
    # Labels padrão
    default_labels: Optional[List[str]] = None
    
    # Template de issue
    issue_template: Optional[str] = None
    
    # Configurações de rate limiting
    respect_rate_limits: bool = True
    rate_limit_buffer: int = 10  # requests para deixar de buffer
    
    def __post_init__(self):
        if self.default_labels is None:
            self.default_labels = ["bug", "automated"]


@dataclass
class CreationMetrics:
    """Métricas de criação de issues"""
    total_attempts: int = 0
    successful_creations: int = 0
    failed_creations: int = 0
    rate_limited_attempts: int = 0
    average_creation_time: float = 0.0
    
    def success_rate(self) -> float:
        """Taxa de sucesso"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_creations / self.total_attempts) * 100
    
    def update_metrics(self, result: IssueCreationResult):
        """Atualiza métricas com novo resultado"""
        self.total_attempts += result.total_attempts
        
        if result.success:
            self.successful_creations += 1
        else:
            self.failed_creations += 1
        
        # Conta tentativas com rate limit
        rate_limited = sum(
            1 for attempt in result.attempts 
            if attempt.status == CreationStatus.RATE_LIMITED
        )
        self.rate_limited_attempts += rate_limited
        
        # Calcula tempo médio (se disponível)
        creation_times = [
            attempt.duration_seconds 
            for attempt in result.attempts 
            if attempt.duration_seconds is not None
        ]
        
        if creation_times:
            avg_time = sum(creation_times) / len(creation_times)
            total_ops = self.successful_creations + self.failed_creations
            if total_ops > 1:
                self.average_creation_time = (
                    (self.average_creation_time * (total_ops - 1) + avg_time) 
                    / total_ops
                )
            else:
                self.average_creation_time = avg_time