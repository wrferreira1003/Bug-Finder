"""
Configuração do Google AI Agent Development Kit (ADK) para o Bug Finder.

Este arquivo define como o ADK deve carregar e executar o sistema Bug Finder.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env ANTES de qualquer import
load_dotenv()

# Verificar se a API key foi carregada corretamente
google_api_key = os.getenv('GOOGLE_AI_API_KEY')
if not google_api_key:
    raise ValueError("GOOGLE_AI_API_KEY not found! Make sure .env file exists and contains the API key.")

# Garantir que a API key esteja disponível em todas as variáveis possíveis
os.environ['GOOGLE_AI_API_KEY'] = google_api_key
os.environ['GOOGLE_API_KEY'] = google_api_key  # ADK pode usar esta variante
os.environ['GENAI_API_KEY'] = google_api_key   # Outra variante possível

# Configurar o Google AI imediatamente
import google.generativeai as genai
genai.configure(api_key=google_api_key)

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

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