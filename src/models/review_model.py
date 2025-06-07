from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReviewCriteria(str, Enum):
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    TECHNICAL_ACCURACY = "technical_accuracy"
    REPRODUCIBILITY = "reproducibility"
    SEVERITY_ASSESSMENT = "severity_assessment"
    PRIORITY_ASSESSMENT = "priority_assessment"


class ReviewScore(BaseModel):
    criteria: ReviewCriteria = Field(..., description="Critério de avaliação")
    score: float = Field(..., description="Pontuação (0-10)")
    comment: Optional[str] = Field(None, description="Comentário sobre o critério")
    suggestions: List[str] = Field(default_factory=list, description="Sugestões específicas para este critério")
    
    def is_passing(self) -> bool:
        return self.score >= 7.0


class IssueReview(BaseModel):
    review_id: str = Field(..., description="ID único da revisão")
    issue_id: str = Field(..., description="ID da issue sendo revisada")
    reviewer_agent: str = Field(..., description="Nome do agente revisor")
    review_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da revisão")
    
    # Pontuações por critério
    scores: List[ReviewScore] = Field(default_factory=list, description="Pontuações por critério")
    overall_score: float = Field(0.0, description="Pontuação geral")
    
    # Decisão da revisão
    approved: bool = Field(False, description="Se a issue foi aprovada")
    requires_refinement: bool = Field(False, description="Se requer refinamento")
    
    # Feedback detalhado
    strengths: List[str] = Field(default_factory=list, description="Pontos fortes da issue")
    weaknesses: List[str] = Field(default_factory=list, description="Pontos fracos da issue")
    missing_information: List[str] = Field(default_factory=list, description="Informações faltantes")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Sugestões de melhoria")
    
    # Análise específica de conteúdo
    title_assessment: Optional[str] = Field(None, description="Avaliação do título")
    description_assessment: Optional[str] = Field(None, description="Avaliação da descrição")
    reproduction_steps_assessment: Optional[str] = Field(None, description="Avaliação dos passos de reprodução")
    technical_details_assessment: Optional[str] = Field(None, description="Avaliação dos detalhes técnicos")
    
    # Metadados da revisão
    review_duration_ms: Optional[float] = Field(None, description="Tempo gasto na revisão")
    reviewer_confidence: float = Field(0.0, description="Confiança do revisor (0-1)")
    
    def add_score(self, criteria: ReviewCriteria, score: float, comment: Optional[str] = None, suggestions: Optional[List[str]] = None) -> None:
        review_score = ReviewScore(
            criteria=criteria,
            score=score,
            comment=comment,
            suggestions=suggestions or []
        )
        self.scores.append(review_score)
        self._calculate_overall_score()
    
    def _calculate_overall_score(self) -> None:
        if self.scores:
            total_score = sum(score.score for score in self.scores)
            self.overall_score = total_score / len(self.scores)
            
            # Determinar se aprovado baseado na pontuação geral
            self.approved = self.overall_score >= 7.0 and all(score.is_passing() for score in self.scores)
            self.requires_refinement = not self.approved
    
    def get_failing_criteria(self) -> List[ReviewScore]:
        return [score for score in self.scores if not score.is_passing()]
    
    def get_detailed_feedback(self) -> Dict[str, Any]:
        return {
            "overall_assessment": {
                "approved": self.approved,
                "overall_score": self.overall_score,
                "requires_refinement": self.requires_refinement
            },
            "criteria_scores": [
                {
                    "criteria": score.criteria.value,
                    "score": score.score,
                    "passing": score.is_passing(),
                    "comment": score.comment,
                    "suggestions": score.suggestions
                } for score in self.scores
            ],
            "feedback": {
                "strengths": self.strengths,
                "weaknesses": self.weaknesses,
                "missing_information": self.missing_information,
                "improvement_suggestions": self.improvement_suggestions
            },
            "content_assessment": {
                "title": self.title_assessment,
                "description": self.description_assessment,
                "reproduction_steps": self.reproduction_steps_assessment,
                "technical_details": self.technical_details_assessment
            }
        }
    
    def generate_refinement_instructions(self) -> List[str]:
        instructions = []
        
        # Instruções baseadas nos critérios que falharam
        failing_criteria = self.get_failing_criteria()
        for score in failing_criteria:
            if score.criteria == ReviewCriteria.COMPLETENESS:
                instructions.append("Adicionar informações faltantes identificadas na revisão")
            elif score.criteria == ReviewCriteria.CLARITY:
                instructions.append("Melhorar a clareza da descrição e dos passos de reprodução")
            elif score.criteria == ReviewCriteria.TECHNICAL_ACCURACY:
                instructions.append("Revisar e corrigir detalhes técnicos imprecisos")
            elif score.criteria == ReviewCriteria.REPRODUCIBILITY:
                instructions.append("Detalhar melhor os passos para reprodução do problema")
            elif score.criteria == ReviewCriteria.SEVERITY_ASSESSMENT:
                instructions.append("Reavaliar a severidade do problema")
            elif score.criteria == ReviewCriteria.PRIORITY_ASSESSMENT:
                instructions.append("Ajustar a prioridade da issue")
            
            # Adicionar sugestões específicas do critério
            instructions.extend(score.suggestions)
        
        # Adicionar informações faltantes
        for missing in self.missing_information:
            instructions.append(f"Adicionar: {missing}")
        
        # Adicionar sugestões de melhoria
        instructions.extend(self.improvement_suggestions)
        
        return list(set(instructions))  # Remover duplicatas


class RefinementRequest(BaseModel):
    request_id: str = Field(..., description="ID único da solicitação de refinamento")
    issue_id: str = Field(..., description="ID da issue a ser refinada")
    review_id: str = Field(..., description="ID da revisão que gerou esta solicitação")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp de criação")
    
    # Instruções de refinamento
    refinement_instructions: List[str] = Field(..., description="Lista de instruções de refinamento")
    priority_changes: List[str] = Field(default_factory=list, description="Mudanças de prioridade solicitadas")
    content_changes: List[str] = Field(default_factory=list, description="Mudanças de conteúdo solicitadas")
    
    # Contexto adicional
    reviewer_notes: Optional[str] = Field(None, description="Notas adicionais do revisor")
    expected_improvements: List[str] = Field(default_factory=list, description="Melhorias esperadas")
    
    def get_refinement_summary(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "issue_id": self.issue_id,
            "total_instructions": len(self.refinement_instructions),
            "priority_changes_count": len(self.priority_changes),
            "content_changes_count": len(self.content_changes),
            "created_at": self.created_at
        }