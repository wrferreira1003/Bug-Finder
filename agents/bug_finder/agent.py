#!/usr/bin/env python3
"""
Bug Finder Agent para Google ADK.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Adicionar tanto o diretório raiz quanto src ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Mudar para o diretório do projeto
os.chdir(project_root)

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

from src.agents import create_agent

# Criar o agente para o ADK
root_agent = create_agent()

# Alias para compatibilidade
agent = root_agent

# Opcional: função para obter o agente
def get_agent():
    return root_agent