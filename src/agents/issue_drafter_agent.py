"""
IssueModelerAgent - Agente Criador de Rascunhos de Issues

Localização: src/agents/issue_drafter_agent.py

Responsabilidades:
- Criar rascunhos bem estruturados de issues do GitHub
- Gerar títulos claros e descritivos
- Escrever descrições detalhadas com contexto técnico
- Incluir passos para reprodução quando possível
- Formatar adequadamente para o GitHub (Markdown)

Este agente atua como um "escritor especializado", transformando 
análises técnicas em documentação clara para desenvolvedores.
"""

import json
import logging
from typing import Dict, Any, Optional, Protocol
from datetime import datetime

from ..models.log_model import LogModel
from ..models.bug_analysis import BugAnalysis
from ..models.issue_model import IssueModel, IssuePriority
from ..config.prompts import IssueDrafterPrompts
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


class IssueModelerAgent:
    """
    Agente responsável por criar rascunhos estruturados de issues.
    
    Este agente usa IA para transformar análises de bugs em issues
    bem documentadas, seguindo as melhores práticas de documentação.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Inicializa o agente criador de rascunhos.
        
        Args:
            llm_provider: Provedor do modelo de linguagem a ser usado
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.prompts = IssueDrafterPrompts()
        
    def create_issue_draft(self, log_entry: LogModel, bug_analysis: BugAnalysis) -> IssueModel:
        """
        Cria um rascunho de issue baseado no log e análise do bug.
        
        Args:
            log_entry: Log original que gerou o bug
            bug_analysis: Análise detalhada do bug
            
        Returns:
            Rascunho estruturado da issue
        """
        try:
            self.logger.info(f"Criando rascunho de issue para bug: {bug_analysis.log_entry_id}")
            
            # Preparação do contexto para criação
            drafting_context = self._prepare_drafting_context(log_entry, bug_analysis)
            
            # Geração do conteúdo principal usando IA
            draft_content = self._generate_issue_content(log_entry, bug_analysis, drafting_context)
            
            # Validação e refinamento do conteúdo
            validated_content = self._validate_draft_content(draft_content)
            
            # Criação do objeto de rascunho final
            issue_draft = self._create_issue_draft_object(
                log_entry, bug_analysis, validated_content
            )
            
            self.logger.info(f"Rascunho criado com sucesso. Título: {issue_draft.title[:50]}...")
            
            return issue_draft
            
        except Exception as e:
            self.logger.error(f"Erro durante criação do rascunho: {str(e)}")
            # Retorna rascunho de fallback em caso de erro
            return self._create_fallback_draft(log_entry, bug_analysis)
    
    def _prepare_drafting_context(self, log_entry: LogModel, bug_analysis: BugAnalysis) -> Dict[str, Any]:
        """
        Prepara contexto para criação do rascunho.
        """
        context = {
            # Informações do log
            'log_level': log_entry.level.value,
            'log_source': log_entry.source.value,
            'log_component': log_entry.component or 'Unknown',
            'log_message': log_entry.message,
            'has_stack_trace': bool(log_entry.stack_trace),
            'log_timestamp': log_entry.timestamp,
            
            # Informações da análise
            'bug_type': bug_analysis.bug_type.value,
            'criticality': bug_analysis.criticality.value,
            'confidence': bug_analysis.confidence_score,
            'ai_reasoning': bug_analysis.reasoning,
            'technical_details': bug_analysis.technical_details,
            
            # Configurações do projeto
            'project_name': self.settings.get('project_name', 'Application'),
            'issue_template': self.settings.get('issue_template', 'bug_report'),
            
            # Metadados
            'created_by': 'BugFinder (Automated)',
            'automation_version': '1.0.0'
        }
        
        return context
    
    def _generate_issue_content(self, log_entry: LogModel, bug_analysis: BugAnalysis, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera o conteúdo principal da issue usando IA.
        """
        # Constrói o prompt para criação do rascunho
        drafting_prompt = self.prompts.get_issue_drafting_prompt(log_entry, bug_analysis, context)
        
        # Gera resposta do modelo
        ai_response = self.llm_provider.generate_response(drafting_prompt, context)
        
        # Faz parsing da resposta JSON
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            self.logger.warning("Resposta da IA não é JSON válido, tentando parsing alternativo")
            return self._parse_alternative_draft_response(ai_response, context)
    
    def _parse_alternative_draft_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz parsing alternativo da resposta da IA.
        """
        # Implementação básica de fallback
        lines = response.strip().split('\n')
        
        # Tenta extrair título (primeira linha não vazia)
        title = "Bug Report: Application Error"
        for line in lines:
            if line.strip() and not line.startswith('#'):
                title = f"Bug: {line.strip()[:80]}"
                break
        
        # Usa a resposta completa como descrição
        description = f"""## Bug Report

**Auto-generated from log analysis**

### Error Details
{response}

### Original Log
- **Level**: {context.get('log_level', 'Unknown')}
- **Component**: {context.get('log_component', 'Unknown')}
- **Timestamp**: {context.get('log_timestamp', 'Unknown')}

### Message
```
{context.get('log_message', 'No message available')}
```

### Analysis
- **Bug Type**: {context.get('bug_type', 'Unknown')}
- **Criticality**: {context.get('criticality', 'Unknown')}
- **Confidence**: {context.get('confidence', 0)}

*This issue was automatically generated by BugFinder.*
"""
        
        return {
            'title': title,
            'description': description,
            'labels': self._generate_labels_from_context(context),
            'priority': self._determine_priority_from_context(context),
            'assignees': [],
            'milestone': None,
            'reproduction_steps': self._generate_basic_reproduction_steps(context),
            'environment_info': self._extract_environment_info(context),
            'additional_context': context.get('technical_details', {})
        }
    
    def _generate_labels_from_context(self, context: Dict[str, Any]) -> list:
        """
        Gera labels baseadas no contexto.
        """
        labels = ['bug', 'automated']
        
        # Adiciona label de criticidade
        criticality = context.get('criticality', '').lower()
        if criticality in ['high', 'critical']:
            labels.append('critical')
        elif criticality == 'medium':
            labels.append('medium-priority')
        
        # Adiciona label do componente
        component = context.get('log_component', '').lower()
        if component and component != 'unknown':
            labels.append(f'component:{component}')
        
        # Adiciona label do tipo de bug
        bug_type = context.get('bug_type', '').lower()
        if 'database' in bug_type:
            labels.append('database')
        elif 'network' in bug_type or 'connection' in bug_type:
            labels.append('network')
        elif 'authentication' in bug_type:
            labels.append('security')
        
        return labels
    
    def _determine_priority_from_context(self, context: Dict[str, Any]) -> str:
        """
        Determina prioridade baseada no contexto.
        """
        criticality = context.get('criticality', '').lower()
        
        if criticality in ['high', 'critical']:
            return 'high'
        elif criticality == 'medium':
            return 'medium'
        else:
            return 'low'
    
    def _generate_basic_reproduction_steps(self, context: Dict[str, Any]) -> list:
        """
        Gera passos básicos de reprodução.
        """
        steps = [
            "1. Check the application logs for similar error patterns",
            f"2. Monitor the {context.get('log_component', 'affected')} component",
            "3. Verify the error conditions that led to this issue"
        ]
        
        if context.get('has_stack_trace'):
            steps.append("4. Review the stack trace for the exact failure point")
        
        return steps
    
    def _extract_environment_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai informações do ambiente.
        """
        return {
            'timestamp': context.get('log_timestamp'),
            'component': context.get('log_component'),
            'source': context.get('log_source'),
            'log_level': context.get('log_level'),
            'detection_method': 'Automated log analysis'
        }
    
    def _validate_draft_content(self, draft_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e ajusta o conteúdo do rascunho.
        """
        validated = draft_content.copy()
        
        # Valida título
        title = validated.get('title', '')
        if not title or len(title) < 10:
            validated['title'] = "Bug Report: Application Error Detected"
        elif len(title) > 100:
            validated['title'] = title[:97] + "..."
        
        # Valida descrição
        description = validated.get('description', '')
        if not description or len(description) < 50:
            validated['description'] = self._generate_minimal_description(validated)
        
        # Valida labels
        labels = validated.get('labels', [])
        if not labels:
            validated['labels'] = ['bug', 'automated']
        
        # Valida prioridade
        priority = validated.get('priority', 'medium')
        if priority not in ['low', 'medium', 'high']:
            validated['priority'] = 'medium'
        
        # Garante campos obrigatórios
        validated.setdefault('assignees', [])
        validated.setdefault('milestone', None)
        validated.setdefault('reproduction_steps', [])
        validated.setdefault('environment_info', {})
        validated.setdefault('additional_context', {})
        
        return validated
    
    def _generate_minimal_description(self, content: Dict[str, Any]) -> str:
        """
        Gera descrição mínima quando a IA falha.
        """
        return f"""## Bug Report (Auto-generated)

**Title**: {content.get('title', 'Unknown Error')}

This issue was automatically detected and requires investigation.

**Priority**: {content.get('priority', 'medium')}
**Labels**: {', '.join(content.get('labels', []))}

*This is an automated bug report. Please investigate and update with additional details.*
"""
    
    def _create_issue_draft_object(self, log_entry: LogModel, bug_analysis: BugAnalysis, content: Dict[str, Any]) -> IssueModel:
        """
        Cria objeto IssueModel a partir do conteúdo gerado.
        """
        # Converte strings para enums
        try:
            priority = IssuePriority[content.get('priority', 'MEDIUM').upper()]
        except KeyError:
            priority = IssuePriority.MEDIUM
        
        # Converte labels para enums
        labels = []
        for label_str in content.get('labels', []):
            try:
                labels.append(IssueLabel[label_str.upper().replace('-', '_')])
            except KeyError:
                # Para labels customizadas, adiciona como string
                labels.append(label_str)
        
        return IssueModel(
            title=content['title'],
            description=content['description'],
            labels=labels,
            priority=priority,
            assignees=content.get('assignees', []),
            milestone=content.get('milestone'),
            reproduction_steps=content.get('reproduction_steps', []),
            environment_info=content.get('environment_info', {}),
            additional_context=content.get('additional_context', {}),
            source_log_id=log_entry.id,
            source_analysis_id=bug_analysis.id,
            created_by='IssueModelerAgent',
            created_at=datetime.now().isoformat()
        )
    
    def _create_fallback_draft(self, log_entry: LogModel, bug_analysis: BugAnalysis) -> IssueModel:
        """
        Cria rascunho de fallback em caso de erro.
        """
        return IssueModel(
            title=f"Bug: {log_entry.message[:60]}..." if len(log_entry.message) > 60 else f"Bug: {log_entry.message}",
            description=f"""## Bug Report (Fallback Generation)

**Error Message**: {log_entry.message}

**Log Details**:
- Level: {log_entry.level.value}
- Component: {log_entry.component or 'Unknown'}
- Source: {log_entry.source.value}
- Timestamp: {log_entry.timestamp}

**Analysis**:
- Bug Type: {bug_analysis.bug_type.value}
- Criticality: {bug_analysis.criticality.value}
- Confidence: {bug_analysis.confidence_score}

{f'**Stack Trace**:\n```\n{log_entry.stack_trace}\n```' if log_entry.stack_trace else ''}

*This issue was automatically generated with fallback template due to AI generation failure.*
""",
            labels=["bug", "automated"],
            priority=IssuePriority.MEDIUM,
            assignees=[],
            milestone=None,
            reproduction_steps=[
                "1. Check application logs for similar patterns",
                "2. Investigate the error condition",
                "3. Implement appropriate fix"
            ],
            environment_info={
                'source': log_entry.source.value,
                'component': log_entry.component,
                'timestamp': log_entry.timestamp
            },
            additional_context={'fallback_reason': 'AI generation failed'},
            source_log_id=log_entry.id,
            source_analysis_id=bug_analysis.id,
            created_by='IssueModelerAgent (Fallback)',
            created_at=datetime.now().isoformat()
        )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente.
        """
        return {
            'name': 'IssueModelerAgent',
            'version': '1.0.0',
            'description': 'Agente responsável por criar rascunhos estruturados de issues',
            'capabilities': [
                'Geração de títulos claros',
                'Criação de descrições detalhadas',
                'Formatação em Markdown',
                'Geração de labels apropriadas',
                'Definição de prioridades',
                'Criação de passos de reprodução',
                'Fallback para casos de erro'
            ],
            'input_formats': ['LogModel', 'BugAnalysis'],
            'output_format': 'IssueModel',
            'requires_llm': True
        }


# Exemplo de implementação de provedor LLM para testes
class MockLLMProvider:
    """Provedor mock para testes sem dependência externa."""
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Resposta simulada baseada no contexto
        bug_type = context.get('bug_type', 'APPLICATION_ERROR')
        criticality = context.get('criticality', 'MEDIUM')
        component = context.get('log_component', 'Application')
        message = context.get('log_message', 'Unknown error')
        
        return json.dumps({
            'title': f"Fix {bug_type.lower().replace('_', ' ')} in {component}",
            'description': f"""## Bug Report

### Summary
An error was detected in the {component} component that requires immediate attention.

### Error Details
**Message**: {message}
**Criticality**: {criticality}
**Detection Time**: {context.get('log_timestamp', 'Unknown')}

### Impact
This error may affect the normal operation of the application.

### Technical Details
{context.get('ai_reasoning', 'Automated analysis detected this as a potential issue.')}

### Stack Trace
{f"Stack trace available in logs" if context.get('has_stack_trace') else "No stack trace available"}

*This issue was automatically generated by BugFinder.*
""",
            'labels': ['bug', 'automated', criticality.lower()],
            'priority': criticality.lower() if criticality.lower() in ['low', 'medium', 'high'] else 'medium',
            'assignees': [],
            'milestone': None,
            'reproduction_steps': [
                "1. Check the application logs",
                "2. Reproduce the error conditions",
                "3. Verify the fix"
            ],
            'environment_info': {
                'component': component,
                'timestamp': context.get('log_timestamp'),
                'source': context.get('log_source')
            },
            'additional_context': context.get('technical_details', {})
        })


# Exemplo de uso e testes
if __name__ == "__main__":
    from ..models.log_model import LogModel, LogLevel, LogSource
    from ..models.bug_analysis import BugAnalysis, BugType, CriticalityLevel, AnalysisResult
    
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Cria agente com provedor mock
    mock_llm = MockLLMProvider()
    agent = IssueModelerAgent(mock_llm)
    
    # Teste: Criação de rascunho para bug crítico
    test_log = LogModel(
        timestamp="2024-01-15T10:30:45Z",
        level=LogLevel.ERROR,
        message="Database connection failed: timeout after 30 seconds",
        source=LogSource.API,
        component="DatabaseService",
        stack_trace="ConnectionError at line 42...",
        context={"connection_string": "postgres://..."}
    )
    
    test_analysis = BugAnalysis(
        log_entry_id=test_log.id,
        is_bug=True,
        bug_type=BugType.DATABASE_ERROR,
        criticality=CriticalityLevel.HIGH,
        confidence_score=0.95,
        reasoning="Database timeout indicates infrastructure problem",
        technical_details={
            'timeout_duration': '30s',
            'connection_type': 'postgresql',
            'retry_count': 3
        },
        recommended_action=AnalysisResult.CREATE_ISSUE,
        analysis_timestamp=datetime.now().isoformat(),
        analyzed_by='BugAnalyserAgent'
    )
    
    print("Teste - Criação de Rascunho:")
    draft = agent.create_issue_draft(test_log, test_analysis)
    print(f"Título: {draft.title}")
    print(f"Labels: {draft.labels}")
    print(f"Prioridade: {draft.priority}")
    print(f"Descrição (primeiros 200 chars): {draft.description[:200]}...")
    
    # Info do agente
    print(f"\nInfo do Agente:")
    print(json.dumps(agent.get_agent_info(), indent=2))