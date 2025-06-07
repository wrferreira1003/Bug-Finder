#!/usr/bin/env python3
"""
Arquivo principal para execução com Google ADK.

Este é o ponto de entrada para usar o Bug Finder com o Google Agent Development Kit.
Para executar:
    adk run adk_agent         # CLI
    adk ui adk_agent          # Interface Web
"""

import os
import sys
from pathlib import Path

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents import create_agent

# Para compatibilidade com ADK, o agente deve estar disponível na raiz do módulo
agent = create_agent()

if __name__ == "__main__":
    print("🐛 Bug Finder - Use os comandos ADK para executar:")
    print("   adk run adk_agent    # CLI interativo")
    print("   adk ui adk_agent     # Interface web")