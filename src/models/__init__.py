"""
Módulo de modelos de dados do Bug Finder.

Este módulo contém todas as estruturas de dados que os agentes
usam para se comunicar e representar informações no sistema.

Importações disponíveis:
- LogModel, LogLevel: Para representar logs de erro
- BugAnalysis, BugSeverity, BugCategory: Para análises de bugs  
- IssueModel, IssueStatus, IssuePriority: Para issues do GitHub
"""

# Importações dos modelos principais
from .log_model import (
    LogModel,
    LogLevel,
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
    IssueStatus, 
    IssuePriority,
    create_basic_issue,
    create_issue_from_analysis
)

# Lista de exportações públicas
__all__ = [
    # Log Model
    'LogModel',
    'LogLevel', 
    'create_log_from_text',
    'is_log_worth_analyzing',
    
    # Bug Analysis
    'BugAnalysis',
    'BugSeverity',
    'BugCategory',
    'create_negative_analysis', 
    'create_quick_bug_analysis',
    
    # Issue Model
    'IssueModel',
    'IssueStatus',
    'IssuePriority',
    'create_basic_issue',
    'create_issue_from_analysis'
]

# Versão do módulo de modelos
__version__ = "1.0.0"