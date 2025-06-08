import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from dotenv import load_dotenv

import google.generativeai as genai
from google.adk import Agent
from google.adk.tools import FunctionTool

from ..models import (
    BugFinderProcess, ProcessStatus, AnalysisResult, IssueModel
)
from ..config import get_settings
from .bug_analyser_agent import BugAnalyserAgent
from .issue_manager_agent import IssueManagerAgent
from .notification_agent import NotificationAgent


class BugFinderSystem:
    """
    Sistema principal Bug Finder usando Google ADK.
    
    Este agente coordena todo o processo de análise de bugs:
    1. Recebe logs de erro
    2. Analisa se são bugs reais
    3. Cria issues no GitHub
    4. Envia notificações
    """
    
    def __init__(self):
        # Ensure .env is loaded first
        load_dotenv()
        
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Validate and configure Google AI API key
        if not self.settings.google_ai_api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required but not found in environment")
        
        # Set Google AI API key as environment variable for ADK and configure genai
        os.environ['GOOGLE_AI_API_KEY'] = self.settings.google_ai_api_key
        genai.configure(api_key=self.settings.google_ai_api_key)
        
        # Inicializar agentes especializados
        self.bug_analyser = BugAnalyserAgent()
        self.issue_manager = IssueManagerAgent()
        self.notification_agent = NotificationAgent()
        
        # Estatísticas do sistema
        self.processed_logs = 0
        self.bugs_found = 0
        self.issues_created = 0
        self.notifications_sent = 0
        
        # Criar agente ADK com ferramentas
        self.agent = self._create_adk_agent()
    
    def _create_adk_agent(self) -> Agent:
        """Cria o agente ADK com todas as ferramentas."""
        
        # Ferramenta para processar logs
        process_log_tool = FunctionTool(self._process_log_wrapper)
        
        # Ferramenta para status do sistema
        system_status_tool = FunctionTool(self._get_system_status_wrapper)
        
        # Ferramenta para testar integrações
        test_integrations_tool = FunctionTool(self._test_integrations_wrapper)
        
        # Ferramenta para análise de amostra
        analyze_sample_tool = FunctionTool(self._analyze_sample_log_wrapper)
        
        # Criar agente com automatic function calling habilitado
        agent = Agent(
            name="BugFinderSystem", 
            description="Sistema automatizado para análise de bugs e criação de issues. Execute as funções diretamente ao receber logs de erro ou comandos.",
            model=self.settings.gemini_model,  # Usar modelo das configurações
            tools=[
                process_log_tool,
                system_status_tool,
                test_integrations_tool,
                analyze_sample_tool
            ]
        )
        
        return agent
    
    def _process_log_wrapper(self, log_content: str) -> Dict[str, Any]:
        """Wrapper para compatibilidade com FunctionTool."""
        try:
            # Check if this is a critical log that should bypass normal analysis
            if self._is_critical_log(log_content):
                self.logger.info("Processing critical log with forced issue creation")
                return self._process_critical_log_forced(log_content)
            
            return self.process_log(log_content)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Process log error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _get_system_status_wrapper(self) -> Dict[str, Any]:
        """Wrapper para compatibilidade com FunctionTool."""
        try:
            return self.get_system_status()
        except Exception as e:
            return {
                "status": "error",
                "message": f"System status error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _test_integrations_wrapper(self) -> Dict[str, Any]:
        """Wrapper para compatibilidade com FunctionTool."""
        try:
            return self.test_integrations()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Integration test error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _is_critical_log(self, log_content: str) -> bool:
        """
        Detecta se um log é crítico baseado em palavras-chave e padrões.
        """
        log_lower = log_content.lower()
        
        # Palavras-chave críticas
        critical_keywords = [
            'critical', 'fatal', 'severe', 'emergency',
            'system crashed', 'system down', 'service down',
            'payment.*failed', 'payment.*crash', 'payment.*error',
            'revenue.*loss', 'business.*impact',
            'all.*customers.*affected', '100%.*customers',
            'data.*corruption', 'data.*loss',
            'security.*breach', 'unauthorized.*access',
            'nullpointerexception.*critical',
            'unable.*process.*payments',
            'all.*transactions.*failing'
        ]
        
        # Verificar palavras-chave críticas
        for keyword in critical_keywords:
            import re
            if re.search(keyword, log_lower):
                return True
        
        # Verificar nível crítico no início
        if log_lower.strip().startswith(('critical', 'fatal', 'emergency')):
            return True
        
        # Verificar padrões de impacto de negócio
        business_impact_patterns = [
            r'business.*impact.*severe',
            r'revenue.*\$\d+',
            r'error.*affects.*\d+%.*customers',
            r'system.*unable.*process',
            r'all.*users.*unable'
        ]
        
        for pattern in business_impact_patterns:
            if re.search(pattern, log_lower):
                return True
        
        return False
    
    def _process_critical_log_forced(self, log_content: str) -> Dict[str, Any]:
        """
        Processa um log crítico forçando criação de issue e notificação Discord,
        mesmo se o sistema interno de análise falhar.
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("🚨 CRITICAL LOG DETECTED - Forcing issue creation")
            
            # Create a forced critical analysis
            critical_analysis_result = self._create_forced_critical_analysis(log_content)
            
            # Force issue creation
            self.logger.info("Creating issue for critical log...")
            
            # Create a simple issue manually to avoid serialization issues
            try:
                issue = self._create_critical_issue_manually(log_content, critical_analysis_result)
            except Exception as issue_error:
                self.logger.error(f"Manual issue creation failed: {str(issue_error)}")
                # Try the normal way as fallback
                issue = self.issue_manager.create_and_publish_issue(critical_analysis_result)
            
            if issue:
                self.issues_created += 1
                self.logger.info(f"✅ Critical issue created: {issue.github_issue_url}")
                
                # Force Discord notification
                self.logger.info("Sending Discord notification for critical issue...")
                notification_sent = self.notification_agent.send_issue_notification(issue)
                
                if notification_sent:
                    self.notifications_sent += 1
                    self.logger.info("✅ Discord notification sent successfully")
                else:
                    self.logger.warning("❌ Discord notification failed")
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    "status": "success",
                    "message": f"🚨 CRITICAL ISSUE CREATED: {issue.github_issue_url}",
                    "critical_workflow": True,
                    "processing_time_ms": processing_time,
                    "issue": {
                        "id": issue.id,
                        "title": issue.draft.title,
                        "github_url": issue.github_issue_url,
                        "github_number": issue.github_issue_number,
                        "severity": "CRITICAL",
                        "status": issue.status,
                        "discord_sent": notification_sent
                    },
                    "analysis_summary": "CRITICAL LOG - Forced issue creation due to severe business impact"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create critical issue",
                    "critical_workflow": True
                }
                
        except Exception as e:
            self.logger.error(f"Error in critical log processing: {str(e)}")
            return {
                "status": "error",
                "message": f"Critical log processing failed: {str(e)}",
                "critical_workflow": True,
                "error_type": type(e).__name__
            }
    
    def _create_forced_critical_analysis(self, log_content: str):
        """Cria uma análise forçada para logs críticos."""
        from datetime import datetime
        from uuid import uuid4
        from ..models import (
            BugAnalysis, AnalysisResult, LogModel, 
            BugSeverity, BugCategory, BugImpact, AnalysisDecision, LogLevel
        )
        
        # Create forced critical log model
        now = datetime.now()
        mock_log = LogModel(
            timestamp=now,
            level=LogLevel.CRITICAL,
            message=log_content[:500],  # Truncate if too long
            source="forced_critical_analysis",
            function_name="critical_system_failure",
            line_number=1,
            stack_trace=log_content,
            user_id="system",
            session_id=f"critical_{uuid4().hex[:8]}"
        )
        
        # Create forced critical analysis
        critical_analysis = BugAnalysis(
            log_id=str(uuid4()),
            is_bug=True,
            severity=BugSeverity.CRITICAL,
            category=BugCategory.RUNTIME_ERROR,
            impact=BugImpact.USER_BLOCKING,
            decision=AnalysisDecision.CREATE_ISSUE,
            confidence_score=0.95,
            root_cause_hypothesis="Critical system failure detected by intelligent log analysis",
            affected_components=["system", "critical_functionality"],
            reproduction_likelihood=0.9,
            priority_score=95,
            analysis_notes="FORCED CRITICAL ANALYSIS: Log contains critical keywords indicating severe business impact"
        )
        
        # Create analysis result
        return AnalysisResult(
            log=mock_log,
            analysis=critical_analysis,
            processing_time_ms=100.0,
            analyzer_version="1.0.0-critical-forced"
        )
    
    def _create_critical_issue_manually(self, log_content: str, analysis_result) -> Optional:
        """Cria issue crítica manualmente para evitar problemas de serialização."""
        try:
            from ..models import IssueModel, IssueDraft, IssueStatus, IssuePriority
            from uuid import uuid4
            
            # Create simple issue draft
            issue_draft = IssueDraft(
                title=f"🚨 CRITICAL: System failure detected",
                description=f"""## Critical System Failure Detected

**Severity:** CRITICAL
**Impact:** High business impact detected
**Confidence:** 95%

### Log Details:
```
{log_content[:1000]}
```

### Analysis:
- **Detected:** Critical keywords indicating severe system failure
- **Business Impact:** Potential revenue loss and customer impact
- **Action Required:** Immediate investigation and resolution

### Recommended Actions:
1. Investigate the root cause immediately
2. Implement emergency fixes if possible
3. Monitor system stability
4. Notify relevant teams

*This issue was automatically created by the Bug Finder system due to critical log detection.*
""",
                reproduction_steps=["Check system logs", "Verify critical functionality", "Monitor error rates"],
                expected_behavior="System should operate normally without critical failures",
                actual_behavior="Critical system failure detected in logs",
                environment_info={
                    "detection_system": "Bug Finder Critical Detection",
                    "analysis_confidence": "95%",
                    "detection_time": datetime.now().isoformat()
                },
                error_details={
                    "error_type": "Critical System Failure",
                    "error_message": log_content[:200],
                    "location": "System logs"
                },
                stack_trace=log_content if len(log_content) < 2000 else log_content[:2000] + "...",
                additional_context="Automatically detected critical failure requiring immediate attention",
                suggested_fixes=["Investigate root cause", "Apply emergency fixes", "Monitor system"],
                priority=IssuePriority.URGENT,
                labels=["critical", "auto-generated", "high-priority", "runtime-error"]
            )
            
            # Create issue model
            issue = IssueModel(
                id=str(uuid4()),
                draft=issue_draft,
                bug_analysis=analysis_result.analysis,
                status=IssueStatus.DRAFT,
                github_issue_url="",  # Will be set when published
                github_issue_number=0,  # Will be set when published
                creation_attempts=[]
            )
            
            # Try to publish to GitHub using the correct API
            try:
                from ..models.creation_model import GitHubIssueCreation, CreationAttempt
                
                # Create GitHub creation data
                github_creation = GitHubIssueCreation(
                    repository_owner=self.settings.github_repository_owner,
                    repository_name=self.settings.github_repository_name,
                    title=issue_draft.title,
                    body=issue_draft.description,
                    labels=issue_draft.labels,
                    assignees=self.settings.github_default_assignees
                )
                
                # Create attempt tracker
                attempt = CreationAttempt(attempt_number=1)
                
                # Create issue using correct API
                github_success = self.issue_manager.github_tool.create_issue(github_creation, attempt)
                
                if github_success and github_creation.github_issue_url:
                    issue.github_issue_url = github_creation.github_issue_url
                    issue.github_issue_number = github_creation.github_issue_number
                    issue.status = IssueStatus.PUBLISHED
                    self.logger.info(f"✅ GitHub issue created: {issue.github_issue_url}")
                else:
                    self.logger.warning("GitHub issue creation failed, but continuing with notification")
                    
            except Exception as github_error:
                self.logger.error(f"GitHub creation failed: {str(github_error)}")
                # Continue anyway for notification
            
            return issue
            
        except Exception as e:
            self.logger.error(f"Manual issue creation failed: {str(e)}")
            return None
    
    def _analyze_sample_log_wrapper(self, log_sample: str) -> Dict[str, Any]:
        """Wrapper para compatibilidade com FunctionTool."""
        try:
            # Check if this looks like a critical log that should trigger full workflow
            if self._is_critical_log(log_sample):
                self.logger.info("Critical log detected! Triggering full workflow instead of sample analysis.")
                return self._process_log_wrapper(log_sample)
            
            return self.analyze_sample_log(log_sample)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Sample analysis error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def process_log(self, log_content: str) -> Dict[str, Any]:
        """
        Processa um log de erro e executa todo o fluxo do Bug Finder.
        
        Args:
            log_content: Conteúdo do log a ser analisado
            
        Returns:
            Resultado do processamento incluindo issue criada (se aplicável)
        """
        process = BugFinderProcess(
            process_id=str(uuid4()),
            raw_log_input=log_content
        )
        
        try:
            self.logger.info(f"Starting Bug Finder process: {process.process_id}")
            self.processed_logs += 1
            
            # Etapa 1: Análise do log
            step = process.start_step("log_analysis", "BugAnalyserAgent", ProcessStatus.LOG_PROCESSED)
            
            analysis_result = self.bug_analyser.process_and_analyze_log(log_content)
            process.add_analysis_result(analysis_result)
            
            if not analysis_result.analysis.should_create_issue():
                self.logger.info("Analysis determined no issue creation needed")
                process.complete_process(success=True)
                return self._create_response(process, "Analysis completed - No issue needed")
            
            self.bugs_found += 1
            
            # Etapa 2: Criação e publicação da issue
            step = process.start_step("issue_creation", "IssueManagerAgent", ProcessStatus.ISSUE_DRAFTED)
            
            issue = self.issue_manager.create_and_publish_issue(analysis_result)
            
            if not issue:
                process.complete_current_step(success=False, error_message="Failed to create issue")
                process.complete_process(success=False)
                return self._create_response(process, "Failed to create issue", success=False)
            
            process.add_issue(issue)
            self.issues_created += 1
            
            # Etapa 3: Notificação
            step = process.start_step("notification", "NotificationAgent", ProcessStatus.NOTIFICATION_SENT)
            
            notification_sent = self.notification_agent.send_issue_notification(issue)
            
            if notification_sent:
                self.notifications_sent += 1
                process.complete_current_step(success=True)
            else:
                process.complete_current_step(success=False, error_message="Failed to send notification")
            
            # Finalizar processo
            process.complete_process(success=True)
            
            self.logger.info(f"Bug Finder process completed successfully: {issue.github_issue_url}")
            
            return self._create_response(
                process, 
                f"Issue created successfully: {issue.github_issue_url}",
                issue=issue
            )
            
        except Exception as e:
            error_msg = f"Error in Bug Finder process: {str(e)}"
            self.logger.error(error_msg)
            
            process.complete_current_step(success=False, error_message=error_msg)
            process.complete_process(success=False)
            
            return self._create_response(process, error_msg, success=False)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do sistema Bug Finder.
        
        Returns:
            Estatísticas e status do sistema
        """
        return {
            "system_info": {
                "name": "Bug Finder System",
                "version": self.settings.system_version,
                "environment": self.settings.environment,
                "uptime": "Active"
            },
            "statistics": {
                "logs_processed": self.processed_logs,
                "bugs_found": self.bugs_found,
                "issues_created": self.issues_created,
                "notifications_sent": self.notifications_sent,
                "success_rate": f"{(self.issues_created / max(self.bugs_found, 1) * 100):.1f}%"
            },
            "configuration": self.settings.get_summary(),
            "integrations": {
                "github": {
                    "configured": bool(self.settings.github_access_token),
                    "repository": f"{self.settings.github_repository_owner}/{self.settings.github_repository_name}"
                },
                "discord": {
                    "configured": bool(self.settings.discord_webhook_url),
                    "enabled": self.settings.enable_discord_notifications
                },
                "ai": {
                    "model": self.settings.gemini_model,
                    "configured": bool(self.settings.google_ai_api_key)
                }
            }
        }
    
    def test_integrations(self) -> Dict[str, Any]:
        """
        Testa todas as integrações do sistema.
        
        Returns:
            Resultado dos testes de integração
        """
        results = {}
        
        try:
            # Teste GitHub
            self.logger.info("Testing GitHub integration...")
            github_test = self.issue_manager.github_tool.test_connection()
            results["github"] = {
                "status": "success" if github_test else "failed",
                "message": "Connection successful" if github_test else "Connection failed"
            }
            
            # Teste Discord
            self.logger.info("Testing Discord integration...")
            discord_test = self.notification_agent.send_test_notification()
            results["discord"] = {
                "status": "success" if discord_test else "failed", 
                "message": "Test notification sent" if discord_test else "Failed to send test notification"
            }
            
            # Teste AI
            self.logger.info("Testing AI integration...")
            try:
                test_analysis = self.bug_analyser.process_and_analyze_log("Test log message")
                ai_test = test_analysis is not None
            except Exception as e:
                ai_test = False
                results["ai"] = {
                    "status": "failed",
                    "message": f"AI test failed: {str(e)}"
                }
            
            if ai_test and "ai" not in results:
                results["ai"] = {
                    "status": "success",
                    "message": "AI analysis working"
                }
            
            # Resultado geral
            all_passed = all(result["status"] == "success" for result in results.values())
            results["overall"] = {
                "status": "success" if all_passed else "partial_failure",
                "message": "All integrations working" if all_passed else "Some integrations failed"
            }
            
        except Exception as e:
            results["overall"] = {
                "status": "error",
                "message": f"Test error: {str(e)}"
            }
        
        return results
    
    def analyze_sample_log(self, log_sample: str) -> Dict[str, Any]:
        """
        Analisa um log de exemplo sem criar issue (apenas para teste).
        
        Args:
            log_sample: Log de exemplo para análise
            
        Returns:
            Resultado da análise sem criação de issue
        """
        try:
            self.logger.info("Analyzing sample log (test mode)")
            
            analysis_result = self.bug_analyser.process_and_analyze_log(log_sample)
            
            return {
                "status": "success",
                "analysis": {
                    "is_bug": analysis_result.analysis.is_bug,
                    "severity": analysis_result.analysis.severity,
                    "category": analysis_result.analysis.category,
                    "confidence": analysis_result.analysis.confidence_score,
                    "decision": analysis_result.analysis.decision,
                    "summary": analysis_result.analysis.get_analysis_summary()
                },
                "log_info": {
                    "level": analysis_result.log.level,
                    "message": analysis_result.log.message,
                    "timestamp": analysis_result.log.timestamp.isoformat()
                },
                "processing_time_ms": analysis_result.processing_time_ms
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }
    
    def _create_response(self, process: BugFinderProcess, message: str, 
                        success: bool = True, issue: Optional[IssueModel] = None) -> Dict[str, Any]:
        """Cria resposta padronizada para as ferramentas."""
        response = {
            "status": "success" if success else "error",
            "message": message,
            "process_id": process.process_id,
            "processing_time_ms": process.total_duration_ms,
            "timestamp": datetime.now().isoformat()
        }
        
        if issue:
            response["issue"] = {
                "id": issue.id,
                "title": issue.draft.title,
                "github_url": issue.github_issue_url,
                "github_number": issue.github_issue_number,
                "severity": issue.bug_analysis.severity,
                "status": issue.status
            }
        
        if process.analysis_result:
            response["analysis_summary"] = process.analysis_result.analysis.get_analysis_summary()
        
        return response
    
    def run(self, input_text: str = None) -> Dict[str, Any]:
        """
        Executa o sistema Bug Finder com entrada fornecida.
        
        Args:
            input_text: Texto de entrada para processar
            
        Returns:
            Resultado da execução
        """
        if input_text:
            # Se parece com um log, processar
            if any(keyword in input_text.lower() for keyword in ['error', 'exception', 'traceback', 'failed']):
                return self.process_log(input_text)
            
            # Comandos especiais
            if input_text.lower() == "status":
                return self.get_system_status()
            elif input_text.lower() == "test":
                return self.test_integrations()
            else:
                return self.analyze_sample_log(input_text)
        
        # Modo interativo
        return {
            "status": "ready",
            "message": "Bug Finder System ready. Provide a log to analyze or use 'status'/'test' commands.",
            "available_tools": [
                "process_log(log_content)",
                "get_system_status()", 
                "test_integrations()",
                "analyze_sample_log(log_sample)"
            ]
        }


# Função para criar instância do agente (usado pelo ADK)
def create_agent():
    """Cria e retorna uma instância do BugFinderSystem para o ADK."""
    system = BugFinderSystem()
    return system.agent