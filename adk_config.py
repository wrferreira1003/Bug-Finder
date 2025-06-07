"""
Configuração do Google AI Agent Development Kit (ADK) para o Bug Finder.

Este arquivo define como o ADK deve carregar e executar o sistema Bug Finder.
"""

from src.agents import create_agent

# Configuração principal do ADK
agent = create_agent()

# Metadata do agente para o ADK
metadata = {
    "name": "Bug Finder System",
    "description": "Sistema automatizado para análise de bugs e criação de issues no GitHub",
    "version": "1.0.0",
    "author": "Bug Finder Team",
    "tags": ["bug-analysis", "automation", "github", "ai"],
    "capabilities": [
        "Log analysis",
        "Bug detection", 
        "Issue creation",
        "GitHub integration",
        "Discord notifications"
    ]
}

# Configurações do ambiente ADK
adk_config = {
    "agent": agent,
    "metadata": metadata,
    "ui_config": {
        "title": "🐛 Bug Finder System",
        "description": "Analise logs, detecte bugs e crie issues automaticamente",
        "theme": "dark",
        "show_tools": True,
        "show_history": True
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}