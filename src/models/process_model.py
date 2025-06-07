from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from .log_model import LogModel, ProcessedLog
from .bug_analysis import AnalysisResult
from .issue_model import IssueModel
from .notification_model import NotificationModel


class ProcessStatus(str, Enum):
    STARTED = "started"
    LOG_RECEIVED = "log_received"
    LOG_PROCESSED = "log_processed"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_REJECTED = "analysis_rejected"
    ISSUE_DRAFTED = "issue_drafted"
    ISSUE_UNDER_REVIEW = "issue_under_review"
    ISSUE_NEEDS_REFINEMENT = "issue_needs_refinement"
    ISSUE_APPROVED = "issue_approved"
    ISSUE_CREATED = "issue_created"
    NOTIFICATION_SENT = "notification_sent"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessStep(BaseModel):
    step_name: str = Field(..., description="Nome da etapa")
    agent_name: str = Field(..., description="Nome do agente responsável")
    status: ProcessStatus = Field(..., description="Status da etapa")
    started_at: datetime = Field(..., description="Timestamp de início")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de conclusão")
    duration_ms: Optional[float] = Field(None, description="Duração em milissegundos")
    success: bool = Field(True, description="Se a etapa foi bem-sucedida")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Dados de saída da etapa")
    
    def complete_step(self, success: bool = True, error_message: Optional[str] = None, output_data: Optional[Dict[str, Any]] = None) -> None:
        self.completed_at = datetime.now()
        self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        self.success = success
        if error_message:
            self.error_message = error_message
        if output_data:
            self.output_data = output_data


class BugFinderProcess(BaseModel):
    process_id: str = Field(..., description="ID único do processo")
    started_at: datetime = Field(default_factory=datetime.now, description="Timestamp de início do processo")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de conclusão do processo")
    status: ProcessStatus = Field(ProcessStatus.STARTED, description="Status atual do processo")
    
    # Dados do processo
    raw_log_input: str = Field(..., description="Log original recebido")
    processed_log: Optional[ProcessedLog] = Field(None, description="Log processado")
    analysis_result: Optional[AnalysisResult] = Field(None, description="Resultado da análise")
    issue: Optional[IssueModel] = Field(None, description="Issue criada")
    notifications: List[NotificationModel] = Field(default_factory=list, description="Notificações enviadas")
    
    # Rastreamento de etapas
    steps: List[ProcessStep] = Field(default_factory=list, description="Etapas do processo")
    current_step: Optional[str] = Field(None, description="Etapa atual")
    
    # Metadados
    system_version: str = Field("1.0.0", description="Versão do sistema Bug Finder")
    environment: str = Field("production", description="Ambiente de execução")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Configuração usada")
    
    # Métricas
    total_duration_ms: Optional[float] = Field(None, description="Duração total em milissegundos")
    success_rate: float = Field(0.0, description="Taxa de sucesso das etapas")
    
    def start_step(self, step_name: str, agent_name: str, status: ProcessStatus) -> ProcessStep:
        step = ProcessStep(
            step_name=step_name,
            agent_name=agent_name,
            status=status,
            started_at=datetime.now()
        )
        self.steps.append(step)
        self.current_step = step_name
        self.status = status
        return step
    
    def complete_current_step(self, success: bool = True, error_message: Optional[str] = None, output_data: Optional[Dict[str, Any]] = None) -> None:
        if self.steps:
            current_step = self.steps[-1]
            current_step.complete_step(success, error_message, output_data)
            
            if not success:
                self.status = ProcessStatus.FAILED
    
    def complete_process(self, success: bool = True) -> None:
        self.completed_at = datetime.now()
        self.total_duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        
        # Calcular taxa de sucesso
        if self.steps:
            successful_steps = sum(1 for step in self.steps if step.success)
            self.success_rate = successful_steps / len(self.steps)
        
        self.status = ProcessStatus.COMPLETED if success else ProcessStatus.FAILED
        self.current_step = None
    
    def add_processed_log(self, processed_log: ProcessedLog) -> None:
        self.processed_log = processed_log
        self.complete_current_step(success=not processed_log.has_errors())
    
    def add_analysis_result(self, analysis_result: AnalysisResult) -> None:
        self.analysis_result = analysis_result
        
        if analysis_result.analysis.should_create_issue():
            self.status = ProcessStatus.ANALYSIS_COMPLETED
            self.complete_current_step(success=True)
        else:
            self.status = ProcessStatus.ANALYSIS_REJECTED
            self.complete_current_step(success=True, output_data={"reason": "Analysis determined no issue creation needed"})
    
    def add_issue(self, issue: IssueModel) -> None:
        self.issue = issue
        self.complete_current_step(success=True)
    
    def add_notification(self, notification: NotificationModel) -> None:
        self.notifications.append(notification)
    
    def should_continue(self) -> bool:
        return self.status not in [ProcessStatus.FAILED, ProcessStatus.COMPLETED, ProcessStatus.ANALYSIS_REJECTED]
    
    def has_failed(self) -> bool:
        return self.status == ProcessStatus.FAILED
    
    def was_successful(self) -> bool:
        return self.status == ProcessStatus.COMPLETED and self.success_rate >= 0.8
    
    def get_process_summary(self) -> Dict[str, Any]:
        return {
            "process_id": self.process_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.total_duration_ms,
            "success_rate": self.success_rate,
            "steps_count": len(self.steps),
            "notifications_sent": len([n for n in self.notifications if n.status == "sent"]),
            "issue_created": self.issue is not None and self.issue.github_issue_number is not None,
            "system_version": self.system_version
        }
    
    def get_detailed_log(self) -> List[Dict[str, Any]]:
        log_entries = []
        
        # Log de início
        log_entries.append({
            "timestamp": self.started_at,
            "event": "process_started",
            "process_id": self.process_id,
            "raw_log_size": len(self.raw_log_input)
        })
        
        # Log de cada etapa
        for step in self.steps:
            log_entries.append({
                "timestamp": step.started_at,
                "event": "step_started",
                "step_name": step.step_name,
                "agent_name": step.agent_name,
                "status": step.status
            })
            
            if step.completed_at:
                log_entries.append({
                    "timestamp": step.completed_at,
                    "event": "step_completed",
                    "step_name": step.step_name,
                    "success": step.success,
                    "duration_ms": step.duration_ms,
                    "error_message": step.error_message
                })
        
        # Log de conclusão
        if self.completed_at:
            log_entries.append({
                "timestamp": self.completed_at,
                "event": "process_completed",
                "status": self.status,
                "total_duration_ms": self.total_duration_ms,
                "success_rate": self.success_rate
            })
        
        return sorted(log_entries, key=lambda x: x["timestamp"])