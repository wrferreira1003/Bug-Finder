"""
Exemplo prático de como usar os modelos do Bug Finder.

Este script demonstra como criar, manipular e usar os modelos
de dados que os agentes usarão para se comunicar.
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório src ao path para importar nossos módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import (
    LogModel, LogLevel, create_log_from_text,
    BugAnalysis, BugSeverity, BugCategory, create_quick_bug_analysis,
    IssueModel, IssueStatus, IssuePriority, create_issue_from_analysis
)


def exemplo_log_model():
    """
    Demonstra como usar o LogModel para representar logs de erro.
    """
    print("=" * 60)
    print("🔍 EXEMPLO: LogModel")
    print("=" * 60)
    
    # 1. Criando um log manualmente
    print("\n1. Criando um log manualmente:")
    log1 = LogModel(
        raw_content="ERROR: Database connection failed - timeout after 30s",
        timestamp=datetime.now(),
        level=LogLevel.ERROR,
        message="Database connection failed - timeout after 30s",
        service_name="user-service",
        environment="production"
    )
    
    print(f"Log criado: {log1}")
    print(f"É um erro? {log1.is_error}")
    print(f"É crítico? {log1.is_critical}")
    
    # 2. Criando log a partir de texto simples
    print("\n2. Criando log a partir de texto:")
    texto_log = """
    FATAL: OutOfMemoryError - Java heap space
    at com.example.UserService.processUsers(UserService.java:45)
    at com.example.Controller.handleRequest(Controller.java:23)
    """
    
    log2 = create_log_from_text(texto_log, service_name="user-service")
    print(f"Log do texto: {log2}")
    print(f"Nível detectado: {log2.level}")
    print(f"Stack trace encontrado: {bool(log2.stack_trace)}")
    
    # 3. Convertendo para dicionário (útil para APIs)
    print("\n3. Convertendo para dicionário:")
    log_dict = log1.to_dict()
    print(f"Como dicionário: {log_dict['level']} - {log_dict['message']}")
    
    # 4. Recriando a partir do dicionário
    print("\n4. Recriando a partir do dicionário:")
    log_restaurado = LogModel.from_dict(log_dict)
    print(f"Log restaurado: {log_restaurado}")


def exemplo_bug_analysis():
    """
    Demonstra como usar BugAnalysis para representar análises de bugs.
    """
    print("\n\n" + "=" * 60)
    print("🧠 EXEMPLO: BugAnalysis")
    print("=" * 60)
    
    # 1. Criando uma análise positiva (é um bug)
    print("\n1. Análise positiva - É um bug:")
    analysis1 = BugAnalysis(
        is_bug=True,
        confidence=0.9,
        severity=BugSeverity.HIGH,
        category=BugCategory.DATABASE,
        title="Timeout de conexão com banco de dados em produção",
        description="Conexões com o banco estão falhando após 30s de timeout",
        impact_description="Usuários não conseguem fazer login",
        estimated_users_affected=500,
        possible_causes=[
            "Sobrecarga no banco de dados",
            "Problema de rede entre serviços",
            "Pool de conexões esgotado"
        ],
        suggested_tags=["database", "timeout", "production"]
    )
    
    print(f"Análise: {analysis1}")
    print(f"É bug crítico? {analysis1.is_critical_bug}")
    print(f"Deve criar issue? {analysis1.should_create_issue}")
    print(f"Score de prioridade: {analysis1.get_priority_score()}")
    
    # 2. Criando uma análise negativa (não é bug)
    print("\n2. Análise negativa - Não é um bug:")
    analysis2 = BugAnalysis(
        is_bug=False,
        confidence=0.8,
        description="Este é apenas um log informativo de inicialização do sistema"
    )
    
    print(f"Análise: {analysis2}")
    print(f"Deve criar issue? {analysis2.should_create_issue}")
    
    # 3. Usando função helper para criar análise rápida
    print("\n3. Análise rápida usando helper:")
    analysis3 = create_quick_bug_analysis(
        title="Erro de validação de dados",
        severity=BugSeverity.MEDIUM,
        category=BugCategory.API
    )
    
    print(f"Análise rápida: {analysis3}")


def exemplo_issue_model():
    """
    Demonstra como usar IssueModel para representar issues do GitHub.
    """
    print("\n\n" + "=" * 60)
    print("📋 EXEMPLO: IssueModel")
    print("=" * 60)
    
    # 1. Criando uma issue básica
    print("\n1. Criando issue básica:")
    issue1 = IssueModel(
        title="Sistema de login apresenta timeout intermitente",
        description="Usuários relatam timeout ao tentar fazer login durante horários de pico",
        priority=IssuePriority.P1
    )
    
    print(f"Issue: {issue1}")
    print(f"É crítica? {issue1.is_critical}")
    print(f"Pronta para GitHub? {issue1.is_ready_for_github}")
    
    # 2. Adicionando informações detalhadas
    print("\n2. Adicionando detalhes:")
    issue1.steps_to_reproduce = [
        "Acesse a página de login",
        "Digite credenciais válidas",
        "Clique em 'Entrar'",
        "Aguarde mais de 30 segundos"
    ]
    
    issue1.expected_behavior = "Login deve ser concluído em menos de 5 segundos"
    issue1.actual_behavior = "Login falha com timeout após 30 segundos"
    
    issue1.environment_info = {
        "Ambiente": "Produção",
        "Navegador": "Chrome 120",
        "Horário": "18:00-19:00 (pico)"
    }
    
    issue1.add_label("urgent")
    issue1.add_label("user-impact")
    issue1.add_assignee("dev-team-lead")
    
    print(f"Labels: {issue1.labels}")
    print(f"Assignees: {issue1.assignees}")
    
    # 3. Gerando corpo da issue para GitHub
    print("\n3. Corpo da issue em Markdown:")
    github_body = issue1.github_body
    print("--- INÍCIO DO MARKDOWN ---")
    print(github_body[:300] + "...")  # Mostra apenas parte para não poluir
    print("--- FIM DO MARKDOWN ---")


def exemplo_fluxo_completo():
    """
    Demonstra um fluxo completo: Log → Análise → Issue
    """
    print("\n\n" + "=" * 60)
    print("🔄 EXEMPLO: Fluxo Completo")
    print("=" * 60)
    
    # 1. Começa com um log de erro
    print("\n1. Log de erro recebido:")
    log_texto = """
    ERROR 2024-06-07 15:30:45 [user-service] Database query timeout
    Query: SELECT * FROM users WHERE active=true
    Duration: 45.2s (timeout at 30s)
    Connection pool: 45/50 connections in use
    """
    
    log = create_log_from_text(log_texto, service_name="user-service")
    print(f"Log processado: {log.level.value} - {log.message}")
    
    # 2. Análise do bug
    print("\n2. Análise do bug:")
    analysis = BugAnalysis(
        is_bug=True,
        confidence=0.85,
        severity=BugSeverity.HIGH,
        category=BugCategory.DATABASE,
        title="Query de usuários apresenta timeout em produção",
        description="Consulta de usuários ativos está excedendo o timeout configurado",
        impact_description="Página de usuários não carrega, afetando dashboard admin",
        estimated_users_affected=10,  # Apenas admins
        possible_causes=[
            "Consulta não otimizada",
            "Índice faltando na coluna 'active'",
            "Volume de dados cresceu além do esperado"
        ],
        suggested_tags=["database", "performance", "timeout"],
        urgency_reason="Afeta funcionalidade crítica do admin"
    )
    
    print(f"Resultado da análise: {analysis}")
    print(f"Deve criar issue? {analysis.should_create_issue}")
    
    # 3. Criação da issue
    print("\n3. Criação da issue:")
    issue = create_issue_from_analysis(analysis, log)
    
    print(f"Issue criada: {issue.title}")
    print(f"Prioridade: {issue.priority.value}")
    print(f"Labels: {', '.join(issue.labels)}")
    
    # 4. Simulando aprovação e finalização
    print("\n4. Fluxo de aprovação:")
    issue.update_status(IssueStatus.UNDER_REVIEW)
    print(f"Status atualizado: {issue.status.value}")
    
    issue.update_status(IssueStatus.APPROVED)
    print(f"Issue aprovada: {issue.status.value}")
    print(f"Pronta para GitHub: {issue.is_ready_for_github}")
    
    # 5. Exemplo do que seria enviado ao GitHub
    print("\n5. Dados que seriam enviados ao GitHub:")
    github_data = {
        "title": issue.title,
        "body": issue.github_body,
        "labels": issue.labels,
        "assignees": issue.assignees
    }
    
    print(f"Título: {github_data['title']}")
    print(f"Labels: {github_data['labels']}")
    print("Corpo da issue gerado em Markdown ✓")


def main():
    """
    Função principal que executa todos os exemplos.
    """
    print("🚀 EXEMPLOS DE USO DOS MODELOS DO BUG FINDER")
    print("Este script demonstra como usar as estruturas de dados do sistema")
    
    try:
        exemplo_log_model()
        exemplo_bug_analysis()
        exemplo_issue_model()
        exemplo_fluxo_completo()
        
        print("\n\n" + "=" * 60)
        print("✅ TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("=" * 60)
        print("\nPróximos passos:")
        print("1. Estudar o código dos modelos")
        print("2. Experimentar criar seus próprios exemplos")
        print("3. Partir para a criação das ferramentas (tools)")
        
    except Exception as e:
        print(f"\n❌ ERRO ao executar exemplos: {e}")
        print("Verifique se a estrutura de diretórios está correta")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()