from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from .bug_analysis import BugAnalysis, BugSeverity


class SolutionType(str, Enum):
    QUICK_FIX = "quick_fix"
    ROBUST_SOLUTION = "robust_solution"
    WORKAROUND = "workaround"


class EffortEstimate(str, Enum):
    LOW = "baixo"
    MEDIUM = "médio"
    HIGH = "alto"


class DetailedSolution(BaseModel):
    type: SolutionType = Field(..., description="Tipo da solução")
    title: str = Field(..., description="Título da solução")
    description: str = Field(..., description="Descrição detalhada da solução")
    implementation_steps: List[str] = Field(default_factory=list, description="Passos de implementação")
    files_to_modify: List[str] = Field(default_factory=list, description="Arquivos que precisam ser modificados")
    risks: List[str] = Field(default_factory=list, description="Riscos identificados")
    effort_estimate: EffortEstimate = Field(EffortEstimate.MEDIUM, description="Estimativa de esforço")
    testing_requirements: List[str] = Field(default_factory=list, description="Requisitos de teste")


class ImplementationPlan(BaseModel):
    prerequisites: List[str] = Field(default_factory=list, description="Pré-requisitos")
    main_steps: List[str] = Field(default_factory=list, description="Passos principais")
    commands_to_run: List[str] = Field(default_factory=list, description="Comandos a serem executados")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Critérios de aceitação")
    rollback_plan: Optional[str] = Field(None, description="Plano de rollback")


class IssueStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    NEEDS_REFINEMENT = "needs_refinement"
    APPROVED = "approved"
    CREATED = "created"
    NOTIFIED = "notified"
    FAILED = "failed"


class IssuePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class IssueLabel(str, Enum):
    BUG = "bug"
    CRITICAL = "critical"
    HIGH_PRIORITY = "high-priority"
    NEEDS_INVESTIGATION = "needs-investigation"
    RUNTIME_ERROR = "runtime-error"
    NETWORK_ISSUE = "network-issue"
    DATABASE_ISSUE = "database-issue"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AUTO_GENERATED = "auto-generated"


class IssueDraft(BaseModel):
    title: str = Field(..., description="Título da issue")
    description: str = Field(..., description="Descrição detalhada da issue")
    reproduction_steps: List[str] = Field(default_factory=list, description="Passos para reproduzir o problema")
    expected_behavior: Optional[str] = Field(None, description="Comportamento esperado")
    actual_behavior: Optional[str] = Field(None, description="Comportamento atual")
    
    # Contexto técnico
    environment_info: Dict[str, Any] = Field(default_factory=dict, description="Informações do ambiente")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detalhes do erro")
    stack_trace: Optional[str] = Field(None, description="Stack trace do erro")
    
    # Metadados
    priority: IssuePriority = Field(IssuePriority.MEDIUM, description="Prioridade da issue")
    labels: List[IssueLabel] = Field(default_factory=list, description="Labels da issue")
    assignees: List[str] = Field(default_factory=list, description="Pessoas assignadas")
    
    # Informações adicionais
    related_logs: List[str] = Field(default_factory=list, description="IDs dos logs relacionados")
    additional_context: Optional[str] = Field(None, description="Contexto adicional")
    
    # Análise detalhada da solução
    root_cause_analysis: Optional[str] = Field(None, description="Análise detalhada da causa raiz")
    suggested_solutions: List[DetailedSolution] = Field(default_factory=list, description="Soluções detalhadas propostas")
    implementation_plan: Optional[ImplementationPlan] = Field(None, description="Plano de implementação detalhado")
    
    # Campos legados para compatibilidade
    suggested_fixes: List[str] = Field(default_factory=list, description="Possíveis soluções sugeridas (legado)")
    resolution_steps: List[str] = Field(default_factory=list, description="Passos detalhados para resolver o problema (legado)")
    
    def add_label(self, label: IssueLabel) -> None:
        if label not in self.labels:
            self.labels.append(label)
    
    def set_priority_from_severity(self, severity: BugSeverity) -> None:
        mapping = {
            BugSeverity.LOW: IssuePriority.LOW,
            BugSeverity.MEDIUM: IssuePriority.MEDIUM,
            BugSeverity.HIGH: IssuePriority.HIGH,
            BugSeverity.CRITICAL: IssuePriority.URGENT
        }
        self.priority = mapping.get(severity, IssuePriority.MEDIUM)
    
    def get_markdown_content(self) -> str:
        content = []
        
        # Descrição principal
        content.append("## Descrição")
        content.append(self.description)
        content.append("")
        
        # Comportamento
        if self.expected_behavior or self.actual_behavior:
            content.append("## Comportamento")
            if self.expected_behavior:
                content.append("**Esperado:**")
                content.append(self.expected_behavior)
                content.append("")
            if self.actual_behavior:
                content.append("**Atual:**")
                content.append(self.actual_behavior)
                content.append("")
        
        # Passos para reproduzir
        if self.reproduction_steps:
            content.append("## Passos para Reproduzir")
            for i, step in enumerate(self.reproduction_steps, 1):
                content.append(f"{i}. {step}")
            content.append("")
        
        # Detalhes técnicos
        if self.error_details or self.environment_info:
            content.append("## Detalhes Técnicos")
            
            if self.error_details:
                content.append("**Erro:**")
                for key, value in self.error_details.items():
                    content.append(f"- {key}: `{value}`")
                content.append("")
            
            if self.environment_info:
                content.append("**Ambiente:**")
                for key, value in self.environment_info.items():
                    content.append(f"- {key}: `{value}`")
                content.append("")
        
        # Stack trace
        if self.stack_trace:
            content.append("## Stack Trace")
            content.append("```")
            content.append(self.stack_trace)
            content.append("```")
            content.append("")
        
        # Contexto adicional
        if self.additional_context:
            content.append("## Contexto Adicional")
            content.append(self.additional_context)
            content.append("")
        
        # Análise da causa raiz
        if self.root_cause_analysis:
            content.append("## Análise da Causa Raiz")
            content.append(self.root_cause_analysis)
            content.append("")
        
        # Soluções detalhadas propostas
        if self.suggested_solutions:
            content.append("## Soluções Propostas")
            for i, solution in enumerate(self.suggested_solutions, 1):
                content.append(f"### {i}. {solution.title} ({solution.type.value.replace('_', ' ').title()})")
                content.append(f"**Descrição:** {solution.description}")
                content.append(f"**Esforço Estimado:** {solution.effort_estimate.value}")
                content.append("")
                
                if solution.implementation_steps:
                    content.append("**Passos de Implementação:**")
                    for j, step in enumerate(solution.implementation_steps, 1):
                        content.append(f"{j}. {step}")
                    content.append("")
                
                if solution.files_to_modify:
                    content.append("**Arquivos a Modificar:**")
                    for file in solution.files_to_modify:
                        content.append(f"- `{file}`")
                    content.append("")
                
                if solution.risks:
                    content.append("**Riscos:**")
                    for risk in solution.risks:
                        content.append(f"- ⚠️ {risk}")
                    content.append("")
                
                if solution.testing_requirements:
                    content.append("**Requisitos de Teste:**")
                    for test in solution.testing_requirements:
                        content.append(f"- 🧪 {test}")
                    content.append("")
                
                content.append("---")
                content.append("")
        
        # Plano de implementação
        if self.implementation_plan:
            content.append("## Plano de Implementação")
            
            if self.implementation_plan.prerequisites:
                content.append("### Pré-requisitos")
                for prereq in self.implementation_plan.prerequisites:
                    content.append(f"- {prereq}")
                content.append("")
            
            if self.implementation_plan.main_steps:
                content.append("### Passos Principais")
                for i, step in enumerate(self.implementation_plan.main_steps, 1):
                    content.append(f"{i}. {step}")
                content.append("")
            
            if self.implementation_plan.commands_to_run:
                content.append("### Comandos a Executar")
                content.append("```bash")
                for cmd in self.implementation_plan.commands_to_run:
                    content.append(cmd)
                content.append("```")
                content.append("")
            
            if self.implementation_plan.acceptance_criteria:
                content.append("### Critérios de Aceitação")
                for criterion in self.implementation_plan.acceptance_criteria:
                    content.append(f"- ✅ {criterion}")
                content.append("")
            
            if self.implementation_plan.rollback_plan:
                content.append("### Plano de Rollback")
                content.append(f"🔄 {self.implementation_plan.rollback_plan}")
                content.append("")

        # Campos legados para compatibilidade
        if self.suggested_fixes:
            content.append("## Soluções Resumidas")
            for i, fix in enumerate(self.suggested_fixes, 1):
                content.append(f"{i}. {fix}")
            content.append("")

        if self.resolution_steps:
            content.append("## Passos de Resolução")
            for i, step in enumerate(self.resolution_steps, 1):
                content.append(f"{i}. {step}")
            content.append("")
        
        # Metadados
        content.append("---")
        content.append(f"**Prioridade:** {self.priority.value}")
        content.append(f"**Labels:** {', '.join([label.value for label in self.labels])}")
        if self.related_logs:
            content.append(f"**Logs relacionados:** {', '.join(self.related_logs)}")
        
        return "\n".join(content)


class ReviewFeedback(BaseModel):
    reviewer_id: str = Field(..., description="ID do revisor")
    review_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da revisão")
    approved: bool = Field(..., description="Se a issue foi aprovada")
    
    # Feedback detalhado
    overall_score: float = Field(..., description="Pontuação geral (0-10)")
    completeness_score: float = Field(..., description="Pontuação de completude (0-10)")
    clarity_score: float = Field(..., description="Pontuação de clareza (0-10)")
    technical_accuracy_score: float = Field(..., description="Pontuação de precisão técnica (0-10)")
    
    # Comentários específicos
    missing_information: List[str] = Field(default_factory=list, description="Informações que estão faltando")
    unclear_sections: List[str] = Field(default_factory=list, description="Seções que precisam de clarificação")
    technical_issues: List[str] = Field(default_factory=list, description="Problemas técnicos identificados")
    suggestions: List[str] = Field(default_factory=list, description="Sugestões de melhoria")
    
    # Comentário geral
    general_comment: Optional[str] = Field(None, description="Comentário geral do revisor")
    
    def needs_improvement(self) -> bool:
        return not self.approved or self.overall_score < 7.0
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "overall_score": self.overall_score,
            "needs_improvement": self.needs_improvement(),
            "issues_count": len(self.missing_information) + len(self.unclear_sections) + len(self.technical_issues),
            "suggestions_count": len(self.suggestions)
        }


class IssueModel(BaseModel):
    id: str = Field(..., description="ID único da issue")
    draft: IssueDraft = Field(..., description="Conteúdo da issue")
    bug_analysis: BugAnalysis = Field(..., description="Análise do bug que originou a issue")
    
    # Status e timestamps
    status: IssueStatus = Field(IssueStatus.DRAFT, description="Status atual da issue")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp de criação")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp da última atualização")
    
    # Processo de revisão
    review_feedback: Optional[ReviewFeedback] = Field(None, description="Feedback da revisão")
    review_iterations: int = Field(0, description="Número de iterações de revisão")
    
    # Integração externa
    github_issue_number: Optional[int] = Field(None, description="Número da issue no GitHub")
    github_issue_url: Optional[str] = Field(None, description="URL da issue no GitHub")
    discord_message_id: Optional[str] = Field(None, description="ID da mensagem no Discord")
    
    # Metadados
    agent_versions: Dict[str, str] = Field(default_factory=dict, description="Versões dos agentes que processaram")
    processing_log: List[str] = Field(default_factory=list, description="Log do processamento")
    
    def update_status(self, new_status: IssueStatus) -> None:
        self.status = new_status
        self.updated_at = datetime.now()
        self.processing_log.append(f"Status changed to {new_status.value} at {self.updated_at}")
    
    def add_review_feedback(self, feedback: ReviewFeedback) -> None:
        self.review_feedback = feedback
        self.review_iterations += 1
        self.update_status(IssueStatus.NEEDS_REFINEMENT if not feedback.approved else IssueStatus.APPROVED)
    
    def mark_as_created(self, github_url: str, issue_number: int) -> None:
        self.github_issue_url = github_url
        self.github_issue_number = issue_number
        self.update_status(IssueStatus.CREATED)
    
    def mark_as_notified(self, discord_message_id: str) -> None:
        self.discord_message_id = discord_message_id
        self.update_status(IssueStatus.NOTIFIED)
    
    def is_ready_for_creation(self) -> bool:
        return self.status == IssueStatus.APPROVED
    
    def needs_review(self) -> bool:
        return self.status in [IssueStatus.DRAFT, IssueStatus.NEEDS_REFINEMENT]
    
    def get_issue_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.draft.title,
            "status": self.status,
            "priority": self.draft.priority,
            "severity": self.bug_analysis.severity,
            "github_url": self.github_issue_url,
            "review_iterations": self.review_iterations,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }