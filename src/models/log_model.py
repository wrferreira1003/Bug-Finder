"""
Modelo que representa um log de erro recebido pelo sistema.

Este modelo padroniza como os logs são estruturados internamente,
independentemente de como chegam ao sistema (texto, JSON, etc.).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class LogLevel(Enum):
    """
    Níveis de log suportados pelo sistema.
    
    Isso nos ajuda a classificar a importância do log de forma padronizada.
    """
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"

@dataclass
class LogModel:
    """
    Representa um log estruturado no sistema Bug Finder.
    
    Esta classe define exatamente quais informações esperamos
    de qualquer log que entra no sistema, criando uma linguagem
    comum entre todos os agentes.
    
    Attributes:
        raw_content (str): O conteúdo original do log, exatamente como recebido
        timestamp (datetime): Quando o erro aconteceu
        level (LogLevel): Nível de importância do log (error, warning, etc.)
        message (str): Mensagem principal do erro
        service_name (Optional[str]): Nome do serviço que gerou o log
        environment (Optional[str]): Ambiente onde aconteceu (dev, staging, prod)
        stack_trace (Optional[str]): Stack trace completo do erro (se houver)
        user_id (Optional[str]): ID do usuário afetado (se aplicável)
        request_id (Optional[str]): ID da requisição que causou o erro
        additional_data (Dict[str, Any]): Qualquer informação extra
    """
    # Campos obrigatórios - todo log deve ter isso
    raw_content: str
    timestamp: datetime
    level: LogLevel
    message: str

    # Campos opcionais - podem estar presentes ou não
    service_name: Optional[str] = None
    environment: Optional[str] = None
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    # ID único para o log
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """
        Método especial que é executado após a criação do objeto.
        
        Aqui fazemos validações e ajustes nos dados para garantir
        que o log está em um formato consistente.
        """
        # Se additional_data for None, inicializa como dicionário vazio
        if self.additional_data is None:
            self.additional_data = {}
            
        # Limpa espaços em branco desnecessários da mensagem
        self.message = self.message.strip()
        
        # Garante que o raw_content não está vazio
        if not self.raw_content:
            raise ValueError("raw_content não pode estar vazio")
        

    @property
    def is_error(self) -> bool:
        """
        Verifica se este log representa um erro (não apenas um warning ou info).
        
        Returns:
            bool: True se o log é de nível ERROR, CRITICAL ou FATAL
        """
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.FATAL]
    
    @property
    def is_critical(self) -> bool:
        """
        Verifica se este log representa um erro crítico que precisa atenção imediata.
        
        Returns:
            bool: True se o log é CRITICAL ou FATAL
        """
        return self.level in [LogLevel.CRITICAL, LogLevel.FATAL]
    
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o log para um dicionário Python.
        
        Útil para serialização (salvar em arquivo, enviar via API, etc.).
        
        Returns:
            Dict[str, Any]: Representação em dicionário do log
        """
        return {
            'raw_content': self.raw_content,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'service_name': self.service_name,
            'environment': self.environment,
            'stack_trace': self.stack_trace,
            'user_id': self.user_id,
            'request_id': self.request_id,
            'additional_data': self.additional_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogModel':
        """
        Cria um LogModel a partir de um dicionário.
        
        Útil para deserialização (ler de arquivo, receber via API, etc.).
        
        Args:
            data (Dict[str, Any]): Dicionário com os dados do log
            
        Returns:
            LogModel: Nova instância criada a partir dos dados
        """
        return cls(
            raw_content=data['raw_content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            level=LogLevel(data['level']),
            message=data['message'],
            service_name=data.get('service_name'),
            environment=data.get('environment'),
            stack_trace=data.get('stack_trace'),
            user_id=data.get('user_id'),
            request_id=data.get('request_id'),
            additional_data=data.get('additional_data', {})
        )
    
    def __str__(self) -> str:
        """
        Representação em string legível do log.
        
        Útil para debug e logging interno do sistema.
        """
        return f"LogModel({self.level.value.upper()}: {self.message[:50]}...)"
    
    def __repr__(self) -> str:
        """
        Representação técnica detalhada do log.
        
        Útil para desenvolvimento e debugging.
        """
        return (f"LogModel(level={self.level.value}, message='{self.message}', "
                f"service={self.service_name}, env={self.environment})")


# Funções utilitárias para trabalhar com logs
def create_log_from_text(raw_text: str, 
                        timestamp: Optional[datetime] = None,
                        service_name: Optional[str] = None) -> LogModel:
    """
    Função helper para criar um LogModel a partir de texto simples.
    
    Esta função usa heurísticas simples para tentar extrair informações
    do texto e criar um log estruturado.
    
    Args:
        raw_text (str): Texto bruto do log
        timestamp (Optional[datetime]): Timestamp do log (usa agora se None)
        service_name (Optional[str]): Nome do serviço que gerou o log
        
    Returns:
        LogModel: Log estruturado criado a partir do texto
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Heurísticas simples para detectar o nível do log
    text_lower = raw_text.lower()
    
    if any(word in text_lower for word in ['fatal', 'panic']):
        level = LogLevel.FATAL
    elif any(word in text_lower for word in ['critical', 'crit']):
        level = LogLevel.CRITICAL
    elif any(word in text_lower for word in ['error', 'err', 'exception', 'failed']):
        level = LogLevel.ERROR
    elif any(word in text_lower for word in ['warning', 'warn']):
        level = LogLevel.WARNING
    elif any(word in text_lower for word in ['debug']):
        level = LogLevel.DEBUG
    else:
        level = LogLevel.INFO
    
    # Extrai a primeira linha como mensagem (ou primeiros 200 caracteres)
    lines = raw_text.strip().split('\n')
    message = lines[0] if lines else raw_text
    if len(message) > 200:
        message = message[:200] + "..."
    
    # Se há múltiplas linhas, considera o resto como stack trace
    stack_trace = None
    if len(lines) > 1:
        stack_trace = '\n'.join(lines[1:])
    
    return LogModel(
        raw_content=raw_text,
        timestamp=timestamp,
        level=level,
        message=message,
        service_name=service_name,
        stack_trace=stack_trace
    )


# Função utilitária para determinar se um log vale a pena ser analisado
def is_log_worth_analyzing(log: LogModel) -> bool:
    """
    Determina se um log vale a pena ser analisado pelos agentes.
    
    Esta é uma primeira triagem rápida antes de chamar o agente
    de análise, economizando recursos computacionais.
    
    Args:
        log (LogModel): Log a ser verificado
        
    Returns:
        bool: True se o log deve ser analisado
    """
    # Só analisa logs de erro ou críticos
    if not log.is_error:
        return False
    
    # Ignora logs muito antigos (mais de 24 horas)
    hours_old = (datetime.now() - log.timestamp).total_seconds() / 3600
    if hours_old > 24:
        return False
    
    # Ignora mensagens muito curtas (provavelmente não são úteis)
    if len(log.message.strip()) < 10:
        return False
    
    return True