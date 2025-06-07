"""
Modelo para representar o resultado da revisão de uma issue.
Define a estrutura de dados para feedback e avaliação de qualidade.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ReviewStatus(Enum):
    """Status possíveis da revisão"""
    APPROVED = "approved"
    NEEDS_IMPROVEMENT = "needs_improvement"
    REJECTED = "rejected"


class ReviewCriteria(Enum):
    """Critérios de avaliação da issue"""
    TITLE_CLARITY = "title_clarity"
    DESCRIPTION_COMPLETENESS = "description_completeness"
    TECHNICAL_ACCURACY = "technical_accuracy"
    REPRODUCTION_STEPS = "reproduction_steps"
    PRIORITY_CLASSIFICATION = "priority_classification"
    FORMATTING = "formatting"


@dataclass
class ReviewFeedback:
    """Feedback específico sobre um critério de revisão"""
    criteria: ReviewCriteria
    score: int  # 1-5 (1 = ruim, 5 = excelente)
    comment: str
    suggestion: Optional[str] = None


@dataclass
class IssueReview:
    """Resultado completo da revisão de uma issue"""
    # Status geral da revisão
    status: ReviewStatus
    overall_score: int  # 1-5
    
    # Feedback detalhado por critério
    feedbacks: List[ReviewFeedback]
    
    # Comentários gerais
    general_comments: str
    
    # Sugestões de melhoria
    improvement_suggestions: List[str]
    
    # Metadados da revisão
    reviewer_agent: str = "IssueReviewerAgent"
    review_timestamp: Optional[str] = None
    
    def is_approved(self) -> bool:
        """Verifica se a issue foi aprovada"""
        return self.status == ReviewStatus.APPROVED
    
    def needs_improvement(self) -> bool:
        """Verifica se a issue precisa de melhorias"""
        return self.status == ReviewStatus.NEEDS_IMPROVEMENT
    
    def get_low_score_criteria(self, threshold: int = 3) -> List[ReviewCriteria]:
        """Retorna critérios com pontuação baixa"""
        return [
            feedback.criteria 
            for feedback in self.feedbacks 
            if feedback.score < threshold
        ]
    
    def get_formatted_feedback(self) -> str:
        """Retorna feedback formatado para o agente refinador"""
        if self.is_approved():
            return f"✅ Issue aprovada! Pontuação geral: {self.overall_score}/5"
        
        feedback_text = f"📋 Revisão da Issue (Pontuação: {self.overall_score}/5)\n\n"
        feedback_text += f"**Status:** {self.status.value}\n\n"
        
        if self.general_comments:
            feedback_text += f"**Comentários Gerais:**\n{self.general_comments}\n\n"
        
        if self.feedbacks:
            feedback_text += "**Feedback Detalhado:**\n"
            for feedback in self.feedbacks:
                emoji = "✅" if feedback.score >= 4 else "⚠️" if feedback.score >= 3 else "❌"
                feedback_text += f"{emoji} {feedback.criteria.value}: {feedback.score}/5 - {feedback.comment}\n"
                if feedback.suggestion:
                    feedback_text += f"   💡 Sugestão: {feedback.suggestion}\n"
            feedback_text += "\n"
        
        if self.improvement_suggestions:
            feedback_text += "**Sugestões de Melhoria:**\n"
            for i, suggestion in enumerate(self.improvement_suggestions, 1):
                feedback_text += f"{i}. {suggestion}\n"
        
        return feedback_text


@dataclass
class ReviewMetrics:
    """Métricas de qualidade da revisão"""
    total_reviews: int = 0
    approved_reviews: int = 0
    improvement_needed: int = 0
    rejected_reviews: int = 0
    average_score: float = 0.0
    
    def approval_rate(self) -> float:
        """Taxa de aprovação"""
        if self.total_reviews == 0:
            return 0.0
        return (self.approved_reviews / self.total_reviews) * 100
    
    def update_metrics(self, review: IssueReview):
        """Atualiza métricas com nova revisão"""
        self.total_reviews += 1
        
        if review.status == ReviewStatus.APPROVED:
            self.approved_reviews += 1
        elif review.status == ReviewStatus.NEEDS_IMPROVEMENT:
            self.improvement_needed += 1
        elif review.status == ReviewStatus.REJECTED:
            self.rejected_reviews += 1
        
        # Recalcula média
        self.average_score = (
            (self.average_score * (self.total_reviews - 1) + review.overall_score) 
            / self.total_reviews
        )