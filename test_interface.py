#!/usr/bin/env python3
"""
Script para testar rapidamente o Bug Finder com logs de exemplo.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Logs de exemplo simples para a interface
SIMPLE_LOGS = [
    "ERROR: Database connection failed - psycopg2.OperationalError",
    "ERROR: Authentication failed - Invalid JWT token", 
    "ERROR: Payment API timeout - HTTPTimeoutError",
    "WARNING: Form validation failed - Invalid email format",
    "CRITICAL: Disk space low - Only 2GB remaining",
    "INFO: User login successful - alice@company.com"
]

print("🧪 LOGS SIMPLES PARA TESTAR NA INTERFACE WEB")
print("=" * 60)
print("Cole estes logs na interface: http://localhost:8000")
print("=" * 60)

for i, log in enumerate(SIMPLE_LOGS, 1):
    print(f"\n{i}. {log}")

print("\n" + "=" * 60)
print("💡 DICA: Use o log #1 ou #5 para ver bugs críticos sendo detectados!")
print("💡 Use o log #6 para ver como logs informativos são ignorados.")
print("=" * 60)