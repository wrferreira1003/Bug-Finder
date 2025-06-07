"""
Modelo para representar o processo completo do Bug Finder.
Define estruturas para tracking de todo o fluxo desde log até notificação.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from .log_model import LogModel
from .bug_analysis import BugAnalysis, BugSeverity
from .issue_model import IssueModel
from .review_model import IssueReview
from .creation_model import IssueCreationResult
from .notification_model import NotificationResult


class ProcessStatus(Enum):
    """Status possíveis do processo completo"""
    STARTED = "started"
    LOG_RECEIVED = "log_received"
    ANALYSIS_IN_PROGRESS = "analysis_in_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    DRAFT_IN_PROGRESS = "draft_in_progress"
    DRAFT_COMPLETED = "draft_completed"
    REVIEW_IN_PROGRESS = "review_in_progress"
    REVIEW_COMPLETED = "review_completed"
    REFINEMENT_IN_PROGRESS = "refinement_in_progress"
    REFINEMENT_COMPLETED = "refinement_completed"
    CREATION_IN_PROGRESS = "creation_in_progress"
    CREATION_COMPLETED = "creation_completed"
    NOTIFICATION_IN_PROGRESS = "notification_in_progress"
    NOTIFICATION_COMPLETED = "notification_completed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessResult(Enum):
    """Resultado final do processo"""
    SUCCESS = "success"
    NOT_A_BUG = "not_a_bug"
    LOW_PRIORITY = "low_priority"
    FAILED_ANALYSIS = "failed_analysis"
    FAILED_CREATION = "failed_creation"
    FAILED_NOTIFICATION = "failed_notification"
    SYSTEM_ERROR = "system_error"


@dataclass
class ProcessStep:
    """Representa um passo no processo"""
    step_name: str
    agent_name: str
    status: ProcessStatus
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def complete_step(self, success: bool = True, error_message: Optional[str] = None):
        """Marca o passo como completo"""
        self.end_time = datetime.now().isoformat()
        self.success = success
        self.error_message = error_message
        
        if self.end_time and self.start_time:
            start_dt = datetime.fromisoformat(self.start_time)
            end_dt = datetime.fromisoformat(self.end_time)
            self.duration_seconds = (end_dt - start_dt).total_seconds()


@dataclass
class ProcessContext:
    """Contexto compartilhado entre todos os agentes"""
    # Identificação do processo
    process_id: str
    session_id: Optional[str] = None
    
    # Dados do log original
    original_log: Optional[LogModel] = None
    
    # Resultados de cada etapa
    bug_analysis: Optional[BugAnalysis] = None
    issue_draft: Optional[IssueModel] = None
    issue_reviews: List[IssueReview] = None
    final_issue: Optional[IssueModel] = None
    creation_result: Optional[IssueCreationResult] = None
    notification_result: Optional[NotificationResult] = None
    
    # Metadados do processo
    configuration: Optional[Dict[str, Any]] = None
    environment: str = "production"
    
    def __post_init__(self):
        if self.issue_reviews is None:
            self.issue_reviews = []
        if self.configuration is None:
            self.configuration = {}
    
    def add_review(self, review: IssueReview):
        """Adiciona uma nova revisão ao contexto"""
        self.issue_reviews.append(review)
    
    def get_latest_review(self) -> Optional[IssueReview]:
        """Retorna a revisão mais recente"""
        if self.issue_reviews:
            return self.issue_reviews[-1]
        return None
    
    def get_review_count(self) -> int:
        """Retorna o número de revisões realizadas"""
        return len(self.issue_reviews)


@dataclass
class BugFinderProcess:
    """Representa o processo completo do Bug Finder"""
    # Identificação
    process_id: str
    start_time: str
    end_time: Optional[str] = None
    
    # Status e resultado
    current_status: ProcessStatus = ProcessStatus.STARTED
    final_result: Optional[ProcessResult] = None
    
    # Contexto compartilhado
    context: Optional[ProcessContext] = None
    
    # Histórico de passos
    steps: List[ProcessStep] = None
    
    # Métricas de performance
    total_duration_seconds: Optional[float] = None
    steps_completed: int = 0
    steps_failed: int = 0
    
    # Informações de erro
    error_step: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.context is None:
            self.context = ProcessContext(process_id=self.process_id)
    
    def add_step(self, step: ProcessStep):
        """Adiciona um passo ao processo"""
        self.steps.append(step)
        
        if step.success:
            self.steps_completed += 1
        else:
            self.steps_failed += 1
    
    def update_status(self, status: ProcessStatus):
        """Atualiza o status atual do processo"""
        self.current_status = status
    
    def complete_process(self, result: ProcessResult, error_message: Optional[str] = None):
        """Marca o processo como completo"""
        self.end_time = datetime.now().isoformat()
        self.final_result = result
        
        if result == ProcessResult.SUCCESS:
            self.current_status = ProcessStatus.COMPLETED
        else:
            self.current_status = ProcessStatus.FAILED
            self.error_message = error_message
        
        # Calcula duração total
        if self.end_time:
            start_dt = datetime.fromisoformat(self.start_time)
            end_dt = datetime.fromisoformat(self.end_time)
            self.total_duration_seconds = (end_dt - start_dt).total_seconds()
    
    def is_completed(self) -> bool:
        """Verifica se o processo foi completado"""
        return self.current_status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED]
    
    def is_successful(self) -> bool:
        """Verifica se o processo foi bem-sucedido"""
        return self.final_result == ProcessResult.SUCCESS
    
    def get_current_step(self) -> Optional[ProcessStep]:
        """Retorna o passo atual (último adicionado)"""
        if self.steps:
            return self.steps[-1]
        return None
    
    def get_step_by_name(self, step_name: str) -> Optional[ProcessStep]:
        """Busca um passo pelo nome"""
        for step in self.steps:
            if step.step_name == step_name:
                return step
        return None
    
    def get_failed_steps(self) -> List[ProcessStep]:
        """Retorna lista de passos que falharam"""
        return [step for step in self.steps if not step.success]
    
    def get_process_summary(self) -> str:
        """Retorna um resumo do processo"""
        if self.is_successful():
            issue_url = ""
            if self.context.creation_result and self.context.creation_result.success:
                issue_url = self.context.creation_result.get_issue_url()
            
            return f"✅ Processo concluído com sucesso em {self.total_duration_seconds:.2f}s\n🔗 Issue criada: {issue_url}"
        
        elif self.final_result == ProcessResult.NOT_A_BUG:
            return "ℹ️ Log analisado - não é um bug que requer issue"
        
        elif self.final_result == ProcessResult.LOW_PRIORITY:
            return "⚪ Bug identificado mas de baixa prioridade - issue não criada"
        
        else:
            return f"❌ Processo falhou: {self.error_message}"
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance do processo"""
        metrics = {
            "total_duration": self.total_duration_seconds,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "success_rate": (self.steps_completed / len(self.steps)) * 100 if self.steps else 0,
            "final_result": self.final_result.value if self.final_result else None
        }
        
        # Adiciona duração por passo
        step_durations = {}
        for step in self.steps:
            if step.duration_seconds:
                step_durations[step.step_name] = step.duration_seconds
        
        metrics["step_durations"] = step_durations
        
        return metrics


@dataclass
class ProcessConfig:
    """Configuração para o processo do Bug Finder"""
    # Configurações gerais
    max_review_iterations: int = 3
    auto_approve_threshold: int = 4  # Score mínimo para aprovação automática
    
    # Configurações de timeout
    step_timeout_seconds: int = 300  # 5 minutos por passo
    total_timeout_seconds: int = 1800  # 30 minutos total
    
    # Configurações de criticidade
    minimum_severity: BugSeverity = BugSeverity.MEDIUM
    create_issue_for_low_priority: bool = False
    
    # Configurações de retry
    retry_failed_steps: bool = True
    max_retries_per_step: int = 2
    
    # Configurações de logging
    log_all_steps: bool = True
    log_agent_communications: bool = False
    
    # Configurações de notificação
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    notify_on_critical_bugs: bool = True


@dataclass
class ProcessMetrics:
    """Métricas globais do Bug Finder"""
    total_processes: int = 0
    successful_processes: int = 0
    failed_processes: int = 0
    not_bug_processes: int = 0
    low_priority_processes: int = 0
    
    average_duration: float = 0.0
    average_steps_per_process: float = 0.0
    
    # Métricas por severidade
    processes_by_severity: Dict[BugSeverity, int] = None
    
    # Métricas por resultado
    processes_by_result: Dict[ProcessResult, int] = None
    
    def __post_init__(self):
        if self.processes_by_severity is None:
            self.processes_by_severity = {}
        if self.processes_by_result is None:
            self.processes_by_result = {}
    
    def success_rate(self) -> float:
        """Taxa de sucesso geral"""
        if self.total_processes == 0:
            return 0.0
        return (self.successful_processes / self.total_processes) * 100
    
    def update_metrics(self, process: BugFinderProcess):
        """Atualiza métricas com novo processo"""
        self.total_processes += 1
        
        # Atualiza contadores por resultado
        if process.final_result:
            self.processes_by_result[process.final_result] = (
                self.processes_by_result.get(process.final_result, 0) + 1
            )
            
            if process.final_result == ProcessResult.SUCCESS:
                self.successful_processes += 1
            elif process.final_result == ProcessResult.NOT_A_BUG:
                self.not_bug_processes += 1
            elif process.final_result == ProcessResult.LOW_PRIORITY:
                self.low_priority_processes += 1
            else:
                self.failed_processes += 1
        
        # Atualiza métricas por severidade
        if process.context.bug_analysis and process.context.bug_analysis.severity:
            severity = process.context.bug_analysis.severity
            self.processes_by_severity[severity] = (
                self.processes_by_severity.get(severity, 0) + 1
            )
        
        # Recalcula médias
        if process.total_duration_seconds:
            self.average_duration = (
                (self.average_duration * (self.total_processes - 1) + process.total_duration_seconds) 
                / self.total_processes
            )
        
        self.average_steps_per_process = (
            (self.average_steps_per_process * (self.total_processes - 1) + len(process.steps))
            / self.total_processes
        )