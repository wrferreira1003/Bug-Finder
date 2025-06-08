#!/usr/bin/env python3
"""
Arquivo principal para execução com Google ADK.

Este é o ponto de entrada para usar o Bug Finder com o Google Agent Development Kit.
Para executar:
    adk run adk_agent         # CLI
    adk web agents/           # Interface Web
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

# Para compatibilidade com ADK, o agente deve estar disponível na raiz do módulo
agent = create_agent()

if __name__ == "__main__":
    print("🐛 Bug Finder - Use os comandos ADK para executar:")
    print("   adk run adk_agent    # CLI interativo")
    print("   adk ui adk_agent     # Interface web")