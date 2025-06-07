"""
Agente responsável por refinar e melhorar issues baseado no feedback do revisor.
Este agente pega o feedback detalhado e aplica melhorias específicas na issue.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.issue_model import IssueModel
from ..models.review_model import IssueReview, ReviewCriteria, ReviewStatus
from ..models.bug_analysis import BugAnalysis
from ..models.log_model import LogModel


class IssueRefinerAgent:
    """
    Agente especializado em refinar issues baseado no feedback de revisão.
    
    Responsabilidades:
    - Analisar feedback detalhado do revisor
    - Aplicar melhorias específicas em cada seção da issue
    - Garantir que todas as sugestões sejam implementadas
    - Manter a qualidade e consistência da issue
    """
    
    def __init__(self, agent_name: str = "IssueRefinerAgent"):
        self.agent_name = agent_name
        self.logger = logging.getLogger(self.agent_name)
        
        # Configurações de refinamento
        self.min_title_length = 20
        self.max_title_length = 100
        self.min_description_length = 100
        
        # Templates para melhorias
        self.improvement_templates = self._init_improvement_templates()
    
    def _init_improvement_templates(self) -> Dict[str, str]:
        """Inicializa templates para diferentes tipos de melhoria"""
        return {
            "technical_context": """
## 🔧 Contexto Técnico
- **Aplicação/Serviço:** {service_name}
- **Ambiente:** {environment}
- **Timestamp:** {timestamp}
- **Versão:** {version}
- **Servidor/Container:** {server_info}
""",
            "reproduction_steps": """
## 🔄 Passos para Reproduzir
1. **Pré-condições:** {preconditions}
2. **Ação que causou o erro:** {trigger_action}
3. **Dados/Parâmetros envolvidos:** {parameters}
4. **Resultado esperado:** {expected_result}
5. **Resultado atual:** {actual_result}
""",
            "impact_analysis": """
## 📊 Análise de Impacto
- **Criticidade:** {criticality}
- **Frequência:** {frequency}
- **Usuários Afetados:** {affected_users}
- **Funcionalidades Impactadas:** {affected_features}
- **Consequências:** {consequences}
""",
            "stack_trace_section": """
## 🐛 Stack Trace
```
{stack_trace}
```
""",
            "log_details": """
## 📝 Detalhes do Log
- **Nível:** {log_level}
- **Origem:** {log_source}
- **Thread/Processo:** {thread_info}
- **Mensagem Original:**
```
{original_message}
```
"""
        }
    
    async def refine_issue(
        self, 
        current_issue: IssueModel, 
        review: IssueReview,
        bug_analysis: BugAnalysis,
        original_log: LogModel
    ) -> IssueModel:
        """
        Refina uma issue baseado no feedback de revisão.
        
        Args:
            current_issue: Issue atual que precisa ser refinada
            review: Feedback detalhado do revisor
            bug_analysis: Análise original do bug
            original_log: Log original que gerou o bug
            
        Returns:
            IssueModel: Issue refinada com melhorias aplicadas
        """
        self.logger.info(f"Iniciando refinamento da issue: {current_issue.title}")
        
        try:
            # Cria uma cópia da issue para modificação
            refined_issue = self._copy_issue(current_issue)
            
            # Aplica melhorias baseadas no feedback
            await self._apply_title_improvements(refined_issue, review, bug_analysis)
            await self._apply_description_improvements(refined_issue, review, bug_analysis, original_log)
            await self._apply_technical_improvements(refined_issue, review, bug_analysis, original_log)
            await self._apply_formatting_improvements(refined_issue, review)
            await self._apply_priority_improvements(refined_issue, review, bug_analysis)
            
            # Adiciona metadados de refinamento
            refined_issue.metadata = refined_issue.metadata or {}
            refined_issue.metadata.update({
                "refined_by": self.agent_name,
                "refinement_timestamp": datetime.now().isoformat(),
                "review_score": review.overall_score,
                "improvements_applied": self._get_applied_improvements(review)
            })
            
            self.logger.info(f"Refinamento concluído. Melhorias aplicadas: {len(self._get_applied_improvements(review))}")
            return refined_issue
            
        except Exception as e:
            self.logger.error(f"Erro durante refinamento: {str(e)}")
            raise
    
    def _copy_issue(self, issue: IssueModel) -> IssueModel:
        """Cria uma cópia profunda da issue para modificação"""
        return IssueModel(
            title=issue.title,
            body=issue.body,
            labels=issue.labels.copy() if issue.labels else [],
            assignees=issue.assignees.copy() if issue.assignees else [],
            priority=issue.priority,
            metadata=issue.metadata.copy() if issue.metadata else {}
        )
    
    async def _apply_title_improvements(
        self, 
        issue: IssueModel, 
        review: IssueReview, 
        bug_analysis: BugAnalysis
    ):
        """Aplica melhorias no título da issue"""
        title_feedback = self._get_criteria_feedback(review, ReviewCriteria.TITLE_CLARITY)
        
        if title_feedback and title_feedback.score < 4:
            self.logger.info("Melhorando título da issue")
            
            # Reconstrói o título com mais contexto
            new_title = self._build_improved_title(issue, bug_analysis, title_feedback)
            
            if new_title != issue.title:
                issue.title = new_title
                self.logger.info(f"Título atualizado: {new_title}")
    
    def _build_improved_title(
        self, 
        issue: IssueModel, 
        bug_analysis: BugAnalysis, 
        feedback
    ) -> str:
        """Constrói um título melhorado"""
        # Componentes do título
        components = []
        
        # Adiciona criticidade se alta
        if bug_analysis.criticality.value in ["HIGH", "CRITICAL"]:
            components.append(f"[{bug_analysis.criticality.value}]")
        
        # Adiciona tipo de erro
        if bug_analysis.error_type:
            components.append(f"{bug_analysis.error_type}:")
        
        # Melhora a descrição principal
        main_description = self._improve_title_description(issue.title, bug_analysis)
        components.append(main_description)
        
        # Adiciona contexto se necessário
        if bug_analysis.affected_component:
            components.append(f"em {bug_analysis.affected_component}")
        
        new_title = " ".join(components)
        
        # Garante que está dentro dos limites
        if len(new_title) > self.max_title_length:
            new_title = new_title[:self.max_title_length-3] + "..."
        
        return new_title
    
    def _improve_title_description(self, current_title: str, bug_analysis: BugAnalysis) -> str:
        """Melhora a descrição principal do título"""
        # Remove prefixos comuns se existirem
        clean_title = current_title
        prefixes_to_remove = ["[HIGH]", "[CRITICAL]", "[MEDIUM]", "[LOW]", "Bug:", "Error:"]
        
        for prefix in prefixes_to_remove:
            if clean_title.startswith(prefix):
                clean_title = clean_title[len(prefix):].strip()
        
        # Se o título está muito genérico, adiciona mais especificidade
        generic_terms = ["erro", "falha", "problema", "bug", "exception"]
        
        if any(term in clean_title.lower() for term in generic_terms):
            if bug_analysis.error_message:
                # Extrai a parte mais informativa da mensagem de erro
                specific_part = self._extract_specific_error_part(bug_analysis.error_message)
                if specific_part:
                    clean_title = f"{clean_title} - {specific_part}"
        
        return clean_title
    
    def _extract_specific_error_part(self, error_message: str) -> str:
        """Extrai a parte mais específica de uma mensagem de erro"""
        # Remove stack traces e mantém apenas a mensagem principal
        lines = error_message.split('\n')
        main_message = lines[0].strip()
        
        # Remove informações muito técnicas
        if ':' in main_message:
            parts = main_message.split(':')
            # Pega a parte após o último ':'
            specific_part = parts[-1].strip()
            if len(specific_part) > 20:
                return specific_part[:50] + "..." if len(specific_part) > 50 else specific_part
        
        return main_message[:50] + "..." if len(main_message) > 50 else main_message
    
    async def _apply_description_improvements(
        self, 
        issue: IssueModel, 
        review: IssueReview,
        bug_analysis: BugAnalysis,
        original_log: LogModel
    ):
        """Aplica melhorias na descrição da issue"""
        desc_feedback = self._get_criteria_feedback(review, ReviewCriteria.DESCRIPTION_COMPLETENESS)
        
        if desc_feedback and desc_feedback.score < 4:
            self.logger.info("Melhorando descrição da issue")
            
            # Reconstrói a descrição com seções bem definidas
            new_description = self._build_improved_description(issue, bug_analysis, original_log, desc_feedback)
            issue.body = new_description
    
    def _build_improved_description(
        self, 
        issue: IssueModel,
        bug_analysis: BugAnalysis,
        original_log: LogModel,
        feedback
    ) -> str:
        """Constrói uma descrição melhorada"""
        sections = []
        
        # Seção de resumo
        sections.append(f"## 📋 Resumo\n{self._build_summary_section(bug_analysis)}")
        
        # Seção de impacto
        sections.append(self._build_impact_section(bug_analysis))
        
        # Seção de contexto técnico
        sections.append(self._build_technical_context_section(bug_analysis, original_log))
        
        # Seção de reprodução
        sections.append(self._build_reproduction_section(bug_analysis, original_log))
        
        # Seção de log details
        sections.append(self._build_log_details_section(original_log))
        
        # Seção de stack trace se disponível
        if bug_analysis.stack_trace:
            sections.append(self._build_stack_trace_section(bug_analysis.stack_trace))
        
        return "\n\n".join(sections)
    
    def _build_summary_section(self, bug_analysis: BugAnalysis) -> str:
        """Constrói seção de resumo"""
        summary = bug_analysis.summary or "Bug detectado automaticamente pelo sistema de monitoramento."
        
        if bug_analysis.error_message:
            summary += f"\n\n**Erro Principal:** {bug_analysis.error_message}"
        
        return summary
    
    def _build_impact_section(self, bug_analysis: BugAnalysis) -> str:
        """Constrói seção de análise de impacto"""
        return self.improvement_templates["impact_analysis"].format(
            criticality=bug_analysis.criticality.value,
            frequency="A determinar",
            affected_users="A determinar",
            affected_features=bug_analysis.affected_component or "A determinar",
            consequences=self._determine_consequences(bug_analysis)
        )
    
    def _determine_consequences(self, bug_analysis: BugAnalysis) -> str:
        """Determina as consequências baseado na criticidade"""
        consequences_map = {
            "CRITICAL": "Sistema pode estar inacessível ou com falhas graves",
            "HIGH": "Funcionalidade importante comprometida",
            "MEDIUM": "Funcionalidade com comportamento inesperado",
            "LOW": "Problema menor que pode afetar experiência do usuário"
        }
        
        return consequences_map.get(bug_analysis.criticality.value, "A avaliar")
    
    def _build_technical_context_section(self, bug_analysis: BugAnalysis, original_log: LogModel) -> str:
        """Constrói seção de contexto técnico"""
        return self.improvement_templates["technical_context"].format(
            service_name=bug_analysis.affected_component or "A determinar",
            environment=original_log.environment or "production",
            timestamp=original_log.timestamp,
            version=original_log.version or "A determinar",
            server_info=original_log.source or "A determinar"
        )
    
    def _build_reproduction_section(self, bug_analysis: BugAnalysis, original_log: LogModel) -> str:
        """Constrói seção de passos para reproduzir"""
        return self.improvement_templates["reproduction_steps"].format(
            preconditions="A determinar",
            trigger_action=self._extract_trigger_action(bug_analysis, original_log),
            parameters=self._extract_parameters(original_log),
            expected_result="Operação deve completar sem erros",
            actual_result=bug_analysis.error_message or "Erro detectado"
        )
    
    def _extract_trigger_action(self, bug_analysis: BugAnalysis, original_log: LogModel) -> str:
        """Extrai a ação que causou o erro"""
        if bug_analysis.affected_component:
            return f"Operação relacionada a {bug_analysis.affected_component}"
        
        # Tenta extrair do log
        if original_log.message:
            # Procura por padrões como "failed to", "error in", etc.
            message_lower = original_log.message.lower()
            if "failed to" in message_lower:
                action_part = original_log.message[message_lower.find("failed to"):].split('.')[0]
                return action_part
            elif "error in" in message_lower:
                action_part = original_log.message[message_lower.find("error in"):].split('.')[0]
                return action_part
        
        return "A determinar baseado na análise do erro"
    
    def _extract_parameters(self, original_log: LogModel) -> str:
        """Extrai parâmetros do log"""
        params = []
        
        if original_log.user_id:
            params.append(f"User ID: {original_log.user_id}")
        
        if original_log.session_id:
            params.append(f"Session ID: {original_log.session_id}")
        
        if original_log.request_id:
            params.append(f"Request ID: {original_log.request_id}")
        
        return ", ".join(params) if params else "A determinar"
    
    def _build_log_details_section(self, original_log: LogModel) -> str:
        """Constrói seção de detalhes do log"""
        return self.improvement_templates["log_details"].format(
            log_level=original_log.level.value,
            log_source=original_log.source or "A determinar",
            thread_info=original_log.thread_id or "A determinar",
            original_message=original_log.message
        )
    
    def _build_stack_trace_section(self, stack_trace: str) -> str:
        """Constrói seção de stack trace"""
        return self.improvement_templates["stack_trace_section"].format(
            stack_trace=stack_trace
        )
    
    async def _apply_technical_improvements(
        self, 
        issue: IssueModel,
        review: IssueReview,
        bug_analysis: BugAnalysis,
        original_log: LogModel
    ):
        """Aplica melhorias técnicas na issue"""
        tech_feedback = self._get_criteria_feedback(review, ReviewCriteria.TECHNICAL_ACCURACY)
        
        if tech_feedback and tech_feedback.score < 4:
            self.logger.info("Aplicando melhorias técnicas")
            
            # Adiciona labels técnicas mais específicas
            self._improve_technical_labels(issue, bug_analysis)
            
            # Melhora metadados técnicos
            self._improve_technical_metadata(issue, bug_analysis, original_log)
    
    def _improve_technical_labels(self, issue: IssueModel, bug_analysis: BugAnalysis):
        """Melhora as labels técnicas da issue"""
        if not issue.labels:
            issue.labels = []
        
        # Remove labels genéricas
        generic_labels = ["bug", "error"]
        issue.labels = [label for label in issue.labels if label not in generic_labels]
        
        # Adiciona labels específicas
        new_labels = ["bug"]  # Mantém bug como base
        
        # Label por criticidade
        new_labels.append(f"priority-{bug_analysis.criticality.value.lower()}")
        
        # Label por tipo de erro
        if bug_analysis.error_type:
            error_label = bug_analysis.error_type.lower().replace(" ", "-")
            new_labels.append(f"error-{error_label}")
        
        # Label por componente
        if bug_analysis.affected_component:
            component_label = bug_analysis.affected_component.lower().replace(" ", "-")
            new_labels.append(f"component-{component_label}")
        
        # Label automática
        new_labels.append("automated")
        
        issue.labels = list(set(new_labels))  # Remove duplicatas
    
    def _improve_technical_metadata(
        self, 
        issue: IssueModel,
        bug_analysis: BugAnalysis,
        original_log: LogModel
    ):
        """Melhora os metadados técnicos"""
        if not issue.metadata:
            issue.metadata = {}
        
        issue.metadata.update({
            "error_type": bug_analysis.error_type,
            "criticality": bug_analysis.criticality.value,
            "log_level": original_log.level.value,
            "log_timestamp": original_log.timestamp,
            "affected_component": bug_analysis.affected_component,
            "environment": original_log.environment,
            "automated_detection": True
        })
    
    async def _apply_formatting_improvements(self, issue: IssueModel, review: IssueReview):
        """Aplica melhorias de formatação"""
        formatting_feedback = self._get_criteria_feedback(review, ReviewCriteria.FORMATTING)
        
        if formatting_feedback and formatting_feedback.score < 4:
            self.logger.info("Aplicando melhorias de formatação")
            
            # Melhora formatação do corpo da issue
            issue.body = self._improve_markdown_formatting(issue.body)
    
    def _improve_markdown_formatting(self, body: str) -> str:
        """Melhora a formatação Markdown"""
        # Adiciona quebras de linha consistentes
        lines = body.split('\n')
        improved_lines = []
        
        for i, line in enumerate(lines):
            # Adiciona espaçamento antes de headers
            if line.startswith('#') and i > 0 and lines[i-1].strip():
                improved_lines.append('')
            
            improved_lines.append(line)
            
            # Adiciona espaçamento após headers
            if line.startswith('#') and i < len(lines)-1 and lines[i+1].strip():
                improved_lines.append('')
        
        return '\n'.join(improved_lines)
    
    async def _apply_priority_improvements(
        self, 
        issue: IssueModel,
        review: IssueReview,
        bug_analysis: BugAnalysis
    ):
        """Aplica melhorias na classificação de prioridade"""
        priority_feedback = self._get_criteria_feedback(review, ReviewCriteria.PRIORITY_CLASSIFICATION)
        
        if priority_feedback and priority_feedback.score < 4:
            self.logger.info("Ajustando classificação de prioridade")
            
            # Reavalia prioridade baseado na análise
            issue.priority = self._determine_improved_priority(bug_analysis)
    
    def _determine_improved_priority(self, bug_analysis: BugAnalysis) -> str:
        """Determina uma prioridade melhorada"""
        criticality_to_priority = {
            "CRITICAL": "P0",
            "HIGH": "P1", 
            "MEDIUM": "P2",
            "LOW": "P3"
        }
        
        return criticality_to_priority.get(bug_analysis.criticality.value, "P2")
    
    def _get_criteria_feedback(self, review: IssueReview, criteria: ReviewCriteria):
        """Busca feedback específico para um critério"""
        for feedback in review.feedbacks:
            if feedback.criteria == criteria:
                return feedback
        return None
    
    def _get_applied_improvements(self, review: IssueReview) -> list:
        """Retorna lista de melhorias que foram aplicadas"""
        improvements = []
        
        for feedback in review.feedbacks:
            if feedback.score < 4:
                improvements.append(feedback.criteria.value)
        
        return improvements