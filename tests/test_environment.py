"""
Teste para verificar se o ambiente está configurado corretamente
Salve como: test_environment.py
Execute com: python test_environment.py
"""

import sys
import os

def test_python_version():
    """Testa se a versão do Python está correta"""
    print("🐍 Testando versão do Python...")
    version = sys.version_info
    print(f"   Versão atual: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 11:
        print("   ✅ Versão do Python OK!")
        return True
    else:
        print("   ❌ Python precisa ser 3.11 ou superior!")
        return False

def test_imports():
    """Testa se as principais bibliotecas podem ser importadas"""
    print("\n📚 Testando importações...")
    
    tests = [
        ("google.generativeai", "Google Gemini"),
        ("requests", "Requests HTTP"),
        ("pydantic", "Pydantic"),
        ("dotenv", "Python-dotenv"),
    ]
    
    all_ok = True
    for module, name in tests:
        try:
            __import__(module)
            print(f"   ✅ {name}: OK")
        except ImportError:
            print(f"   ❌ {name}: ERRO - Execute 'pip install -r requirements.txt'")
            all_ok = False
    
    return all_ok

def test_environment_file():
    """Testa se o arquivo .env existe"""
    print("\n🔐 Testando arquivo de ambiente...")
    
    if os.path.exists('.env'):
        print("   ✅ Arquivo .env encontrado!")
        
        # Carrega e testa algumas variáveis
        from dotenv import load_dotenv
        load_dotenv()
        
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key and google_key != 'sua_chave_do_gemini_aqui':
            print("   ✅ GOOGLE_API_KEY configurada!")
        else:
            print("   ⚠️  GOOGLE_API_KEY não configurada (configure depois)")
        
        return True
    else:
        print("   ⚠️  Arquivo .env não encontrado")
        print("   💡 Copie .env.example para .env e configure as chaves")
        return False

def test_project_structure():
    """Testa se a estrutura de pastas está correta"""
    print("\n📁 Testando estrutura do projeto...")
    
    required_dirs = [
        'src',
        'src/agents', 
        'src/tools',
        'src/models',
        'src/config',
        'tests'
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ - pasta não encontrada")
            all_ok = False
    
    return all_ok

def main():
    """Executa todos os testes"""
    print("🧪 TESTE DO AMBIENTE - BUG FINDER")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_imports,
        test_environment_file,
        test_project_structure
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 RESULTADO FINAL:")
    
    if all(results):
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Ambiente pronto para desenvolvimento!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        print("🔧 Revise as configurações acima")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
