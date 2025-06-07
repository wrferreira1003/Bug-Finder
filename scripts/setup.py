"""
Script de configuração inicial do Bug Finder System.
Prepara o ambiente, valida dependências e configura credenciais.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict

class BugFinderSetup:
    """Classe para configuração inicial do Bug Finder"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.logs_dir = self.project_root / "logs"
        self.config_dir = self.src_dir / "config"
        
        self.required_env_vars = {
            "GEMINI_API_KEY": "Chave da API do Google Gemini",
            "GITHUB_TOKEN": "Token de acesso do GitHub",
            "GITHUB_OWNER": "Proprietário do repositório GitHub",
            "GITHUB_REPOSITORY": "Nome do repositório GitHub",
            "DISCORD_WEBHOOK_URL": "URL do webhook do Discord"
        }
        
        self.optional_env_vars = {
            "ENVIRONMENT": "Ambiente de execução (development/staging/production)",
            "LOG_LEVEL": "Nível de log (DEBUG/INFO/WARNING/ERROR)",
            "DISCORD_CRITICAL_CHANNEL": "ID do canal para bugs críticos",
            "DISCORD_HIGH_CHANNEL": "ID do canal para bugs de alta prioridade",
            "DISCORD_GENERAL_CHANNEL": "ID do canal geral"
        }
    
    def run_setup(self):
        """Executa toda a configuração inicial"""
        print("🚀 Configuração Inicial do Bug Finder System")
        print("=" * 50)
        
        try:
            self.check_python_version()
            self.create_directories()
            self.setup_environment_file()
            self.install_dependencies()
            self.validate_configuration()
            self.run_initial_tests()
            
            print("\n✅ Configuração inicial concluída com sucesso!")
            print("\n📋 Próximos passos:")
            print("1. Configure suas credenciais no arquivo .env")
            print("2. Execute: python src/main.py --mode status")
            print("3. Teste com: python src/main.py")
            
        except Exception as e:
            print(f"\n❌ Erro durante a configuração: {str(e)}")
            sys.exit(1)
    
    def check_python_version(self):
        """Verifica se a versão do Python é compatível"""
        print("🐍 Verificando versão do Python...")
        
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version < min_version:
            raise Exception(
                f"Python {min_version[0]}.{min_version[1]}+ é necessário. "
                f"Versão atual: {current_version[0]}.{current_version[1]}"
            )
        
        print(f"✅ Python {current_version[0]}.{current_version[1]} compatível")
    
    def create_directories(self):
        """Cria diretórios necessários"""
        print("📁 Criando estrutura de diretórios...")
        
        directories = [
            self.logs_dir,
            self.project_root / "examples" / "sample_logs",
            self.project_root / "tests" / "unit",
            self.project_root / "tests" / "integration",
            self.project_root / "docs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   📂 {directory.relative_to(self.project_root)}")
        
        print("✅ Diretórios criados")
    
    def setup_environment_file(self):
        """Configura arquivo de ambiente"""
        print("⚙️  Configurando arquivo de ambiente...")
        
        env_file = self.project_root / ".env"
        env_example_file = self.project_root / ".env.example"
        
        # Cria arquivo .env.example se não existir
        if not env_example_file.exists():
            self.create_env_example(env_example_file)
        
        # Configura arquivo .env se não existir
        if not env_file.exists():
            self.create_env_file(env_file)
        else:
            print("   ℹ️  Arquivo .env já existe, pulando criação")
        
        print("✅ Arquivo de ambiente configurado")
    
    def create_env_example(self, filepath: Path):
        """Cria arquivo .env.example"""
        content = "# Configurações do Bug Finder System\n"
        content += "# Copie este arquivo para .env e configure suas credenciais\n\n"
        
        content += "# Configurações obrigatórias\n"
        for var, desc in self.required_env_vars.items():
            content += f"{var}=your_{var.lower()}_here  # {desc}\n"
        
        content += "\n# Configurações opcionais\n"
        for var, desc in self.optional_env_vars.items():
            if var == "ENVIRONMENT":
                content += f"{var}=development  # {desc}\n"
            elif var == "LOG_LEVEL":
                content += f"{var}=INFO  # {desc}\n"
            else:
                content += f"{var}=  # {desc}\n"
        
        content += "\n# Configurações avançadas\n"
        content += "DB_HOST=localhost\n"
        content += "DB_PORT=5432\n"
        content += "DB_NAME=bugfinder\n"
        content += "DB_USERNAME=\n"
        content += "DB_PASSWORD=\n"
        
        filepath.write_text(content)
        print(f"   📝 {filepath.name} criado")
    
    def create_env_file(self, filepath: Path):
        """Cria arquivo .env básico"""
        print("   📝 Criando arquivo .env...")
        print("   ⚠️  Configure suas credenciais após a instalação!")
        
        content = "# Configurações do Bug Finder System\n\n"
        content += "# Configure suas credenciais reais aqui\n"
        content += "ENVIRONMENT=development\n"
        content += "LOG_LEVEL=INFO\n\n"
        
        for var in self.required_env_vars.keys():
            content += f"{var}=\n"
        
        filepath.write_text(content)
        print(f"   📝 {filepath.name} criado")
    
    def install_dependencies(self):
        """Instala dependências do Python"""
        print("📦 Instalando dependências...")
        
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            self.create_requirements_file(requirements_file)
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True)
            print("✅ Dependências instaladas")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Erro na instalação: {e}")
            print("   💡 Tente executar manualmente: pip install -r requirements.txt")
    
    def create_requirements_file(self, filepath: Path):
        """Cria arquivo requirements.txt"""
        requirements = [
            "# Google AI Agent Development Kit",
            "# google-ai-adk>=1.0.0  # Quando disponível",
            "",
            "# Modelo de linguagem",
            "google-generativeai>=0.3.0",
            "",
            "# APIs e integrações",
            "requests>=2.31.0",
            "aiohttp>=3.8.0",
            "",
            "# Estruturas de dados",
            "pydantic>=2.0.0",
            "dataclasses-json>=0.6.0",
            "",
            "# Utilitários",
            "python-dotenv>=1.0.0",
            "click>=8.1.0",
            "",
            "# Desenvolvimento e testes",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "",
            "# Logging",
            "structlog>=23.1.0",
            "",
            "# Servidor web (futuro)",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0"
        ]
        
        filepath.write_text("\n".join(requirements))
        print(f"   📝 {filepath.name} criado")
    
    def validate_configuration(self):
        """Valida configuração básica"""
        print("🔍 Validando configuração...")
        
        # Verifica se o código Python compila
        try:
            import py_compile
            main_file = self.src_dir / "main.py"
            if main_file.exists():
                py_compile.compile(str(main_file), doraise=True)
                print("   ✅ Código principal compila corretamente")
        except py_compile.PyCompileError as e:
            print(f"   ⚠️  Erro de compilação: {e}")
        
        # Verifica estrutura de arquivos
        essential_files = [
            "src/config/__init__.py",
            "src/models/__init__.py",
            "src/agents/__init__.py"
        ]
        
        for file_path in essential_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} não encontrado")
        
        print("✅ Validação concluída")
    
    def run_initial_tests(self):
        """Executa testes básicos"""
        print("🧪 Executando testes básicos...")
        
        try:
            # Testa importações básicas
            sys.path.insert(0, str(self.src_dir))
            
            # Testa importação de configurações
            from src.config import get_settings
            _ = get_settings  # valida import
            print("   ✅ Importação de configurações")
            
            # Testa importação de modelos
            from src.models import LogModel, LogLevel
            print("   ✅ Importação de modelos")
            
            # Testa criação de log de exemplo
            _ = LogModel(
                message="Teste de configuração",
                level=LogLevel.INFO,
                timestamp="2024-06-07T12:00:00Z"
            )
            print("   ✅ Criação de objetos")
            
        except ImportError as e:
            print(f"   ⚠️  Erro de importação: {e}")
        except Exception as e:
            print(f"   ⚠️  Erro nos testes: {e}")
        
        print("✅ Testes básicos concluídos")
    
    def interactive_config(self):
        """Configuração interativa das credenciais"""
        print("\n🔧 Configuração Interativa")
        print("=" * 30)
        
        env_file = self.project_root / ".env"
        current_config = self.load_env_file(env_file)
        
        print("Configure suas credenciais:")
        
        for var, desc in self.required_env_vars.items():
            current_value = current_config.get(var, "")
            display_value = current_value if not current_value or len(current_value) < 10 else current_value[:10] + "..."
            
            new_value = input(f"{desc} [{display_value}]: ").strip()
            if new_value:
                current_config[var] = new_value
        
        print("\nConfigurações opcionais:")
        for var, desc in self.optional_env_vars.items():
            current_value = current_config.get(var, "")
            new_value = input(f"{desc} [{current_value}]: ").strip()
            if new_value:
                current_config[var] = new_value
        
        self.save_env_file(env_file, current_config)
        print("✅ Configurações salvas!")
    
    def load_env_file(self, filepath: Path) -> Dict[str, str]:
        """Carrega arquivo .env"""
        config = {}
        if filepath.exists():
            for line in filepath.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    
    def save_env_file(self, filepath: Path, config: Dict[str, str]):
        """Salva arquivo .env"""
        content = "# Configurações do Bug Finder System\n"
        content += f"# Atualizado em: {os.popen('date').read().strip()}\n\n"
        
        for key, value in config.items():
            content += f"{key}={value}\n"
        
        filepath.write_text(content)
    
    def check_status(self):
        """Verifica status da configuração"""
        print("📊 Status da Configuração")
        print("=" * 30)
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("❌ Arquivo .env não encontrado")
            return
        
        config = self.load_env_file(env_file)
        
        print("Variáveis obrigatórias:")
        for var, desc in self.required_env_vars.items():
            value = config.get(var, "")
            status = "✅" if value else "❌"
            print(f"  {status} {var}: {desc}")
        
        print("\nVariáveis opcionais:")
        for var, desc in self.optional_env_vars.items():
            value = config.get(var, "")
            status = "✅" if value else "⚪"
            print(f"  {status} {var}: {desc}")


def main():
    """Função principal do script de setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup do Bug Finder System")
    parser.add_argument("--action", choices=["setup", "config", "status"], 
                       default="setup", help="Ação a executar")
    parser.add_argument("--interactive", action="store_true",
                       help="Configuração interativa")
    
    args = parser.parse_args()
    
    setup = BugFinderSetup()
    
    if args.action == "setup":
        setup.run_setup()
        if args.interactive:
            setup.interactive_config()
    elif args.action == "config":
        setup.interactive_config()
    elif args.action == "status":
        setup.check_status()


if __name__ == "__main__":
    main()