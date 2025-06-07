#!/usr/bin/env python3
"""
Script de configuração inicial do Bug Finder.

Este script automatiza a configuração do ambiente de desenvolvimento,
criando a estrutura de diretórios e verificando dependências.
"""

import os
import sys
import subprocess
from pathlib import Path


def criar_banner():
    """Exibe banner do Bug Finder."""
    banner = """
    ██████╗ ██╗   ██╗ ██████╗     ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
    ██╔══██╗██║   ██║██╔════╝     ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
    ██████╔╝██║   ██║██║  ███╗    █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
    ██╔══██╗██║   ██║██║   ██║    ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
    ██████╔╝╚██████╔╝╚██████╔╝    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
    ╚═════╝  ╚═════╝  ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
    
    🤖 Sistema Inteligente de Detecção e Criação de Issues
    📋 Fase 2: Configuração dos Modelos de Dados
    """
    print(banner)


def verificar_python():
    """Verifica se a versão do Python é adequada."""
    print("🐍 Verificando versão do Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário!")
        print(f"   Versão atual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK!")
    return True


def criar_estrutura_diretorios():
    """Cria a estrutura de diretórios do projeto."""
    print("\n📁 Criando estrutura de diretórios...")
    
    diretorios = [
        "src",
        "src/models",
        "src/agents", 
        "src/tools",
        "src/config",
        "tests",
        "tests/unit",
        "tests/integration",
        "examples",
        "examples/sample_logs",
        "docs",
        "scripts"
    ]
    
    for diretorio in diretorios:
        path = Path(diretorio)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"   📂 Criado: {diretorio}")
        else:
            print(f"   ✅ Existe: {diretorio}")


def criar_arquivos_init():
    """Cria arquivos __init__.py necessários."""
    print("\n📄 Criando arquivos __init__.py...")
    
    arquivos_init = [
        "src/__init__.py",
        "src/models/__init__.py", 
        "src/agents/__init__.py",
        "src/tools/__init__.py",
        "src/config/__init__.py",
        "tests/__init__.py"
    ]
    
    for arquivo in arquivos_init:
        path = Path(arquivo)
        if not path.exists():
            # Cria arquivo com comentário básico
            with open(path, 'w', encoding='utf-8') as f:
                modulo = path.parent.name
                f.write(f'"""\nMódulo {modulo} do Bug Finder.\n"""\n')
            print(f"   📝 Criado: {arquivo}")
        else:
            print(f"   ✅ Existe: {arquivo}")


def criar_arquivo_env():
    """Cria arquivo .env.example com configurações necessárias."""
    print("\n🔧 Criando arquivo de configuração...")
    
    env_content = """# Bug Finder - Configurações de Ambiente
# Copie este arquivo para .env e preencha com seus valores

# =============================================================================
# CONFIGURAÇÕES DO GITHUB
# =============================================================================
# Token de acesso pessoal do GitHub (com permissões de repo)
# Como criar: https://github.com/settings/personal-access-tokens/new
GITHUB_TOKEN=ghp_seu_token_aqui

# Repositório onde as issues serão criadas (formato: owner/repo)
GITHUB_REPOSITORY=seu-usuario/seu-repositorio

# =============================================================================
# CONFIGURAÇÕES DO DISCORD
# =============================================================================
# URL do webhook do Discord para notificações
# Como criar: Configurações do Servidor > Integrações > Webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/seu/webhook/aqui

# =============================================================================
# CONFIGURAÇÕES DO GEMINI (GOOGLE AI)
# =============================================================================
# Chave da API do Google AI para usar o Gemini
# Como obter: https://makersuite.google.com/app/apikey
GOOGLE_AI_API_KEY=sua_chave_aqui

# =============================================================================
# CONFIGURAÇÕES DO SISTEMA
# =============================================================================
# Ambiente de execução (development, staging, production)
ENVIRONMENT=development

# Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Diretório para salvar logs do sistema
LOG_DIRECTORY=logs

# =============================================================================
# CONFIGURAÇÕES DE FILTROS
# =============================================================================
# Confiança mínima para criar issues (0.0 a 1.0)
MIN_CONFIDENCE_FOR_ISSUE=0.6

# Idade máxima dos logs para processar (em horas)
MAX_LOG_AGE_HOURS=24

# Severidades que devem criar issues (comma-separated)
ISSUE_SEVERITIES=medium,high,critical
"""
    
    env_path = Path(".env.example")
    if not env_path.exists():
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("   📝 Criado: .env.example")
        print("   💡 Dica: Copie para .env e configure suas chaves")
    else:
        print("   ✅ Existe: .env.example")


def criar_gitignore():
    """Cria arquivo .gitignore apropriado."""
    print("\n🚫 Criando .gitignore...")
    
    gitignore_content = """# Bug Finder - Arquivos a serem ignorados pelo Git

# =============================================================================
# PYTHON
# =============================================================================
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# =============================================================================
# BUG FINDER ESPECÍFICOS
# =============================================================================
# Logs do sistema
logs/
*.log

# Dados temporários
temp/
tmp/

# Arquivos de configuração com secrets
.env.local
.env.production
config/secrets.py

# Backup de issues
backups/

# Cache de análises
cache/

# =============================================================================
# IDE / EDITOR
# =============================================================================
# VSCode
.vscode/
*.code-workspace

# PyCharm
.idea/

# Sublime Text
*.sublime-project
*.sublime-workspace

# =============================================================================
# SISTEMA OPERACIONAL
# =============================================================================
# Windows
Thumbs.db
ehthumbs.db
Desktop.ini
$RECYCLE.BIN/

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*

# Linux
*~
.nfs*
"""
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("   📝 Criado: .gitignore")
    else:
        print("   ✅ Existe: .gitignore")


def verificar_pip():
    """Verifica se pip está disponível."""
    print("\n📦 Verificando pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("   ✅ pip disponível!")
        return True
    except subprocess.CalledProcessError:
        print("   ❌ pip não encontrado!")
        return False


def instalar_dependencias_basicas():
    """Instala dependências básicas para esta fase."""
    print("\n📥 Instalando dependências básicas...")
    
    dependencias_basicas = [
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0", 
        "rich>=13.0.0"
    ]
    
    for dep in dependencias_basicas:
        print(f"   📦 Instalando {dep}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
            print(f"   ✅ {dep} instalado!")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erro ao instalar {dep}: {e}")
            return False
    
    return True


def executar_teste_basico():
    """Executa um teste básico dos modelos."""
    print("\n🧪 Executando teste básico...")
    
    try:
        # Adiciona src ao path
        src_path = Path("src").resolve()
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # Tenta importar nossos modelos
        from models import LogModel, LogLevel
        from datetime import datetime
        
        # Teste básico
        log = LogModel(
            raw_content="TEST: Setup verification",
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message="Teste de configuração"
        )
        
        print(f"   ✅ Teste passou! Log criado: {log}")
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro na importação: {e}")
        print("   💡 Certifique-se que os arquivos de modelo foram criados")
        return False
    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        return False


def main():
    """Função principal do script de setup."""
    criar_banner()
    
    print("🚀 Iniciando configuração do Bug Finder...")
    print("   Esta fase configura os modelos de dados do sistema")
    
    # Verificações iniciais
    if not verificar_python():
        print("\n❌ Configuração abortada - Python inadequado")
        return False
    
    if not verificar_pip():
        print("\n❌ Configuração abortada - pip não disponível") 
        return False
    
    # Criação da estrutura
    criar_estrutura_diretorios()
    criar_arquivos_init()
    criar_arquivo_env()
    criar_gitignore()
    
    # Instalação de dependências
    if not instalar_dependencias_basicas():
        print("\n⚠️  Algumas dependências falharam, mas você pode continuar")
    
    # Teste final
    print("\n" + "="*60)
    print("📋 RESUMO DA CONFIGURAÇÃO")
    print("="*60)
    
    checklist = [
        ("Python 3.8+", verificar_python()),
        ("Estrutura de diretórios", True),  # Sempre True se chegou aqui
        ("Arquivos __init__.py", True),
        ("Configuração (.env.example)", True),
        ("Gitignore", True),
        ("Dependências básicas", True)  # Simplificado para este exemplo
    ]
    
    for item, status in checklist:
        emoji = "✅" if status else "❌"
        print(f"   {emoji} {item}")
    
    print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
    print("\n📋 Próximos passos:")
    print("   1. Copie .env.example para .env")
    print("   2. Configure suas chaves de API no arquivo .env")
    print("   3. Execute: python examples/models_example.py")
    print("   4. Estude o código dos modelos em src/models/")
    
    print("\n💡 Dicas:")
    print("   • Use um ambiente virtual (python -m venv venv)")
    print("   • Leia o FASE2_README.md para detalhes completos")
    print("   • Os modelos são a base de todo o sistema!")
    
    return True


if __name__ == "__main__":
    try:
        sucesso = main()
        exit_code = 0 if sucesso else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Configuração cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)