"""
IssueReviewerAgent - Agente Revisor de Issues

Localização: src/agents/issue_reviewer_agent.py

Responsabilidades:
- Revisar a qualidade dos rascunhos de issues
- Verificar completude das informações
- Validar clareza e estrutura
- Identificar pontos de melhoria
- Decidir se aprova ou solicita refinamento

Este agente atua como um "crítico especializado", garantindo que
apenas issues de alta qualidade sejam publicadas no GitHub.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime
from enum import Enum

from ..models.issue_model import IssueModel, IssuePriority
from ..models.review_model import IssueReview, ReviewStatus, ReviewCriteria, ReviewFeedback
from ..config.prompts import IssueReviewPrompts
from ..config.settings import get_settings


class LLMProvider(Protocol):
    """
    Interface para provedor de modelo de linguagem.
    
    Permite independência de modelo específico (Gemini, OpenAI, etc.).
    """
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Gera resposta baseada no prompt fornecido.
        
        Args:
            prompt: Prompt para o modelo
            context: Contexto adicional opcional
            
        Returns:
            Resposta gerada pelo modelo
        """
        ...


class IssueReviewerAgent:
    """
    Agente responsável por revisar a qualidade de rascunhos de issues.
    
    Este agente analisa rascunhos e fornece feedback detalhado,
    garantindo que atendam aos padrões de qualidade antes da publicação.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Inicializa o agente revisor de issues.
        
        Args:
            llm_provider: Provedor do modelo de linguagem a ser usado
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.prompts = IssueReviewPrompts()
        
        # Configurações de qualidade
        self.quality_thresholds = {
            'min_title_length': 15,
            'max_title_length': 100,
            'min_description_length': 100,
            'min_sections_required': 3,
            'required_labels': ['bug'],
            'max_review_iterations': 3
        }
    
    def review_issue_draft(self, issue_draft: IssueModel) -> IssueReview:
        """
        Revisa um rascunho de issue e fornece feedback detalhado.
        
        Args:
            issue_draft: Rascunho de issue para revisar
            
        Returns:
            Revisão completa com feedback e decisão
        """
        try:
            self.logger.info(f"Iniciando revisão da issue: {issue_draft.title[:50]}...")
            
            # Preparação do contexto para revisão
            review_context = self._prepare_review_context(issue_draft)
            
            # Análise estrutural básica
            structural_review = self._perform_structural_review(issue_draft)
            
            # Análise de qualidade usando IA
            quality_review = self._perform_ai_quality_review(issue_draft, review_context)
            
            # Consolidação da revisão
            consolidated_review = self._consolidate_review_results(
                issue_draft, structural_review, quality_review
            )
            
            # Criação do objeto de revisão final
            issue_review = self._create_issue_review(issue_draft, consolidated_review)
            
            self.logger.info(f"Revisão concluída. Resultado: {issue_review.result}")
            
            return issue_review
            
        except Exception as e:
            self.logger.error(f"Erro durante revisão da issue: {str(e)}")
            # Retorna revisão de fallback em caso de erro
            return self._create_fallback_review(issue_draft)
    
    def _prepare_review_context(self, issue_draft: IssueModel) -> Dict[str, Any]:
        """
        Prepara contexto para revisão da issue.
        """
        context = {
            # Informações básicas
            'title_length': len(issue_draft.title),
            'description_length': len(issue_draft.description),
            'labels_count': len(issue_draft.labels),
            'has_reproduction_steps': bool(issue_draft.reproduction_steps),
            'has_environment_info': bool(issue_draft.environment_info),
            'has_assignees': bool(issue_draft.assignees),
            'has_milestone': bool(issue_draft.milestone),
            
            # Análise de conteúdo
            'title_words': len(issue_draft.title.split()),
            'description_sections': self._count_markdown_sections(issue_draft.description),
            'description_code_blocks': self._count_code_blocks(issue_draft.description),
            
            # Configurações de qualidade
            'quality_thresholds': self.quality_thresholds,
            
            # Padrões do projeto
            'project_standards': self.settings.get('issue_standards', {}),
        }
        
        return context
    
    def _count_markdown_sections(self, text: str) -> int:
        """Conta seções markdown (##, ###, etc.) no texto."""
        import re
        return len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))
    
    def _count_code_blocks(self, text: str) -> int:
        """Conta blocos de código (```) no texto."""
        return text.count('```') // 2
    
    def _perform_structural_review(self, issue_draft: IssueModel) -> Dict[str, Any]:
        """
        Realiza revisão estrutural básica da issue.
        """
        issues = []
        score = 100
        
        # Verifica título
        if len(issue_draft.title) < self.quality_thresholds['min_title_length']:
            issues.append({
                'category': 'title',
                'severity': 'high',
                'message': f"Título muito curto ({len(issue_draft.title)} chars). Mínimo: {self.quality_thresholds['min_title_length']}",
                'suggestion': 'Expanda o título para ser mais descritivo'
            })
            score -= 20
        
        if len(issue_draft.title) > self.quality_thresholds['max_title_length']:
            issues.append({
                'category': 'title',
                'severity': 'medium',
                'message': f"Título muito longo ({len(issue_draft.title)} chars). Máximo: {self.quality_thresholds['max_title_length']}",
                'suggestion': 'Reduza o título mantendo as informações essenciais'
            })
            score -= 10
        
        # Verifica descrição
        if len(issue_draft.description) < self.quality_thresholds['min_description_length']:
            issues.append({
                'category': 'description',
                'severity': 'high',
                'message': f"Descrição muito curta ({len(issue_draft.description)} chars). Mínimo: {self.quality_thresholds['min_description_length']}",
                'suggestion': 'Adicione mais detalhes técnicos e contexto'
            })
            score -= 25
        
        # Verifica seções da descrição
        sections_count = self._count_markdown_sections(issue_draft.description)
        if sections_count < self.quality_thresholds['min_sections_required']:
            issues.append({
                'category': 'structure',
                'severity': 'medium',
                'message': f"Poucas seções na descrição ({sections_count}). Mínimo: {self.quality_thresholds['min_sections_required']}",
                'suggestion': 'Organize a descrição em seções claras (ex: Summary, Details, Steps to Reproduce)'
            })
            score -= 15
        
        # Verifica labels
        has_required_labels = any(
            label in [str(l).lower() for l in issue_draft.labels] 
            for label in self.quality_thresholds['required_labels']
        )
        if not has_required_labels:
            issues.append({
                'category': 'labels',
                'severity': 'medium',
                'message': f"Labels obrigatórias ausentes: {self.quality_thresholds['required_labels']}",
                'suggestion': 'Adicione as labels apropriadas para categorizar a issue'
            })
            score -= 10
        
        # Verifica passos de reprodução
        if not issue_draft.reproduction_steps:
            issues.append({
                'category': 'reproduction',
                'severity': 'low',
                'message': "Passos de reprodução ausentes",
                'suggestion': 'Adicione passos claros para reproduzir o problema'
            })
            score -= 5
        
        # Verifica informações de ambiente
        if not issue_draft.environment_info:
            issues.append({
                'category': 'environment',
                'severity': 'low',
                'message': "Informações de ambiente ausentes",
                'suggestion': 'Adicione informações sobre o ambiente onde o erro ocorreu'
            })
            score -= 5
        
        return {
            'score': max(0, score),
            'issues': issues,
            'total_issues': len(issues),
            'high_severity_count': len([i for i in issues if i['severity'] == 'high']),
            'medium_severity_count': len([i for i in issues if i['severity'] == 'medium']),
            'low_severity_count': len([i for i in issues if i['severity'] == 'low'])
        }
    
    def _perform_ai_quality_review(self, issue_draft: IssueModel, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza análise de qualidade usando IA.
        """
        # Constrói o prompt para revisão
        review_prompt = self.prompts.get_issue_review_prompt(issue_draft, context)
        
        # Gera resposta do modelo
        ai_response = self.llm_provider.generate_response(review_prompt, context)
        
        # Faz parsing da resposta JSON
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            self.logger.warning("Resposta da IA não é JSON válido, tentando parsing alternativo")
            return self._parse_alternative_review_response(ai_response, context)
    
    def _parse_alternative_review_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz parsing alternativo da resposta da IA.
        """
        # Implementação básica de fallback
        response_lower = response.lower()
        
        # Determina se aprova ou não
        is_approved = any(word in response_lower for word in [
            'approved', 'good', 'acceptable', 'ready', 'publish'
        ])
        
        # Extrai feedback básico
        feedback_items = []
        if 'title' in response_lower:
            feedback_items.append({
                'category': 'title',
                'severity': 'medium',
                'message': 'Revisar título conforme sugestão da IA',
                'suggestion': 'Melhorar clareza e especificidade do título'
            })
        
        if 'description' in response_lower:
            feedback_items.append({
                'category': 'description',
                'severity': 'medium', 
                'message': 'Revisar descrição conforme sugestão da IA',
                'suggestion': 'Adicionar mais detalhes técnicos e contexto'
            })
        
        return {
            'overall_quality': 'medium' if is_approved else 'low',
            'is_approved': is_approved,
            'confidence': 0.6,
            'feedback': feedback_items,
            'strengths': ['Automated generation', 'Basic structure'],
            'improvements': ['Needs manual review', 'AI parsing failed'],
            'ai_reasoning': response
        }
    
    def _consolidate_review_results(self, issue_draft: IssueModel, structural: Dict[str, Any], quality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolida resultados da revisão estrutural e de qualidade.
        """
        # Combina feedbacks
        all_feedback = structural['issues'] + quality.get('feedback', [])
        
        # Calcula score final
        structural_score = structural['score']
        quality_score = self._convert_quality_to_score(quality.get('overall_quality', 'medium'))
        final_score = (structural_score * 0.6) + (quality_score * 0.4)
        
        # Determina se aprova
        is_approved = (
            final_score >= 70 and
            structural['high_severity_count'] == 0 and
            quality.get('is_approved', False)
        )
        
        # Determina resultado final
        if is_approved:
            result = ReviewStatus.APPROVED
        elif final_score >= 50:
            result = ReviewStatus.NEEDS_IMPROVEMENT
        else:
            result = ReviewStatus.REJECTED
        
        return {
            'result': result,
            'final_score': final_score,
            'structural_score': structural_score,
            'quality_score': quality_score,
            'is_approved': is_approved,
            'feedback': all_feedback,
            'strengths': quality.get('strengths', []),
            'improvements': quality.get('improvements', []),
            'confidence': quality.get('confidence', 0.7),
            'ai_reasoning': quality.get('ai_reasoning', ''),
            'total_issues': len(all_feedback),
            'high_severity_count': len([f for f in all_feedback if f['severity'] == 'high']),
            'medium_severity_count': len([f for f in all_feedback if f['severity'] == 'medium']),
            'low_severity_count': len([f for f in all_feedback if f['severity'] == 'low'])
        }
    
    def _convert_quality_to_score(self, quality: str) -> float:
        """Converte qualidade textual para score numérico."""
        quality_scores = {
            'high': 90,
            'good': 80,
            'medium': 60,
            'low': 40,
            'poor': 20
        }
        return quality_scores.get(quality.lower(), 60)
    
    def _create_issue_review(self, issue_draft: IssueModel, review_data: Dict[str, Any]) -> IssueReview:
        """
        Cria objeto IssueReview a partir dos dados consolidados.
        """
        # Converte feedback para objetos ReviewFeedback
        feedback_objects = []
        for feedback in review_data['feedback']:
            try:
                category = ReviewCriteria[feedback['category'].upper()]
            except KeyError:
                category = ReviewCriteria.FORMATTING
            
            feedback_obj = ReviewFeedback(
                category=category,
                severity=feedback['severity'],
                message=feedback['message'],
                suggestion=feedback['suggestion']
            )
            feedback_objects.append(feedback_obj)
        
        return IssueReview(
            status=review_data['result'],
            overall_score=int(review_data['final_score']),
            feedbacks=feedback_objects,
            general_comments=review_data['ai_reasoning'],
            improvement_suggestions=review_data['improvements'],
            reviewer_agent='IssueReviewerAgent',
            review_timestamp=datetime.now().isoformat()
        )
    
    def _create_fallback_review(self, issue_draft: IssueModel) -> IssueReview:
        """
        Cria revisão de fallback em caso de erro.
        """
        fallback_feedback = [
            ReviewFeedback(
                criteria=ReviewCriteria.FORMATTING,
                score=1,
                comment='Revisão automática falhou',
                suggestion='Revisar manualmente antes de publicar'
            )
        ]
        
        return IssueReview(
            status=ReviewStatus.REJECTED,
            overall_score=1,  # Score baixo para forçar revisão manual
            feedbacks=fallback_feedback,
            general_comments='Erro durante processo de revisão automática',
            improvement_suggestions=['Revisão manual necessária'],
            reviewer_agent='IssueReviewerAgent (Fallback)',
            review_timestamp=datetime.now().isoformat()
        )
    
    def should_approve_issue(self, review: IssueReview) -> bool:
        """
        Determina se a issue deve ser aprovada baseada na revisão.
        
        Args:
            review: Resultado da revisão
            
        Returns:
            True se deve ser aprovada, False caso contrário
        """
        return review.status == ReviewStatus.APPROVED
    
    def get_improvement_priorities(self, review: IssueReview) -> List[Dict[str, Any]]:
        """
        Retorna lista priorizada de melhorias necessárias.
        
        Args:
            review: Resultado da revisão
            
        Returns:
            Lista de melhorias ordenadas por prioridade
        """
        improvements = []
        
        # Agrupa feedback por score
        high_priority = [f for f in review.feedbacks if f.score <= 2]
        medium_priority = [f for f in review.feedbacks if f.score == 3]
        low_priority = [f for f in review.feedbacks if f.score == 4]
        
        # Adiciona melhorias por prioridade
        for feedback in high_priority + medium_priority + low_priority:
            improvements.append({
                'category': feedback.criteria.value,
                'score': feedback.score,
                'message': feedback.comment,
                'suggestion': feedback.suggestion,
                'priority': 'high' if feedback.score <= 2 else 'medium' if feedback.score == 3 else 'low'
            })
        
        return improvements
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente.
        """
        return {
            'name': 'IssueReviewerAgent',
            'version': '1.0.0',
            'description': 'Agente responsável por revisar qualidade de rascunhos de issues',
            'capabilities': [
                'Revisão estrutural de issues',
                'Análise de qualidade usando IA',
                'Feedback detalhado e categorizado',
                'Pontuação de qualidade',
                'Priorização de melhorias',
                'Decisão de aprovação/rejeição'
            ],
            'input_format': 'IssueModel',
            'output_format': 'IssueReview',
            'requires_llm': True,
            'quality_thresholds': self.quality_thresholds
        }


# Exemplo de implementação de provedor LLM para testes
class MockLLMProvider:
    """Provedor mock para testes sem dependência externa."""
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Simula análise baseada no contexto
        title_length = context.get('title_length', 50)
        description_length = context.get('description_length', 200)
        
        if title_length < 15 or description_length < 100:
            return json.dumps({
                'overall_quality': 'low',
                'is_approved': False,
                'confidence': 0.8,
                'feedback': [
                    {
                        'category': 'title' if title_length < 15 else 'description',
                        'severity': 'high',
                        'message': 'Conteúdo insuficiente detectado',
                        'suggestion': 'Expandir informações e adicionar mais detalhes'
                    }
                ],
                'strengths': ['Estrutura básica presente'],
                'improvements': ['Adicionar mais detalhes', 'Melhorar clareza'],
                'ai_reasoning': 'Issue precisa de mais informações para ser útil aos desenvolvedores'
            })
        else:
            return json.dumps({
                'overall_quality': 'good',
                'is_approved': True,
                'confidence': 0.9,
                'feedback': [],
                'strengths': ['Título claro', 'Descrição adequada', 'Boa estrutura'],
                'improvements': ['Considera adicionar mais exemplos'],
                'ai_reasoning': 'Issue está bem estruturada e contém informações suficientes'
            })


# Exemplo de uso e testes
if __name__ == "__main__":
    from ..models.issue_model import IssueModel, IssuePriority
    
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Cria agente com provedor mock
    mock_llm = MockLLMProvider()
    agent = IssueReviewerAgent(mock_llm)
    
    # Teste 1: Issue bem estruturada
    good_draft = IssueModel(
        title="Fix database connection timeout in UserService component",
        description="""## Bug Report

### Summary
The UserService component is experiencing database connection timeouts during peak hours.

### Error Details
**Message**: Database connection failed: timeout after 30 seconds
**Component**: UserService
**Frequency**: Multiple times during peak hours

### Impact
Users cannot log in or access their profiles during high traffic periods.

### Steps to Reproduce
1. Access the application during peak hours (2-4 PM)
2. Try to log in with valid credentials
3. Observe the timeout error

### Environment
- Service: UserService v2.1.4
- Database: PostgreSQL 13.2
- Connection Pool: HikariCP

### Additional Context
This started happening after the recent database migration.
""",
        labels=["bug", "automated"],
        priority=IssuePriority.HIGH,
        reproduction_steps=[
            "1. Access application during peak hours",
            "2. Attempt login",
            "3. Observe timeout"
        ],
        environment_info={
            'service_version': 'v2.1.4',
            'database': 'PostgreSQL 13.2'
        }
    )
    
    print("Teste 1 - Issue Bem Estruturada:")
    review1 = agent.review_issue_draft(good_draft)
    print(f"Resultado: {review1.result}")
    print(f"Score: {review1.overall_score}")
    print(f"Aprovada: {agent.should_approve_issue(review1)}")
    
    # Teste 2: Issue mal estruturada
    bad_draft = IssueModel(
        title="Error",
        description="Something is broken",
        labels=[],
        priority=IssuePriority.LOW
    )
    
    print("\nTeste 2 - Issue Mal Estruturada:")
    review2 = agent.review_issue_draft(bad_draft)
    print(f"Resultado: {review2.result}")
    print(f"Score: {review2.overall_score}")
    print(f"Aprovada: {agent.should_approve_issue(review2)}")
    print(f"Melhorias necessárias: {len(agent.get_improvement_priorities(review2))}")
    
    # Info do agente
    print(f"\nInfo do Agente:")
    print(json.dumps(agent.get_agent_info(), indent=2))