"""
Configurações gerais do sistema Bug Finder.
Define parâmetros, credenciais e configurações de comportamento.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Carrega variáveis do arquivo .env
try:
    from dotenv import load_dotenv
    
    # Procura o arquivo .env na raiz do projeto
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # src/config/settings.py -> projeto/
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Arquivo .env carregado: {env_file}")
    else:
        # Tenta carregar do diretório atual
        load_dotenv()
        print(f"⚠️  Arquivo .env não encontrado em {env_file}, usando variáveis do sistema")
        
except ImportError:
    print("⚠️  python-dotenv não instalado. Execute: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Erro ao carregar .env: {e}")


class Environment(Enum):
    """Ambientes de execução"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AIConfig:
    """Configurações do modelo de IA"""
    # Configurações do Gemini
    model_name: str = "gemini-2.0-flash"
    api_key: Optional[str] = None
    
    # Parâmetros de geração
    temperature: float = 0.3
    max_tokens: int = 4096
    top_p: float = 0.8
    top_k: int = 40
    
    # Configurações de timeout
    request_timeout: int = 60
    max_retries: int = 3
    retry_delay: int = 2
    
    def __post_init__(self):
        # Carrega API key do ambiente se não fornecida
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY é obrigatória")


@dataclass
class GitHubConfig:
    """Configurações do GitHub"""
    # Credenciais
    token: Optional[str] = None
    
    # Repositório padrão
    owner: str = ""
    repository: str = ""
    
    # Configurações de API
    api_base_url: str = "https://api.github.com"
    timeout: int = 30
    max_retries: int = 3
    
    # Configurações de issue
    default_labels: List[str] = None
    default_assignees: List[str] = None
    
    # Rate limiting
    requests_per_hour: int = 5000
    respect_rate_limits: bool = True
    
    def __post_init__(self):
        if self.default_labels is None:
            self.default_labels = ["bug", "automated"]
        if self.default_assignees is None:
            self.default_assignees = []
        
        # Carrega token do ambiente se não fornecido
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN é obrigatório")
        
        # Carrega repositório do ambiente se não fornecido
        if not self.owner:
            self.owner = os.getenv("GITHUB_OWNER", "")
        if not self.repository:
            self.repository = os.getenv("GITHUB_REPOSITORY", "")


@dataclass
class DiscordConfig:
    """Configurações do Discord"""
    # Webhook URL
    webhook_url: Optional[str] = None
    
    # Configurações de canal
    default_channel_id: str = ""
    notification_channels: Dict[str, str] = None
    
    # Configurações de menção
    mention_roles: Dict[str, List[str]] = None
    mention_users: Dict[str, List[str]] = None
    
    # Rate limiting
    requests_per_second: int = 1
    max_retries: int = 3
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = {
                "critical": os.getenv("DISCORD_CRITICAL_CHANNEL", ""),
                "high": os.getenv("DISCORD_HIGH_CHANNEL", ""),
                "general": os.getenv("DISCORD_GENERAL_CHANNEL", "")
            }
        
        if self.mention_roles is None:
            self.mention_roles = {
                "critical": os.getenv("DISCORD_CRITICAL_ROLES", "").split(","),
                "high": os.getenv("DISCORD_HIGH_ROLES", "").split(",")
            }
        
        if self.mention_users is None:
            self.mention_users = {}
        
        # Carrega webhook URL do ambiente se não fornecida
        if not self.webhook_url:
            self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL é obrigatória")


@dataclass
class ProcessConfig:
    """Configurações do processo Bug Finder"""
    # Configurações de análise
    minimum_criticality: str = "MEDIUM"
    create_issues_for_low_priority: bool = False
    auto_close_duplicates: bool = True
    
    # Configurações de revisão
    max_review_iterations: int = 3
    auto_approve_threshold: int = 4
    require_manual_approval: bool = False
    
    # Configurações de timeout
    step_timeout_seconds: int = 300  # 5 minutos
    total_timeout_seconds: int = 1800  # 30 minutos
    
    # Configurações de retry
    retry_failed_steps: bool = True
    max_retries_per_step: int = 2
    retry_delay_seconds: int = 60
    
    # Configurações de notificação
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    notify_critical_immediately: bool = True
    
    # Configurações de logging
    log_all_steps: bool = True
    log_agent_communications: bool = False
    save_process_history: bool = True


@dataclass
class DatabaseConfig:
    """Configurações do banco de dados (para futura implementação)"""
    # Configurações de conexão
    host: str = "localhost"
    port: int = 5432
    database: str = "bugfinder"
    username: str = ""
    password: str = ""
    
    # Pool de conexões
    min_connections: int = 1
    max_connections: int = 10
    
    # Configurações de timeout
    connection_timeout: int = 30
    query_timeout: int = 60
    
    def __post_init__(self):
        # Carrega credenciais do ambiente
        self.host = os.getenv("DB_HOST", self.host)
        self.port = int(os.getenv("DB_PORT", str(self.port)))
        self.database = os.getenv("DB_NAME", self.database)
        self.username = os.getenv("DB_USERNAME", self.username)
        self.password = os.getenv("DB_PASSWORD", self.password)


@dataclass
class LoggingConfig:
    """Configurações de logging"""
    # Nível de log
    level: LogLevel = LogLevel.INFO
    
    # Formato dos logs
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Arquivo de log
    log_to_file: bool = True
    log_file_path: str = "logs/bugfinder.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    # Log estruturado
    structured_logging: bool = True
    include_process_id: bool = True
    include_thread_id: bool = True
    
    def __post_init__(self):
        # Carrega configurações do ambiente
        env_level = os.getenv("LOG_LEVEL", self.level.value)
        try:
            self.level = LogLevel(env_level)
        except ValueError:
            self.level = LogLevel.INFO


class Settings:
    """Classe principal de configurações do Bug Finder"""
    
    def __init__(self, environment: Environment = Environment.PRODUCTION):
        self.environment = environment
        
        # Inicializa todas as configurações
        self.ai = AIConfig()
        self.github = GitHubConfig()
        self.discord = DiscordConfig()
        self.process = ProcessConfig()
        self.database = DatabaseConfig()
        self.logging = LoggingConfig()
        
        # Configurações específicas por ambiente
        self._apply_environment_configs()
    
    def _apply_environment_configs(self):
        """Aplica configurações específicas por ambiente"""
        if self.environment == Environment.DEVELOPMENT:
            self._apply_development_config()
        elif self.environment == Environment.STAGING:
            self._apply_staging_config()
        elif self.environment == Environment.PRODUCTION:
            self._apply_production_config()
    
    def _apply_development_config(self):
        """Configurações para desenvolvimento"""
        # IA - configurações mais flexíveis
        self.ai.temperature = 0.5
        self.ai.max_retries = 1
        
        # Processo - mais permissivo
        self.process.create_issues_for_low_priority = True
        self.process.require_manual_approval = False
        self.process.max_review_iterations = 2
        
        # Logging - mais verboso
        self.logging.level = LogLevel.DEBUG
        self.logging.log_agent_communications = True
        
        # GitHub - labels de desenvolvimento
        self.github.default_labels = ["bug", "automated", "development"]
    
    def _apply_staging_config(self):
        """Configurações para staging"""
        # Processo - configurações intermediárias
        self.process.require_manual_approval = True
        self.process.notify_critical_immediately = True
        
        # Logging - nível intermediário
        self.logging.level = LogLevel.INFO
        
        # GitHub - labels de staging
        self.github.default_labels = ["bug", "automated", "staging"]
    
    def _apply_production_config(self):
        """Configurações para produção"""
        # IA - configurações conservadoras
        self.ai.temperature = 0.3
        self.ai.max_retries = 3
        
        # Processo - configurações rigorosas
        self.process.create_issues_for_low_priority = False
        self.process.auto_approve_threshold = 4
        self.process.notify_critical_immediately = True
        
        # Logging - nível de produção
        self.logging.level = LogLevel.WARNING
        self.logging.log_agent_communications = False
        
        # GitHub - labels de produção
        self.github.default_labels = ["bug", "automated", "production"]
    
    def get_environment_name(self) -> str:
        """Retorna o nome do ambiente atual"""
        return self.environment.value
    
    def is_development(self) -> bool:
        """Verifica se está em ambiente de desenvolvimento"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Verifica se está em ambiente de produção"""
        return self.environment == Environment.PRODUCTION
    
    def validate_config(self) -> List[str]:
        """Valida todas as configurações e retorna lista de erros"""
        errors = []
        
        # Valida configurações obrigatórias
        if not self.ai.api_key:
            errors.append("GEMINI_API_KEY não configurada")
        
        if not self.github.token:
            errors.append("GITHUB_TOKEN não configurado")
        
        if not self.github.owner or not self.github.repository:
            errors.append("GitHub owner/repository não configurados")
        
        if not self.discord.webhook_url:
            errors.append("DISCORD_WEBHOOK_URL não configurada")
        
        # Valida valores numéricos
        if self.ai.temperature < 0 or self.ai.temperature > 1:
            errors.append("AI temperature deve estar entre 0 e 1")
        
        if self.process.max_review_iterations < 1:
            errors.append("max_review_iterations deve ser pelo menos 1")
        
        return errors
    
    def get_config_summary(self) -> Dict[str, str]:
        """Retorna um resumo das configurações principais"""
        return {
            "environment": self.environment.value,
            "ai_model": self.ai.model_name,
            "github_repo": f"{self.github.owner}/{self.github.repository}",
            "log_level": self.logging.level.value,
            "min_criticality": self.process.minimum_criticality,
            "max_review_iterations": str(self.process.max_review_iterations)
        }


# Instância global de configurações
def get_settings(environment: Optional[Environment] = None) -> Settings:
    """
    Retorna instância de configurações.
    Se environment não for especificado, detecta do ambiente.
    """
    if environment is None:
        env_name = os.getenv("ENVIRONMENT", "production").lower()
        try:
            environment = Environment(env_name)
        except ValueError:
            environment = Environment.PRODUCTION
    
    return Settings(environment)


# Configurações padrão para importação direta
settings = get_settings()