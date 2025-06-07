"""
Módulo de modelos de dados do Bug Finder.
Centraliza todas as estruturas de dados utilizadas pelos agentes.
"""

# Modelos básicos
from .log_model import (
    LogLevel,
    LogModel,
    create_log_from_text,
    is_log_worth_analyzing
)

from .bug_analysis import (
    BugAnalysis,
    BugSeverity,
    BugCategory,
    create_negative_analysis,
    create_quick_bug_analysis
)

from .issue_model import (
    IssueModel,
    IssuePriority,
    IssueStatus,
    create_basic_issue,
    create_issue_from_analysis
)

# Modelos de processo
from .review_model import (
    ReviewStatus,
    ReviewCriteria,
    ReviewFeedback,
    IssueReview,
    ReviewMetrics
)

from .creation_model import (
    CreationStatus,
    IssueState,
    GitHubIssueData,
    CreationAttempt,
    IssueCreationResult,
    CreationConfig,
    CreationMetrics
)

from .notification_model import (
    NotificationStatus,
    NotificationType,
    NotificationPriority,
    DiscordEmbed,
    DiscordMessage,
    NotificationAttempt,
    NotificationResult,
    NotificationTemplate,
    NotificationConfig,
    NotificationMetrics
)

from .process_model import (
    ProcessStatus,
    ProcessResult,
    ProcessStep,
    ProcessContext,
    BugFinderProcess,
    ProcessConfig,
    ProcessMetrics
)

# Lista de todas as classes exportadas
__all__ = [
    # Modelos básicos
    "LogLevel",
    "LogModel",
    "create_log_from_text",
    "is_log_worth_analyzing",
    "BugAnalysis",
    "BugSeverity",
    "BugCategory", 
    "create_negative_analysis",
    "create_quick_bug_analysis",
    "IssueModel",
    "IssuePriority", 
    "IssueStatus",
    "create_basic_issue",
    "create_issue_from_analysis",
    
    # Modelos de processo
    "ReviewStatus",
    "ReviewCriteria",
    "ReviewFeedback",
    "IssueReview",
    "ReviewMetrics",
    "CreationStatus",
    "IssueState",
    "GitHubIssueData",
    "CreationAttempt", 
    "IssueCreationResult",
    "CreationConfig",
    "CreationMetrics",
    "NotificationStatus",
    "NotificationType",
    "NotificationPriority",
    "DiscordEmbed",
    "DiscordMessage",
    "NotificationAttempt",
    "NotificationResult",
    "NotificationTemplate",
    "NotificationConfig", 
    "NotificationMetrics",
    "ProcessStatus",
    "ProcessResult",
    "ProcessStep",
    "ProcessContext",
    "BugFinderProcess",
    "ProcessConfig",
    "ProcessMetrics"
]

# Versão do módulo
__version__ = "1.0.0"