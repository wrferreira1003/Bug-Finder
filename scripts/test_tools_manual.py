"""
Script para testar as ferramentas manualmente com APIs reais.
Use apenas em ambiente de desenvolvimento!
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar diretório raiz ao path para importar src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.github_tool import GitHubTool, GitHubConfig
from src.tools.discord_tool import DiscordTool, DiscordConfig
from src.models.issue_model import IssueModel, IssuePriority

def test_github_connection():
    """Testa conexão real com GitHub"""
    print("🔧 Testando conexão com GitHub...")
    
    config = GitHubConfig(
        token=os.getenv("GITHUB_TOKEN"),
        repository=os.getenv("GITHUB_REPOSITORY", "placeholder/repo")
    )
    
    tool = GitHubTool(config)
    
    # Testar apenas a autenticação
    result = tool.test_connection()
    
    if result["success"]:
        print(f"✅ Conexão OK! {result['message']}")
        
        # Se a autenticação funcionou, testar listagem de issues se o repositório estiver configurado
        if os.getenv("GITHUB_REPOSITORY"):
            print("  Testando acesso ao repositório...")
            list_result = tool.list_issues(limit=5)
            if list_result["success"]:
                print(f"  ✅ Repositório OK! Encontradas {list_result['total_count']} issues")
                for issue in list_result["issues"]:
                    print(f"    - #{issue['number']}: {issue['title']}")
            else:
                print(f"  ⚠️  Repositório inacessível: {list_result['message']}")
                return False
    else:
        print(f"❌ Erro: {result['message']}")
        return False
    
    return True

def test_discord_connection():
    """Testa conexão real com Discord"""
    print("💬 Testando conexão com Discord...")
    
    if not os.getenv("DISCORD_WEBHOOK_URL"):
        print("⏭️  Discord webhook não configurado, pulando teste.")
        return True  # Não falha se não está configurado
    
    config = DiscordConfig(
        webhook_url=os.getenv("DISCORD_WEBHOOK_URL")
    )
    
    tool = DiscordTool(config)
    
    # Testar conexão
    result = tool.test_connection()
    
    if result["success"]:
        print("✅ Conexão OK! Mensagem enviada para Discord")
    else:
        print(f"❌ Erro: {result['message']}")
    
    return result["success"]

def test_create_test_issue():
    """Cria uma issue de teste (cuidado - isso é real!)"""
    print("\n🐛 Criando issue de teste...")
    
    # Confirmar antes de criar
    confirm = input("Isso criará uma issue REAL no GitHub. Continuar? (y/N): ")
    if confirm.lower() != 'y':
        print("Teste cancelado.")
        return False
    
    config = GitHubConfig(
        token=os.getenv("GITHUB_TOKEN"),
        repository=os.getenv("GITHUB_REPOSITORY")
    )
    
    tool = GitHubTool(config)
    
    # Criar issue de teste
    test_issue = IssueModel(
        title="[TESTE] Bug Finder - Teste de Integração",
        description="""
## 🧪 Issue de Teste

Esta é uma issue criada automaticamente pelo sistema Bug Finder para testar a integração com GitHub.

### Detalhes do Teste
- **Sistema**: Bug Finder
- **Módulo**: Ferramenta GitHub  
- **Objetivo**: Validar criação automática de issues

### ⚠️ Ação Necessária
Esta issue pode ser fechada imediatamente, pois é apenas um teste.

---
*Issue criada automaticamente pelo Bug Finder System*
        """,
        priority=IssuePriority.P3,
        labels=["test", "bug-finder", "automation"]
    )
    
    result = tool.create_issue(test_issue)
    
    if result["success"]:
        print(f"✅ Issue criada: {result['issue_url']}")
        return result["issue_url"]
    else:
        print(f"❌ Erro: {result['message']}")
        return False

def test_full_workflow():
    """Testa fluxo completo: GitHub + Discord"""
    print("\n🔄 Testando fluxo completo...")
    
    # Criar issue
    issue_url = test_create_test_issue()
    if not issue_url:
        return False
    
    # Notificar Discord
    config = DiscordConfig(
        webhook_url=os.getenv("DISCORD_WEBHOOK_URL")
    )
    
    tool = DiscordTool(config)
    
    result = tool.send_bug_notification(
        issue_url=issue_url,
        issue_title="[TESTE] Bug Finder - Teste de Integração",
        severity="low",
        description="Esta é uma notificação de teste do sistema Bug Finder",
        additional_info={
            "sistema": "Bug Finder",
            "ambiente": "Desenvolvimento",
            "modulo": "Testes de Integração"
        }
    )
    
    if result["success"]:
        print("✅ Fluxo completo executado com sucesso!")
        print(f"   - Issue: {issue_url}")
        print("   - Discord: Notificação enviada")
        return True
    else:
        print(f"❌ Erro no Discord: {result['message']}")
        return False

def main():
    """Função principal do script de teste"""
    print("🚀 Bug Finder - Teste Manual das Ferramentas")
    print("=" * 50)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar variáveis mínimas necessárias
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN é obrigatório. Configure o arquivo .env antes de executar os testes.")
        return
    
    missing_optional = []
    if not os.getenv("GITHUB_REPOSITORY"):
        missing_optional.append("GITHUB_REPOSITORY (teste de repositório será pulado)")
    if not os.getenv("DISCORD_WEBHOOK_URL"):
        missing_optional.append("DISCORD_WEBHOOK_URL (teste de Discord será pulado)")
    
    if missing_optional:
        print(f"⚠️  Variáveis opcionais faltando: {', '.join(missing_optional)}")
        print()
    
    # Executar testes
    github_ok = test_github_connection()
    discord_ok = test_discord_connection()
    
    if github_ok and discord_ok:
        print("\n🎉 Todas as conexões estão funcionando!")
        
        test_full = input("\nExecutar teste completo (criar issue + notificar)? (y/N): ")
        if test_full.lower() == 'y':
            test_full_workflow()
    else:
        print("\n❌ Algumas conexões falharam. Verifique as configurações.")

if __name__ == "__main__":
    main()