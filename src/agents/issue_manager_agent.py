import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

import google.generativeai as genai

from ..models import (
    IssueModel, IssueDraft, IssueStatus, IssuePriority, IssueLabel,
    AnalysisResult, ReviewFeedback, IssueCreationRequest, 
    GitHubIssueCreation, CreationAttempt
)
from ..config import get_settings, get_prompt
from ..tools import GitHubTool


class IssueManagerAgent:
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Ensure API key is available
        if not self.settings.google_ai_api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required but not found in environment")
        
        # Configure Google AI with explicit API key
        genai.configure(api_key=self.settings.google_ai_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_model)
        
        # Generation config
        self.generation_config = {
            "temperature": self.settings.gemini_temperature,
            "max_output_tokens": self.settings.gemini_max_tokens,
        }
        
        # GitHub tool
        self.github_tool = GitHubTool()
    
    def create_and_publish_issue(self, analysis_result: AnalysisResult) -> Optional[IssueModel]:
        """
        Gerencia todo o processo de criação de issue:
        1. Cria rascunho inicial
        2. Revisa qualidade
        3. Refina se necessário (até max_iterations)
        4. Publica no GitHub
        
        Combina as funcionalidades de 4 agentes em um só.
        """
        try:
            self.logger.info("Starting issue creation and publication process")
            
            # Etapa 1: Criar rascunho inicial
            issue_draft = self._create_issue_draft(analysis_result)
            if not issue_draft:
                self.logger.error("Failed to create issue draft")
                return None
            
            # Criar modelo de issue
            issue = IssueModel(
                id=str(uuid4()),
                draft=issue_draft,
                bug_analysis=analysis_result.analysis,
                status=IssueStatus.DRAFT
            )
            
            # Etapa 2: Processo de revisão e refinamento (se habilitado)
            if self.settings.enable_issue_review:
                if not self._review_and_refine_issue(issue):
                    self.logger.error("Issue review and refinement failed")
                    return None
            else:
                # Pular revisão - marcar como aprovado
                issue.update_status(IssueStatus.APPROVED)
            
            # Etapa 3: Publicar no GitHub
            if not self._publish_to_github(issue):
                self.logger.error("Failed to publish issue to GitHub")
                return None
            
            self.logger.info(f"Successfully created and published issue: {issue.github_issue_url}")
            return issue
            
        except Exception as e:
            self.logger.error(f"Error in issue creation process: {str(e)}")
            return None
    
    def _create_issue_draft(self, analysis_result: AnalysisResult) -> Optional[IssueDraft]:
        """Cria o rascunho inicial da issue usando IA."""
        try:
            # Preparar contexto para o prompt
            log_context = analysis_result.log.get_error_context()
            bug_analysis = analysis_result.analysis.get_analysis_summary()
            
            context = {
                "log_context": json.dumps(log_context, indent=2, default=str),
                "bug_analysis": json.dumps(bug_analysis, indent=2, default=str)
            }
            
            # Gerar prompt e solicitar criação
            prompt = get_prompt("issue_drafter", **context)
            
            self.logger.debug("Sending issue draft creation request to AI")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse da resposta
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            result = json.loads(response_text)
            
            # Criar IssueDraft
            draft = IssueDraft(
                title=result["title"],
                description=result["description"],
                reproduction_steps=result.get("reproduction_steps", []),
                expected_behavior=result.get("expected_behavior"),
                actual_behavior=result.get("actual_behavior"),
                environment_info=result.get("environment_info", {}),
                error_details=result.get("error_details", {}),
                stack_trace=result.get("stack_trace"),
                additional_context=result.get("additional_context"),
                suggested_fixes=result.get("suggested_fixes", []),
                resolution_steps=result.get("resolution_steps", [])
            )
            
            # Configurar prioridade e labels baseado na análise
            draft.set_priority_from_severity(analysis_result.analysis.severity)
            
            # Adicionar labels baseado na categoria e severidade
            self._add_smart_labels(draft, analysis_result.analysis)
            
            return draft
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse issue draft response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating issue draft: {e}")
            return None
    
    def _review_and_refine_issue(self, issue: IssueModel) -> bool:
        """Realiza processo de revisão e refinamento da issue."""
        max_iterations = self.settings.max_review_iterations
        
        for iteration in range(max_iterations):
            self.logger.info(f"Starting review iteration {iteration + 1}/{max_iterations}")
            
            # Revisar issue atual
            review = self._review_issue(issue)
            if not review:
                self.logger.error(f"Review failed on iteration {iteration + 1}")
                return False
            
            # Adicionar feedback de revisão
            issue.add_review_feedback(review)
            
            # Se aprovado, parar o processo
            if review.approved:
                self.logger.info("Issue approved by review")
                return True
            
            # Se não aprovado e ainda há iterações, refinar
            if iteration < max_iterations - 1:
                self.logger.info("Issue needs refinement, starting refinement process")
                if not self._refine_issue(issue, review):
                    self.logger.error(f"Refinement failed on iteration {iteration + 1}")
                    return False
            else:
                self.logger.warning("Maximum review iterations reached, proceeding with current version")
                # Forçar aprovação na última iteração se não há erros críticos
                if review.overall_score >= 6.0:  # Threshold mais baixo na última iteração
                    issue.update_status(IssueStatus.APPROVED)
                    return True
                else:
                    return False
        
        return False
    
    def _review_issue(self, issue: IssueModel) -> Optional[ReviewFeedback]:
        """Realiza revisão da qualidade da issue."""
        try:
            # Preparar contexto para revisão
            issue_content = {
                "title": issue.draft.title,
                "description": issue.draft.description,
                "reproduction_steps": issue.draft.reproduction_steps,
                "technical_details": {
                    "environment_info": issue.draft.environment_info,
                    "error_details": issue.draft.error_details,
                    "stack_trace": issue.draft.stack_trace
                },
                "priority": issue.draft.priority,
                "labels": [label.value for label in issue.draft.labels]
            }
            
            bug_analysis = issue.bug_analysis.get_analysis_summary()
            
            context = {
                "issue_content": json.dumps(issue_content, indent=2),
                "bug_analysis": json.dumps(bug_analysis, indent=2)
            }
            
            # Gerar prompt e solicitar revisão
            prompt = get_prompt("issue_reviewer", **context)
            
            self.logger.debug("Sending issue review request to AI")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse da resposta
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            result = json.loads(response_text)
            
            # Criar ReviewFeedback
            review = ReviewFeedback(
                reviewer_id="issue_manager_agent",
                approved=result.get("approved", False),
                overall_score=result.get("overall_score", 0.0),
                completeness_score=result.get("scores", {}).get("completeness", 0.0),
                clarity_score=result.get("scores", {}).get("clarity", 0.0),
                technical_accuracy_score=result.get("scores", {}).get("technical_accuracy", 0.0),
                missing_information=result.get("missing_information", []),
                unclear_sections=result.get("weaknesses", []),
                technical_issues=result.get("technical_issues", []),
                suggestions=result.get("improvement_suggestions", []),
                general_comment=result.get("reviewer_confidence", "AI Review")
            )
            
            return review
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse review response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reviewing issue: {e}")
            return None
    
    def _refine_issue(self, issue: IssueModel, review: ReviewFeedback) -> bool:
        """Refina a issue baseado no feedback de revisão."""
        try:
            # Preparar instruções de refinamento
            refinement_instructions = []
            refinement_instructions.extend(review.missing_information)
            refinement_instructions.extend(review.suggestions)
            
            if review.unclear_sections:
                refinement_instructions.append("Clarificar seções que estão confusas")
            
            if review.technical_issues:
                refinement_instructions.extend(review.technical_issues)
            
            # Preparar contexto para refinamento
            original_issue = {
                "title": issue.draft.title,
                "description": issue.draft.description,
                "reproduction_steps": issue.draft.reproduction_steps,
                "expected_behavior": issue.draft.expected_behavior,
                "actual_behavior": issue.draft.actual_behavior,
                "environment_info": issue.draft.environment_info,
                "error_details": issue.draft.error_details,
                "stack_trace": issue.draft.stack_trace,
                "additional_context": issue.draft.additional_context,
                "suggested_fixes": issue.draft.suggested_fixes,
                "resolution_steps": issue.draft.resolution_steps,
                "priority": issue.draft.priority,
                "labels": [label.value for label in issue.draft.labels]
            }
            
            review_feedback = {
                "overall_score": review.overall_score,
                "approved": review.approved,
                "missing_information": review.missing_information,
                "suggestions": review.suggestions,
                "general_comment": review.general_comment
            }
            
            context = {
                "original_issue": json.dumps(original_issue, indent=2),
                "review_feedback": json.dumps(review_feedback, indent=2),
                "refinement_instructions": refinement_instructions
            }
            
            # Gerar prompt e solicitar refinamento
            prompt = get_prompt("issue_refiner", **context)
            
            self.logger.debug("Sending issue refinement request to AI")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse da resposta
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            result = json.loads(response_text)
            
            # Atualizar draft com versão refinada
            issue.draft.title = result.get("title", issue.draft.title)
            issue.draft.description = result.get("description", issue.draft.description)
            issue.draft.reproduction_steps = result.get("reproduction_steps", issue.draft.reproduction_steps)
            issue.draft.expected_behavior = result.get("expected_behavior", issue.draft.expected_behavior)
            issue.draft.actual_behavior = result.get("actual_behavior", issue.draft.actual_behavior)
            issue.draft.environment_info = result.get("environment_info", issue.draft.environment_info)
            issue.draft.error_details = result.get("error_details", issue.draft.error_details)
            issue.draft.stack_trace = result.get("stack_trace", issue.draft.stack_trace)
            issue.draft.additional_context = result.get("additional_context", issue.draft.additional_context)
            issue.draft.suggested_fixes = result.get("suggested_fixes", issue.draft.suggested_fixes)
            issue.draft.resolution_steps = result.get("resolution_steps", issue.draft.resolution_steps)
            
            # Atualizar prioridade se especificada
            if "priority" in result:
                try:
                    issue.draft.priority = IssuePriority(result["priority"])
                except:
                    pass  # Manter prioridade atual se inválida
            
            # Atualizar labels se especificadas
            if "labels" in result:
                try:
                    new_labels = [IssueLabel(label) for label in result["labels"] if label in [e.value for e in IssueLabel]]
                    issue.draft.labels = new_labels
                except:
                    pass  # Manter labels atuais se inválidas
            
            issue.update_status(IssueStatus.UNDER_REVIEW)
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse refinement response: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error refining issue: {e}")
            return False
    
    def _publish_to_github(self, issue: IssueModel) -> bool:
        """Publica a issue no GitHub."""
        try:
            # Criar request de criação
            creation_request = IssueCreationRequest(
                request_id=str(uuid4()),
                issue_id=issue.id,
                max_attempts=self.settings.max_issue_creation_retries
            )
            
            # Preparar dados para o GitHub
            github_data = GitHubIssueCreation(
                repository_owner=self.settings.github_repository_owner,
                repository_name=self.settings.github_repository_name,
                title=issue.draft.title,
                body=issue.draft.get_markdown_content(),
                labels=[label.value for label in issue.draft.labels] + self.settings.github_default_labels,
                assignees=issue.draft.assignees + self.settings.github_default_assignees
            )
            
            # Tentar criar issue no GitHub
            for attempt_num in range(creation_request.max_attempts):
                self.logger.info(f"GitHub creation attempt {attempt_num + 1}/{creation_request.max_attempts}")
                
                attempt = creation_request.create_attempt(github_data)
                
                if self.github_tool.create_issue(github_data, attempt):
                    # Sucesso - atualizar issue com dados do GitHub
                    creation_request.mark_success(
                        github_data.issue_number,
                        github_data.html_url
                    )
                    
                    issue.mark_as_created(github_data.html_url, github_data.issue_number)
                    
                    return True
                
                # Se falhou mas pode tentar novamente
                if attempt.should_retry() and attempt_num < creation_request.max_attempts - 1:
                    import time
                    time.sleep(self.settings.issue_creation_retry_delay_seconds)
                    continue
                else:
                    break
            
            # Todas as tentativas falharam
            creation_request.mark_failed()
            issue.update_status(IssueStatus.FAILED)
            return False
            
        except Exception as e:
            self.logger.error(f"Error publishing issue to GitHub: {e}")
            issue.update_status(IssueStatus.FAILED)
            return False
    
    def _add_smart_labels(self, draft: IssueDraft, analysis) -> None:
        """Adiciona labels inteligentes baseadas na análise."""
        # Label obrigatória
        draft.add_label(IssueLabel.BUG)
        draft.add_label(IssueLabel.AUTO_GENERATED)
        
        # Labels baseadas na severidade
        if analysis.severity.value == "critical":
            draft.add_label(IssueLabel.CRITICAL)
        elif analysis.severity.value == "high":
            draft.add_label(IssueLabel.HIGH_PRIORITY)
        
        # Labels baseadas na categoria
        category_mapping = {
            "runtime_error": IssueLabel.RUNTIME_ERROR,
            "network_error": IssueLabel.NETWORK_ISSUE,
            "database_error": IssueLabel.DATABASE_ISSUE,
            "security_issue": IssueLabel.SECURITY,
            "performance_issue": IssueLabel.PERFORMANCE
        }
        
        category_label = category_mapping.get(analysis.category.value)
        if category_label:
            draft.add_label(category_label)
        
        # Label para investigação se confidence baixa
        if analysis.confidence_score < 0.8:
            draft.add_label(IssueLabel.NEEDS_INVESTIGATION)