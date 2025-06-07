"""
Módulo de configurações do Bug Finder.
Centraliza todas as configurações e prompts do sistema.
"""

# Configurações principais
from .settings import (
    Environment,
    LogLevel,
    AIConfig,
    GitHubConfig,
    DiscordConfig,
    ProcessConfig,
    DatabaseConfig,
    LoggingConfig,
    Settings,
    get_settings,
    settings
)

# Prompts dos agentes
from .prompts import (
    BugAnalyserPrompts,
    IssueDrafterPrompts,
    IssueReviewerPrompts,
    IssueRefinerPrompts,
    BugFinderPrompts,
    NotificationPrompts,
    PromptManager,
    prompt_manager,
    get_system_prompt,
    get_task_prompt,
    format_analysis_prompt,
    format_draft_prompt,
    format_review_prompt,
    format_refinement_prompt,
    format_notification_prompt
)

# Lista de todas as classes e funções exportadas
__all__ = [
    # Settings
    "Environment",
    "LogLevel", 
    "AIConfig",
    "GitHubConfig",
    "DiscordConfig",
    "ProcessConfig",
    "DatabaseConfig",
    "LoggingConfig",
    "Settings",
    "get_settings",
    "settings",
    
    # Prompts
    "BugAnalyserPrompts",
    "IssueDrafterPrompts", 
    "IssueReviewerPrompts",
    "IssueRefinerPrompts",
    "BugFinderPrompts",
    "NotificationPrompts",
    "PromptManager",
    "prompt_manager",
    "get_system_prompt",
    "get_task_prompt",
    "format_analysis_prompt",
    "format_draft_prompt", 
    "format_review_prompt",
    "format_refinement_prompt",
    "format_notification_prompt"
]

# Versão do módulo
__version__ = "1.0.0"

# Configurações globais para fácil acesso
def get_current_config() -> Settings:
    """Retorna as configurações atuais do sistema"""
    return settings

def validate_environment() -> bool:
    """Valida se o ambiente está configurado corretamente"""
    errors = settings.validate_config()
    if errors:
        for error in errors:
            print(f"❌ Erro de configuração: {error}")
        return False
    return True

def print_config_summary():
    """Imprime um resumo das configurações atuais"""
    config_summary = settings.get_config_summary()
    print("🔧 Configurações do Bug Finder:")
    print("=" * 40)
    for key, value in config_summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("=" * 40)