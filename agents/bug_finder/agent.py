#!/usr/bin/env python3
"""
Bug Finder Agent para Google ADK.
"""

import sys
import os
from pathlib import Path

# Adicionar tanto o diretório raiz quanto src ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Mudar para o diretório do projeto
os.chdir(project_root)

from src.agents import create_agent

# Criar o agente para o ADK
root_agent = create_agent()

# Alias para compatibilidade
agent = root_agent

# Opcional: função para obter o agente
def get_agent():
    return root_agent