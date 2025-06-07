
"""
BugAnalyserAgent - Agente Analisador de Bugs

Localização: src/agents/bug_analyser_agent.py

Responsabilidades:
- Analisar logs estruturados para determinar se são bugs
- Classificar a criticidade dos problemas encontrados
- Determinar se o processo deve continuar ou parar
- Extrair informações técnicas relevantes

Este agente atua como um "detetive", investigando logs para 
identificar problemas que requerem atenção da equipe de desenvolvimento.
"""

import json
import logging
from typing import Dict, Any, Optional, Protocol
from datetime import datetime

from ..models.log_model import LogModel, LogLevel
from ..models.bug_analysis import BugAnalysis, BugSeverity, BugCategory
from ..config.prompts import BugAnalyserPrompts
from ..config.settings import get_settings


# Interface para provedor de modelo de linguagem
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

class BugAnalyserAgent:
    """
    Agente responsável por analisar logs e identificar bugs críticos.
    
    Este agente usa IA para interpretar logs e determinar:
    - Se o log representa um bug real
    - Qual a criticidade do problema
    - Que informações técnicas são relevantes
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Inicializa o agente analisador de bugs.
        
        Args:
            llm_provider: Provedor do modelo de linguagem a ser usado
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.prompts = BugAnalyserPrompts()
        
    def analyze_log(self, log_entry: LogModel) -> BugAnalysis:
        """
        Analisa um log para determinar se é um bug e sua criticidade.
        
        Args:
            log_entry: LogModel estruturado para análise
            
        Returns:
            Análise completa do bug com classificação e recomendações
        """
        try:
            self.logger.info(f"Iniciando análise do log: {log_entry.message[:50]}...")
            
            # Preparação do contexto para análise
            analysis_context = self._prepare_analysis_context(log_entry)
            
            # Análise principal usando IA
            analysis_result = self._perform_ai_analysis(log_entry, analysis_context)
            
            # Validação e refinamento da análise
            validated_result = self._validate_analysis(analysis_result, log_entry)
            
            # Criação do objeto de análise final
            bug_analysis = self._create_bug_analysis(log_entry, validated_result)
            
            self.logger.info(f"Análise concluída. Categoria: {bug_analysis.category}, Severidade: {bug_analysis.severity}")
            
            return bug_analysis
            
        except Exception as e:
            self.logger.error(f"Erro durante análise do log: {str(e)}")
            # Retorna análise de fallback em caso de erro
            return self._create_fallback_analysis(log_entry)
    
    def _prepare_analysis_context(self, log_entry: LogModel) -> Dict[str, Any]:
        """
        Prepara contexto adicional para análise baseado no log.
        """
        context = {
            'log_level': log_entry.level.value,
            'service_name': log_entry.service_name or 'unknown',
            'has_stack_trace': bool(log_entry.stack_trace),
            'message_length': len(log_entry.message),
            'environment': log_entry.environment or 'unknown',
            'timestamp': log_entry.timestamp,
        }
        
        # Adiciona contexto de padrões conhecidos
        context.update(self._identify_known_patterns(log_entry))
        
        return context
    
    # Identifica padrões conhecidos no log que ajudam na análise.
    def _identify_known_patterns(self, log_entry: LogModel) -> Dict[str, Any]:
        """
        Identifica padrões conhecidos no log que ajudam na análise.
        """
        message = log_entry.message.lower()
        patterns = {
            'has_exception': any(word in message for word in [
                'exception', 'error', 'failed', 'failure', 'crash', 'fatal'
            ]),
            'has_connection_issue': any(word in message for word in [
                'connection', 'timeout', 'network', 'socket', 'refused'
            ]),
            'has_authentication_issue': any(word in message for word in [
                'authentication', 'authorization', 'token', 'unauthorized', 'forbidden'
            ]),
            'has_database_issue': any(word in message for word in [
                'database', 'sql', 'query', 'transaction', 'deadlock'
            ]),
            'has_memory_issue': any(word in message for word in [
                'memory', 'heap', 'out of space', 'allocation', 'leak'
            ]),
            'has_performance_issue': any(word in message for word in [
                'slow', 'performance', 'latency', 'timeout', 'bottleneck'
            ])
        }
        
        return patterns
    
    # Realiza a análise principal usando o modelo de IA.
    def _perform_ai_analysis(self, log_entry: LogModel, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza a análise principal usando o modelo de IA.
        """
        # Constrói o prompt para análise
        analysis_prompt = self.prompts.get_bug_analysis_prompt(log_entry, context)
        
        # Gera resposta do modelo
        ai_response = self.llm_provider.generate_response(analysis_prompt, context)
        
        # Faz parsing da resposta JSON
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            self.logger.warning("Resposta da IA não é JSON válido, tentando parsing alternativo")
            return self._parse_alternative_response(ai_response)
    
    def _parse_alternative_response(self, response: str) -> Dict[str, Any]:
        """
        Faz parsing alternativo caso a resposta não seja JSON válido.
        """
        # Implementação básica de fallback
        lines = response.strip().split('\n')
        result = {
            'is_bug': False,
            'bug_type': 'UNKNOWN',
            'criticality': 'LOW',
            'confidence': 0.5,
            'reasoning': response,
            'technical_details': {},
            'recommended_action': 'MONITOR'
        }
        
        # Busca por indicadores na resposta
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['yes', 'true', 'is a bug', 'critical', 'error']):
            result['is_bug'] = True
            
        if any(word in response_lower for word in ['critical', 'high', 'severe']):
            result['criticality'] = 'HIGH'
        elif any(word in response_lower for word in ['medium', 'moderate']):
            result['criticality'] = 'MEDIUM'
            
        return result
    
    def _validate_analysis(self, analysis_result: Dict[str, Any], log_entry: LogModel) -> Dict[str, Any]:
        """
        Valida e ajusta a análise baseada em regras de negócio.
        """
        validated = analysis_result.copy()
        
        # Validação baseada no nível do log
        if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.FATAL]:
            # Logs de erro sempre devem ser considerados como potenciais bugs
            if not validated.get('is_bug', False):
                validated['is_bug'] = True
                validated['reasoning'] += " (Ajustado: logs de ERROR/CRITICAL são sempre considerados bugs)"
        
        # Validação de criticidade baseada em padrões
        if log_entry.level == LogLevel.CRITICAL or log_entry.level == LogLevel.FATAL:
            if validated.get('criticality', 'LOW') != 'HIGH':
                validated['criticality'] = 'HIGH'
                validated['reasoning'] += " (Ajustado: logs CRITICAL/FATAL têm criticidade HIGH)"
        
        # Garantir campos obrigatórios
        validated.setdefault('confidence', 0.7)
        validated.setdefault('technical_details', {})
        validated.setdefault('recommended_action', 'CREATE_ISSUE')
        
        # Validar faixa de confiança
        confidence = validated.get('confidence', 0.5)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            validated['confidence'] = 0.5
        
        return validated
    
    def _create_bug_analysis(self, log_entry: LogModel, analysis_result: Dict[str, Any]) -> BugAnalysis:
        """
        Cria objeto BugAnalysis a partir dos resultados da análise.
        """
        # Converte strings para enums
        try:
            bug_type = BugType[analysis_result.get('bug_type', 'UNKNOWN').upper()]
        except KeyError:
            bug_type = BugType.UNKNOWN
            
        try:
            criticality = CriticalityLevel[analysis_result.get('criticality', 'LOW').upper()]
        except KeyError:
            criticality = CriticalityLevel.LOW
            
        try:
            recommended_action = AnalysisResult[analysis_result.get('recommended_action', 'MONITOR').upper()]
        except KeyError:
            recommended_action = AnalysisResult.MONITOR
        
        return BugAnalysis(
            log_entry_id=log_entry.id,
            is_bug=analysis_result.get('is_bug', False),
            bug_type=bug_type,
            criticality=criticality,
            confidence_score=analysis_result.get('confidence', 0.5),
            reasoning=analysis_result.get('reasoning', ''),
            technical_details=analysis_result.get('technical_details', {}),
            recommended_action=recommended_action,
            analysis_timestamp=datetime.now().isoformat(),
            analyzed_by='BugAnalyserAgent'
        )
    
    def _create_fallback_analysis(self, log_entry: LogModel) -> BugAnalysis:
        """
        Cria análise de fallback em caso de erro na análise principal.
        """
        # Análise conservadora baseada apenas no nível do log
        is_bug = log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.FATAL]
        
        if log_entry.level == LogLevel.CRITICAL or log_entry.level == LogLevel.FATAL:
            criticality = CriticalityLevel.HIGH
        elif log_entry.level == LogLevel.ERROR:
            criticality = CriticalityLevel.MEDIUM
        else:
            criticality = CriticalityLevel.LOW
        
        return BugAnalysis(
            log_entry_id=log_entry.id,
            is_bug=is_bug,
            bug_type=BugType.UNKNOWN,
            criticality=criticality,
            confidence_score=0.3,  # Baixa confiança para fallback
            reasoning="Análise de fallback baseada apenas no nível do log devido a erro na análise principal",
            technical_details={'fallback_reason': 'AI analysis failed'},
            recommended_action=AnalysisResult.CREATE_ISSUE if is_bug else AnalysisResult.MONITOR,
            analysis_timestamp=datetime.now().isoformat(),
            analyzed_by='BugAnalyserAgent (Fallback)'
        )
    
    def should_continue_processing(self, analysis: BugAnalysis) -> bool:
        """
        Determina se o processamento deve continuar baseado na análise.
        
        Args:
            analysis: Resultado da análise do bug
            
        Returns:
            True se deve continuar processamento, False caso contrário
        """
        # Continua se é um bug confirmado
        if analysis.is_bug:
            return True
        
        # Continua se tem alta confiança mas baixa criticidade (para monitoramento)
        if analysis.confidence_score > 0.8 and analysis.criticality != CriticalityLevel.LOW:
            return True
        
        # Para todos os outros casos
        return False
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente.
        """
        return {
            'name': 'BugAnalyserAgent',
            'version': '1.0.0',
            'description': 'Agente responsável por analisar logs e identificar bugs críticos',
            'capabilities': [
                'Análise de logs usando IA',
                'Classificação de tipos de bug',
                'Determinação de criticidade',
                'Identificação de padrões conhecidos',
                'Validação de análises',
                'Fallback para casos de erro'
            ],
            'input_format': 'LogModel',
            'output_format': 'BugAnalysis',
            'requires_llm': True
        }


# Exemplo de implementação de provedor LLM para testes
class MockLLMProvider:
    """Provedor mock para testes sem dependência externa."""
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Resposta simulada baseada no contexto
        if context and context.get('log_level') in ['ERROR', 'CRITICAL', 'FATAL']:
            return json.dumps({
                'is_bug': True,
                'bug_type': 'APPLICATION_ERROR',
                'criticality': 'HIGH',
                'confidence': 0.9,
                'reasoning': 'Log de nível ERROR indica problema na aplicação',
                'technical_details': {
                    'category': 'runtime_error',
                    'affected_component': context.get('component', 'unknown')
                },
                'recommended_action': 'CREATE_ISSUE'
            })
        else:
            return json.dumps({
                'is_bug': False,
                'bug_type': 'INFO',
                'criticality': 'LOW',
                'confidence': 0.8,
                'reasoning': 'Log informativo, não indica problema',
                'technical_details': {},
                'recommended_action': 'MONITOR'
            })


# Exemplo de uso e testes
if __name__ == "__main__":
    from ..models.log_model import LogModel, LogLevel, LogSource
    
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Cria agente com provedor mock
    mock_llm = MockLLMProvider()
    agent = BugAnalyserAgent(mock_llm)
    
    # Teste 1: Log de erro crítico
    error_log = LogModel(
        timestamp="2024-01-15T10:30:45Z",
        level=LogLevel.ERROR,
        message="Falha na conexão com banco de dados",
        source=LogSource.API,
        component="DatabaseService",
        stack_trace="ConnectionError at line 42...",
        context={"connection_string": "postgres://..."}
    )
    
    print("Teste 1 - Log de Erro:")
    analysis1 = agent.analyze_log(error_log)
    print(f"É bug: {analysis1.is_bug}")
    print(f"Criticidade: {analysis1.criticality}")
    print(f"Deve continuar: {agent.should_continue_processing(analysis1)}")
    
    # Teste 2: Log informativo
    info_log = LogModel(
        timestamp="2024-01-15T10:30:45Z",
        level=LogLevel.INFO,
        message="Usuário logado com sucesso",
        source=LogSource.WEB,
        component="AuthService"
    )
    
    print("\nTeste 2 - Log Informativo:")
    analysis2 = agent.analyze_log(info_log)
    print(f"É bug: {analysis2.is_bug}")
    print(f"Criticidade: {analysis2.criticality}")
    print(f"Deve continuar: {agent.should_continue_processing(analysis2)}")
    
    # Info do agente
    print(f"\nInfo do Agente:")
    print(json.dumps(agent.get_agent_info(), indent=2))