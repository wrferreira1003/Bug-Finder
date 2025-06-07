#!/usr/bin/env python3
"""
Bug Finder - Sistema automatizado para análise de bugs e criação de issues

Este é o ponto de entrada principal do sistema Bug Finder.
Use os comandos do ADK para executar:

    adk run main         # Executar via CLI
    adk ui main          # Abrir interface web
"""

import os
import sys
import logging
from pathlib import Path

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import get_settings
from src.agents import BugFinderSystem, create_agent


def setup_logging():
    """Configura o sistema de logging."""
    settings = get_settings()
    
    # Configurar formato de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configurar nível
    log_level = getattr(logging, settings.log_level.value)
    
    # Configurar logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Adicionar handler de arquivo se especificado
    if settings.log_file_path:
        file_handler = logging.FileHandler(settings.log_file_path)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)


def validate_environment():
    """Valida se o ambiente está configurado corretamente."""
    settings = get_settings()
    errors = settings.validate_required_settings()
    
    if errors:
        print("❌ Configuração inválida:")
        for error in errors:
            print(f"  - {error}")
        print("\n💡 Verifique o arquivo .env e configure as variáveis necessárias.")
        print("   Use .env.example como referência.")
        return False
    
    return True


def main():
    """Função principal do sistema Bug Finder."""
    print("🐛 Bug Finder System - Inicializando...")
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validar ambiente
        if not validate_environment():
            sys.exit(1)
        
        # Criar sistema Bug Finder
        bug_finder = BugFinderSystem()
        
        # Testar integrações na inicialização
        logger.info("Testing system integrations...")
        test_results = bug_finder.test_integrations()
        
        failed_tests = [name for name, result in test_results.items() 
                       if result.get("status") != "success" and name != "overall"]
        
        if failed_tests:
            logger.warning(f"Some integrations failed: {', '.join(failed_tests)}")
            print(f"⚠️  Algumas integrações falharam: {', '.join(failed_tests)}")
            print("   O sistema pode funcionar com funcionalidade limitada.")
        else:
            logger.info("All integrations working correctly")
            print("✅ Todas as integrações funcionando corretamente!")
        
        # Mostrar status do sistema
        status = bug_finder.get_system_status()
        print(f"\n📊 Sistema Bug Finder {status['system_info']['version']} iniciado")
        print(f"🏗️  Ambiente: {status['system_info']['environment']}")
        print(f"🔗 GitHub: {status['integrations']['github']['repository']}")
        print(f"🤖 Modelo AI: {status['integrations']['ai']['model']}")
        
        return bug_finder
        
    except Exception as e:
        logger.error(f"Failed to initialize Bug Finder: {e}")
        print(f"❌ Erro na inicialização: {e}")
        sys.exit(1)


# Para uso com ADK
def create_agent():
    """Cria e retorna uma instância do agente para o ADK."""
    return main()


if __name__ == "__main__":
    # Modo standalone - não ADK
    print("🚀 Executando Bug Finder em modo standalone...")
    print("💡 Para usar a interface web ADK, execute: adk ui main")
    print("💡 Para usar o CLI ADK, execute: adk run main")
    
    bug_finder = main()
    
    # Exemplo de uso direto
    print("\n🧪 Exemplo de análise de log:")
    sample_log = """
    ERROR 2024-01-20 10:30:45 - app.py:142 - Database connection failed
    Traceback (most recent call last):
      File "app.py", line 142, in connect_db
        connection = psycopg2.connect(DATABASE_URL)
    psycopg2.OperationalError: could not connect to server
    """
    
    result = bug_finder.analyze_sample_log(sample_log.strip())
    
    if result["status"] == "success":
        analysis = result["analysis"]
        print(f"✅ Log analisado:")
        print(f"   - É bug: {analysis['is_bug']}")
        print(f"   - Severidade: {analysis['severity']}")
        print(f"   - Categoria: {analysis['category']}")
        print(f"   - Confiança: {analysis['confidence']:.2f}")
        print(f"   - Decisão: {analysis['decision']}")
    else:
        print(f"❌ Erro na análise: {result['message']}")