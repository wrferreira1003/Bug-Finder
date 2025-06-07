from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from .log_model import LogModel


class BugSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BugCategory(str, Enum):
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_ISSUE = "security_issue"
    OTHER = "other"


class BugImpact(str, Enum):
    USER_BLOCKING = "user_blocking"
    FEATURE_DEGRADATION = "feature_degradation"
    PERFORMANCE_IMPACT = "performance_impact"
    DATA_INTEGRITY = "data_integrity"
    SECURITY_RISK = "security_risk"
    SYSTEM_STABILITY = "system_stability"
    LOW_IMPACT = "low_impact"


class AnalysisDecision(str, Enum):
    CREATE_ISSUE = "create_issue"
    MONITOR = "monitor"
    IGNORE = "ignore"


class BugAnalysis(BaseModel):
    log_id: str = Field(..., description="ID único do log analisado")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da análise")
    
    # Classificação principal
    is_bug: bool = Field(..., description="Indica se realmente é um bug")
    severity: BugSeverity = Field(..., description="Severidade do bug")
    category: BugCategory = Field(..., description="Categoria do bug")
    impact: BugImpact = Field(..., description="Impacto do bug")
    
    # Análise detalhada
    error_pattern: Optional[str] = Field(None, description="Padrão de erro identificado")
    root_cause_hypothesis: Optional[str] = Field(None, description="Hipótese da causa raiz")
    affected_components: List[str] = Field(default_factory=list, description="Componentes afetados")
    reproduction_likelihood: float = Field(0.0, description="Probabilidade de reprodução (0-1)")
    
    # Contexto técnico
    technical_details: Dict[str, Any] = Field(default_factory=dict, description="Detalhes técnicos relevantes")
    environment_factors: List[str] = Field(default_factory=list, description="Fatores ambientais relevantes")
    
    # Recomendações
    decision: AnalysisDecision = Field(..., description="Decisão sobre o que fazer")
    recommended_actions: List[str] = Field(default_factory=list, description="Ações recomendadas")
    priority_score: float = Field(0.0, description="Pontuação de prioridade (0-100)")
    
    # Análise de contexto
    similar_issues_found: bool = Field(False, description="Se foram encontradas issues similares")
    frequency_analysis: Optional[str] = Field(None, description="Análise de frequência do erro")
    
    # Metadados da análise
    confidence_score: float = Field(0.0, description="Confiança na análise (0-1)")
    analysis_notes: Optional[str] = Field(None, description="Notas adicionais da análise")
    
    def should_create_issue(self) -> bool:
        return self.decision == AnalysisDecision.CREATE_ISSUE
    
    def is_high_priority(self) -> bool:
        return self.priority_score >= 70.0 or self.severity in [BugSeverity.HIGH, BugSeverity.CRITICAL]
    
    def requires_immediate_attention(self) -> bool:
        return (
            self.severity == BugSeverity.CRITICAL or
            self.impact in [BugImpact.USER_BLOCKING, BugImpact.SECURITY_RISK, BugImpact.DATA_INTEGRITY] or
            self.priority_score >= 90.0
        )
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        return {
            "is_bug": self.is_bug,
            "severity": self.severity,
            "category": self.category,
            "impact": self.impact,
            "decision": self.decision,
            "priority_score": self.priority_score,
            "confidence": self.confidence_score,
            "requires_immediate_attention": self.requires_immediate_attention()
        }


class AnalysisResult(BaseModel):
    log: LogModel = Field(..., description="Log original que foi analisado")
    analysis: BugAnalysis = Field(..., description="Resultado da análise")
    processing_time_ms: float = Field(..., description="Tempo de processamento em milissegundos")
    analyzer_version: str = Field("1.0.0", description="Versão do analisador usado")
    
    def is_actionable(self) -> bool:
        return self.analysis.should_create_issue()
    
    def get_full_context(self) -> Dict[str, Any]:
        return {
            "log_context": self.log.get_error_context(),
            "analysis_summary": self.analysis.get_analysis_summary(),
            "processing_info": {
                "processing_time_ms": self.processing_time_ms,
                "analyzer_version": self.analyzer_version
            }
        }