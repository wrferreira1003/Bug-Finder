"""
BugFinderAgent - Agente Maestro Principal

Localização: src/agents/bug_finder_agent.py

Responsabilidades:
- Coordenar todo o fluxo de processamento de bugs
- Orquestrar a execução dos agentes especializados
- Gerenciar o estado do processo
- Implementar lógica de retry e recuperação de erros
- Fornecer interface unificada para o sistema

Este é o agente principal que atua como "maestro",
conduzindo a orquestra de agentes especializados em harmonia.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from ..models.log_model import LogModel
from ..models.bug_analysis import BugAnalysis
from ..models.issue_model import IssueModel
from ..models.review_model import IssueReview
from ..models.creation_model import IssueCreationResult, CreationStatus
from ..models.notification_model import NotificationResult, NotificationStatus
from ..models.process_model import ProcessResult, ProcessStatus, ProcessStep

from .log_receiver_agent import LogReceiverAgent
from .bug_analyser_agent import BugAnalyserAgent
from .issue_drafter_agent import IssueDrafterAgent
from .issue_reviewer_agent import IssueReviewerAgent
from .issue_refiner_agent import IssueRefinerAgent
from .issue_creator_agent import IssueCreatorAgent
from .issue_notificator_agent import IssueNotificatorAgent

from ..config.settings import get_settings


class ProcessPhase(Enum):
    """Fases do processamento de bugs."""
    RECEIVING = "receiving"
    ANALYZING = "analyzing"
    DRAFTING = "drafting"
    REVIEWING = "reviewing"
    REFINING = "refining"
    CREATING = "creating"
    NOTIFYING = "notifying"
    COMPLETED = "completed"
    FAILED = "failed"


class BugFinderAgent:
    """
    Agente principal que coordena todo o sistema de detecção e criação de bugs.
    
    Este agente orquestra todos os outros agentes especializados,
    gerenciando o fluxo completo desde a recepção de logs até a notificação.
    """
    
    def __init__(self, 
                 log_receiver: LogReceiverAgent,
                 bug_analyser: BugAnalyserAgent,
                 issue_drafter: IssueDrafterAgent,
                 issue_reviewer: IssueReviewerAgent,
                 issue_refiner: IssueRefinerAgent,
                 issue_creator: IssueCreatorAgent,
                 issue_notificator: IssueNotificatorAgent):
        """
        Inicializa o agente maestro com todos os agentes especializados.
        
        Args:
            log_receiver: Agente recebedor de logs
            bug_analyser: Agente analisador de bugs
            issue_drafter: Agente criador de rascunhos
            issue_reviewer: Agente revisor de issues
            issue_refiner: Agente refinador de issues
            issue_creator: Agente criador de issues no GitHub
            issue_notificator: Agente notificador Discord
        """
        self.log_receiver = log_receiver
        self.bug_analyser = bug_analyser
        self.issue_drafter = issue_drafter
        self.issue_reviewer = issue_reviewer
        self.issue_refiner = issue_refiner
        self.issue_creator = issue_creator
        self.issue_notificator = issue_notificator
        
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Configurações do processo
        self.process_config = {
            'max_refinement_iterations': 3,
            'enable_auto_retry': True,
            'retry_failed_steps': True,
            'save_intermediate_results': True,
            'timeout_seconds': 300,
            'enable_parallel_processing': False  # Para futuras melhorias
        }
        
        # Contadores de métricas
        self.metrics = {
            'total_logs_processed': 0,
            'bugs_detected': 0,
            'issues_created': 0,
            'notifications_sent': 0,
            'errors_encountered': 0,
            'average_processing_time': 0.0
        }
    
    def process_log(self, raw_log: Union[str, Dict[str, Any]]) -> ProcessResult:
        """
        Processa um log completo através de todo o pipeline.
        
        Args:
            raw_log: Log bruto para processar
            
        Returns:
            Resultado completo do processamento
        """
        process_start_time = datetime.now()
        process_id = f"process_{int(process_start_time.timestamp())}"
        
        self.logger.info(f"Iniciando processamento completo: {process_id}")
        
        # Inicializa resultado do processo
        process_result = ProcessResult(
            process_id=process_id,
            status=ProcessStatus.RUNNING,
            started_at=process_start_time.isoformat(),
            steps_completed=[],
            current_phase=ProcessPhase.RECEIVING,
            raw_log=raw_log
        )
        
        try:
            # Fase 1: Recepção e estruturação do log
            log_entry = self._execute_log_reception(raw_log, process_result)
            if not log_entry:
                return self._finalize_process_failure(process_result, "Falha na recepção do log")
            
            # Fase 2: Análise do bug
            bug_analysis = self._execute_bug_analysis(log_entry, process_result)
            if not bug_analysis:
                return self._finalize_process_failure(process_result, "Falha na análise do bug")
            
            # Verifica se deve continuar processamento
            if not self.bug_analyser.should_continue_processing(bug_analysis):
                return self._finalize_process_skip(process_result, "Bug não requer criação de issue", bug_analysis)
            
            # Fase 3: Criação do rascunho
            issue_draft = self._execute_issue_drafting(log_entry, bug_analysis, process_result)
            if not issue_draft:
                return self._finalize_process_failure(process_result, "Falha na criação do rascunho")
            
            # Fase 4: Revisão e refinamento (loop)
            final_draft = self._execute_review_refinement_loop(issue_draft, process_result)
            if not final_draft:
                return self._finalize_process_failure(process_result, "Falha no processo de revisão/refinamento")
            
            # Fase 5: Criação da issue no GitHub
            creation_result = self._execute_issue_creation(final_draft, process_result)
            if not creation_result or creation_result.status != CreationStatus.SUCCESS:
                return self._finalize_process_failure(process_result, "Falha na criação da issue no GitHub")
            
            # Fase 6: Notificação no Discord
            notification_result = self._execute_notification(creation_result, final_draft, process_result)
            
            # Finalização do processo
            return self._finalize_process_success(process_result, creation_result, notification_result)
            
        except Exception as e:
            self.logger.error(f"Erro crítico durante processamento: {str(e)}")
            self.metrics['errors_encountered'] += 1
            return self._finalize_process_failure(process_result, f"Erro crítico: {str(e)}")
        
        finally:
            # Atualiza métricas
            self._update_processing_metrics(process_start_time)
    
    def _execute_log_reception(self, raw_log: Union[str, Dict[str, Any]], process_result: ProcessResult) -> Optional[LogModel]:
        """
        Executa fase de recepção e estruturação do log.
        """
        try:
            self.logger.info("Executando recepção do log")
            process_result.current_phase = ProcessPhase.RECEIVING
            
            log_entry = self.log_receiver.receive_log(raw_log)
            
            if log_entry:
                step = ProcessStep(
                    phase=ProcessPhase.RECEIVING,
                    status=ProcessStatus.SUCCESS,
                    started_at=datetime.now().isoformat(),
                    completed_at=datetime.now().isoformat(),
                    agent='LogReceiverAgent',
                    result={'log_entry_id': log_entry.id}
                )
                process_result.steps_completed.append(step)
                process_result.log_entry = log_entry
                self.logger.info(f"Log recebido e estruturado: {log_entry.id}")
            else:
                step = ProcessStep(
                    phase=ProcessPhase.RECEIVING,
                    status=ProcessStatus.FAILED,
                    started_at=datetime.now().isoformat(),
                    completed_at=datetime.now().isoformat(),
                    agent='LogReceiverAgent',
                    error='Log inválido ou malformado'
                )
                process_result.steps_completed.append(step)
                self.logger.error("Falha na recepção do log")
            
            return log_entry
            
        except Exception as e:
            self.logger.error(f"Erro na recepção do log: {str(e)}")
            step = ProcessStep(
                phase=ProcessPhase.RECEIVING,
                status=ProcessStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='LogReceiverAgent',
                error=str(e)
            )
            process_result.steps_completed.append(step)
            return None
    
    def _execute_bug_analysis(self, log_entry: LogModel, process_result: ProcessResult) -> Optional[BugAnalysis]:
        """
        Executa fase de análise do bug.
        """
        try:
            self.logger.info("Executando análise do bug")
            process_result.current_phase = ProcessPhase.ANALYZING
            
            bug_analysis = self.bug_analyser.analyze_log(log_entry)
            
            step = ProcessStep(
                phase=ProcessPhase.ANALYZING,
                status=ProcessStatus.SUCCESS,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='BugAnalyserAgent',
                result={
                    'analysis_id': bug_analysis.id,
                    'is_bug': bug_analysis.is_bug,
                    'criticality': bug_analysis.criticality.value,
                    'confidence': bug_analysis.confidence_score
                }
            )
            process_result.steps_completed.append(step)
            process_result.bug_analysis = bug_analysis
            
            self.logger.info(f"Análise concluída - É bug: {bug_analysis.is_bug}, Criticidade: {bug_analysis.criticality}")
            
            if bug_analysis.is_bug:
                self.metrics['bugs_detected'] += 1
            
            return bug_analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise do bug: {str(e)}")
            step = ProcessStep(
                phase=ProcessPhase.ANALYZING,
                status=ProcessStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='BugAnalyserAgent',
                error=str(e)
            )
            process_result.steps_completed.append(step)
            return None
    
    def _execute_issue_drafting(self, log_entry: LogModel, bug_analysis: BugAnalysis, process_result: ProcessResult) -> Optional[IssueModel]:
        """
        Executa fase de criação do rascunho da issue.
        """
        try:
            self.logger.info("Executando criação do rascunho")
            process_result.current_phase = ProcessPhase.DRAFTING
            
            issue_draft = self.issue_drafter.create_issue_draft(log_entry, bug_analysis)
            
            step = ProcessStep(
                phase=ProcessPhase.DRAFTING,
                status=ProcessStatus.SUCCESS,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueDrafterAgent',
                result={
                    'draft_id': issue_draft.id,
                    'title': issue_draft.title,
                    'labels_count': len(issue_draft.labels),
                    'priority': issue_draft.priority.value
                }
            )
            process_result.steps_completed.append(step)
            process_result.issue_draft = issue_draft
            
            self.logger.info(f"Rascunho criado: {issue_draft.title[:50]}...")
            
            return issue_draft
            
        except Exception as e:
            self.logger.error(f"Erro na criação do rascunho: {str(e)}")
            step = ProcessStep(
                phase=ProcessPhase.DRAFTING,
                status=ProcessStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueDrafterAgent',
                error=str(e)
            )
            process_result.steps_completed.append(step)
            return None
    
    def _execute_review_refinement_loop(self, initial_draft: IssueModel, process_result: ProcessResult) -> Optional[IssueModel]:
        """
        Executa loop de revisão e refinamento até aprovação ou limite de iterações.
        """
        current_draft = initial_draft
        iteration = 1
        max_iterations = self.process_config['max_refinement_iterations']
        
        while iteration <= max_iterations:
            self.logger.info(f"Iniciando iteração {iteration} de revisão/refinamento")
            
            # Fase de revisão
            review_result = self._execute_issue_review(current_draft, process_result, iteration)
            if not review_result:
                return None
            
            # Se aprovado, retorna o draft atual
            if self.issue_reviewer.should_approve_issue(review_result):
                self.logger.info(f"Issue aprovada na iteração {iteration}")
                return current_draft
            
            # Se não aprovado e é a última iteração, falha
            if iteration >= max_iterations:
                self.logger.warning(f"Limite de iterações atingido ({max_iterations}), usando último draft")
                return current_draft
            
            # Fase de refinamento
            refined_draft = self._execute_issue_refinement(current_draft, review_result, process_result, iteration)
            if not refined_draft:
                return None
            
            current_draft = refined_draft
            iteration += 1
        
        return current_draft
    
    def _execute_issue_review(self, issue_draft: IssueModel, process_result: ProcessResult, iteration: int) -> Optional[IssueReview]:
        """
        Executa fase de revisão da issue.
        """
        try:
            self.logger.info(f"Executando revisão da issue (iteração {iteration})")
            process_result.current_phase = ProcessPhase.REVIEWING
            
            review_result = self.issue_reviewer.review_issue_draft(issue_draft)
            
            step = ProcessStep(
                phase=ProcessPhase.REVIEWING,
                status=ProcessStatus.SUCCESS,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueReviewerAgent',
                result={
                    'review_id': review_result.id,
                    'result': review_result.result.value,
                    'score': review_result.overall_score,
                    'feedback_count': len(review_result.feedback),
                    'iteration': iteration
                }
            )
            process_result.steps_completed.append(step)
            
            self.logger.info(f"Revisão concluída - Resultado: {review_result.result}, Score: {review_result.overall_score}")
            
            return review_result
            
        except Exception as e:
            self.logger.error(f"Erro na revisão da issue: {str(e)}")
            step = ProcessStep(
                phase=ProcessPhase.REVIEWING,
                status=ProcessStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueReviewerAgent',
                error=str(e)
            )
            process_result.steps_completed.append(step)
            return None
    
    def _execute_issue_refinement(self, issue_draft: IssueModel, review_result: IssueReview, 
                                 process_result: ProcessResult, iteration: int) -> Optional[IssueModel]:
        """
        Executa fase de refinamento da issue.
        """
        try:
            self.logger.info(f"Executando refinamento da issue (iteração {iteration})")
            process_result.current_phase = ProcessPhase.REFINING
            
            refined_draft = self.issue_refiner.refine_issue_draft(issue_draft, review_result)
            
            # Gera resumo das melhorias
            improvement_summary = self.issue_refiner.get_refinement_summary(issue_draft, refined_draft)
            
            step = ProcessStep(
                phase=ProcessPhase.REFINING,
                status=ProcessStatus.SUCCESS,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueRefinerAgent',
                result={
                    'refined_draft_id': refined_draft.id,
                    'improvements_count': improvement_summary['total_changes'],
                    'iteration': iteration,
                    'improvements': improvement_summary['improvements_applied']
                }
            )
            process_result.steps_completed.append(step)
            
            self.logger.info(f"Refinamento concluído - {improvement_summary['total_changes']} melhorias aplicadas")
            
            return refined_draft
            
        except Exception as e:
            self.logger.error(f"Erro no refinamento da issue: {str(e)}")
            step = ProcessStep(
                phase=ProcessPhase.REFINING,
                status=ProcessStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueRefinerAgent',
                error=str(e)
            )
            process_result.steps_completed.append(step)
            return None
    
    def _execute_issue_creation(self, issue_draft: IssueModel, process_result: ProcessResult) -> Optional[IssueCreationResult]:
        """
        Executa fase de criação da issue no GitHub.
        """
        try:
            self.logger.info("Executando criação da issue no GitHub")
            process_result.current_phase = ProcessPhase.CREATING
            
            creation_result = self.issue_creator.create_issue(issue_draft)
            
            step_status = ProcessStatus.SUCCESS if creation_result.status == CreationStatus.SUCCESS else ProcessStatus.FAILED
            
            step = ProcessStep(
                phase=ProcessPhase.CREATING,
                status=step_status,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueCreatorAgent',
                result={
                    'creation_status': creation_result.status.value,
                    'github_issue_url': self.issue_creator.get_issue_url(creation_result),
                    'github_issue_number': creation_result.github_issue.number if creation_result.github_issue else None
                } if creation_result.status == CreationStatus.SUCCESS else None,
                error=creation_result.message if creation_result.status != CreationStatus.SUCCESS else None
            )
            process_result.steps_completed.append(step)
            process_result.creation_result = creation_result
            
            if creation_result.status == CreationStatus.SUCCESS:
                self.metrics['issues_created'] += 1
                self.logger.info(f"Issue criada com sucesso: {creation_result.github_issue.url}")
            else:
                self.logger.error(f"Falha na criação da issue: {creation_result.message}")
            
            return creation_result
            
        except Exception as e:
            self.logger.error(f"Erro na criação da issue: {str(e)}")
            step = ProcessStep(
                phase=ProcessPhase.CREATING,
                status=ProcessStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueCreatorAgent',
                error=str(e)
            )
            process_result.steps_completed.append(step)
            return None
    
    def _execute_notification(self, creation_result: IssueCreationResult, issue_draft: IssueModel, 
                            process_result: ProcessResult) -> Optional[NotificationResult]:
        """
        Executa fase de notificação no Discord.
        """
        try:
            self.logger.info("Executando notificação no Discord")
            process_result.current_phase = ProcessPhase.NOTIFYING
            
            if creation_result.status == CreationStatus.SUCCESS:
                notification_result = self.issue_notificator.notify_issue_created(creation_result, issue_draft)
            else:
                notification_result = self.issue_notificator.notify_creation_failure(creation_result, issue_draft)
            
            step_status = ProcessStatus.SUCCESS if notification_result.status == NotificationStatus.SUCCESS else ProcessStatus.FAILED
            
            step = ProcessStep(
                phase=ProcessPhase.NOTIFYING,
                status=step_status,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueNotificatorAgent',
                result={
                    'notification_status': notification_result.status.value,
                    'discord_channel': notification_result.discord_channel,
                    'discord_message_id': notification_result.discord_message_id
                } if notification_result.status == NotificationStatus.SUCCESS else None,
                error=notification_result.message if notification_result.status != NotificationStatus.SUCCESS else None
            )
            process_result.steps_completed.append(step)
            process_result.notification_result = notification_result
            
            if notification_result.status == NotificationStatus.SUCCESS:
                self.metrics['notifications_sent'] += 1
                self.logger.info(f"Notificação enviada com sucesso para: {notification_result.discord_channel}")
            else:
                self.logger.warning(f"Falha na notificação: {notification_result.message}")
            
            return notification_result
            
        except Exception as e:
            self.logger.error(f"Erro na notificação: {str(e)}")
            step = ProcessStep(
                phase=ProcessPhase.NOTIFYING,
                status=ProcessStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                agent='IssueNotificatorAgent',
                error=str(e)
            )
            process_result.steps_completed.append(step)
            return None
    
    def _finalize_process_success(self, process_result: ProcessResult, creation_result: IssueCreationResult, 
                                 notification_result: Optional[NotificationResult]) -> ProcessResult:
        """
        Finaliza processo com sucesso.
        """
        process_result.status = ProcessStatus.SUCCESS
        process_result.current_phase = ProcessPhase.COMPLETED
        process_result.completed_at = datetime.now().isoformat()
        process_result.github_issue_url = self.issue_creator.get_issue_url(creation_result)
        
        # Calcula tempo total de processamento
        start_time = datetime.fromisoformat(process_result.started_at)
        end_time = datetime.now()
        process_result.processing_time_seconds = (end_time - start_time).total_seconds()
        
        self.logger.info(f"Processo finalizado com sucesso: {process_result.process_id}")
        self.logger.info(f"Issue criada: {process_result.github_issue_url}")
        self.logger.info(f"Tempo de processamento: {process_result.processing_time_seconds:.2f}s")
        
        return process_result
    
    def _finalize_process_failure(self, process_result: ProcessResult, error_message: str) -> ProcessResult:
        """
        Finaliza processo com falha.
        """
        process_result.status = ProcessStatus.FAILED
        process_result.current_phase = ProcessPhase.FAILED
        process_result.completed_at = datetime.now().isoformat()
        process_result.error_message = error_message
        
        # Calcula tempo até falha
        start_time = datetime.fromisoformat(process_result.started_at)
        end_time = datetime.now()
        process_result.processing_time_seconds = (end_time - start_time).total_seconds()
        
        self.logger.error(f"Processo falhou: {process_result.process_id} - {error_message}")
        
        return process_result
    
    def _finalize_process_skip(self, process_result: ProcessResult, skip_reason: str, bug_analysis: BugAnalysis) -> ProcessResult:
        """
        Finaliza processo que foi pulado (não é bug crítico).
        """
        process_result.status = ProcessStatus.SKIPPED
        process_result.current_phase = ProcessPhase.COMPLETED
        process_result.completed_at = datetime.now().isoformat()
        process_result.skip_reason = skip_reason
        
        # Calcula tempo de processamento
        start_time = datetime.fromisoformat(process_result.started_at)
        end_time = datetime.now()
        process_result.processing_time_seconds = (end_time - start_time).total_seconds()
        
        self.logger.info(f"Processo pulado: {process_result.process_id} - {skip_reason}")
        self.logger.info(f"Análise: É bug: {bug_analysis.is_bug}, Criticidade: {bug_analysis.criticality}")
        
        return process_result
    
    def _update_processing_metrics(self, start_time: datetime):
        """
        Atualiza métricas de processamento.
        """
        self.metrics['total_logs_processed'] += 1
        
        # Calcula tempo médio (média móvel simples)
        current_time = (datetime.now() - start_time).total_seconds()
        current_avg = self.metrics['average_processing_time']
        total_processed = self.metrics['total_logs_processed']
        
        new_avg = ((current_avg * (total_processed - 1)) + current_time) / total_processed
        self.metrics['average_processing_time'] = new_avg
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas do sistema.
        """
        return {
            'metrics': self.metrics.copy(),
            'success_rate': (self.metrics['issues_created'] / max(1, self.metrics['total_logs_processed'])) * 100,
            'notification_rate': (self.metrics['notifications_sent'] / max(1, self.metrics['issues_created'])) * 100,
            'error_rate': (self.metrics['errors_encountered'] / max(1, self.metrics['total_logs_processed'])) * 100,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Retorna status dos agentes do sistema.
        """
        agents_info = {
            'log_receiver': self.log_receiver.get_agent_info(),
            'bug_analyser': self.bug_analyser.get_agent_info(),
            'issue_drafter': self.issue_drafter.get_agent_info(),
            'issue_reviewer': self.issue_reviewer.get_agent_info(),
            'issue_refiner': self.issue_refiner.get_agent_info(),
            'issue_creator': self.issue_creator.get_agent_info(),
            'issue_notificator': self.issue_notificator.get_agent_info()
        }
        
        return {
            'system_name': 'BugFinder',
            'version': '1.0.0',
            'status': 'operational',
            'agents': agents_info,
            'process_config': self.process_config,
            'metrics': self.get_system_metrics()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente maestro.
        """
        return {
            'name': 'BugFinderAgent',
            'version': '1.0.0',
            'description': 'Agente maestro que coordena todo o sistema de detecção e criação de bugs',
            'role': 'orchestrator',
            'capabilities': [
                'Coordenação de agentes especializados',
                'Gerenciamento de fluxo de processamento',
                'Loop de revisão e refinamento',
                'Tratamento de erros e retry',
                'Coleta de métricas',
                'Monitoramento de status do sistema'
            ],
            'input_format': 'raw_log (str ou dict)',
            'output_format': 'ProcessResult',
            'managed_agents': [
                'LogReceiverAgent',
                'BugAnalyserAgent', 
                'IssueDrafterAgent',
                'IssueReviewerAgent',
                'IssueRefinerAgent',
                'IssueCreatorAgent',
                'IssueNotificatorAgent'
            ],
            'process_phases': [phase.value for phase in ProcessPhase],
            'process_config': self.process_config
        }


# Exemplo de uso e testes
if __name__ == "__main__":
    # Este exemplo mostra como seria inicializado o sistema completo
    # Na prática, seria feito através de um factory ou container de dependências
    
    logging.basicConfig(level=logging.INFO)
    
    print("BugFinderAgent - Sistema Completo")
    print("=" * 50)
    
    # Simulação de inicialização (os agentes reais seriam injetados)
    print("Inicializando agentes especializados...")
    
    # Exemplo de estrutura do sistema
    system_info = {
        'name': 'BugFinder',
        'version': '1.0.0',
        'description': 'Sistema inteligente de detecção e criação automática de bugs',
        'architecture': 'Multi-Agent System',
        'agents_count': 8,
        'phases': [
            'Log Reception',
            'Bug Analysis',
            'Issue Drafting', 
            'Issue Review',
            'Issue Refinement',
            'GitHub Creation',
            'Discord Notification'
        ],
        'features': [
            'Processamento automático de logs',
            'Análise inteligente de criticidade',
            'Criação de issues estruturadas',
            'Loop de revisão e refinamento',
            'Integração GitHub/Discord',
            'Métricas e monitoramento'
        ]
    }
    
    print(f"Sistema: {system_info['name']} v{system_info['version']}")
    print(f"Arquitetura: {system_info['architecture']}")
    print(f"Agentes: {system_info['agents_count']}")
    print("\nFases de Processamento:")
    for i, phase in enumerate(system_info['phases'], 1):
        print(f"  {i}. {phase}")
    
    print("\nRecursos:")
    for feature in system_info['features']:
        print(f"  ✓ {feature}")
    
    print("\n" + "=" * 50)
    print("Sistema pronto para processar logs e criar issues automaticamente!")
    print("Uso: bug_finder.process_log(raw_log)")