"""
Ponto de entrada principal do Bug Finder.
Orquestra todo o processo de análise de logs e criação de issues.
"""

import asyncio
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# Configurações e modelos
from .config import settings, validate_environment, print_config_summary
from .models import (
    LogModel, LogLevel, BugFinderProcess, ProcessStatus, 
    ProcessResult, ProcessStep, ProcessContext
)

# Agentes
from .agents.bug_finder_agent import BugFinderAgent
from .agents.log_receiver_agent import LogReceiverAgent
from .agents.bug_analyser_agent import BugAnalyserAgent
from .agents.issue_drafter_agent import IssueDrafterAgent
from .agents.issue_reviewer_agent import IssueReviewerAgent
from .agents.issue_refiner_agent import IssueRefinerAgent
from .agents.issue_creator_agent import IssueCreatorAgent
from .agents.issue_notificator_agent import IssueNotificatorAgent

# MockLLMProvider para testes
class MockLLMProvider:
    """Provedor de modelo de linguagem simulado para testes"""
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Simula uma resposta de um modelo de linguagem"""
        if "análise de bug" in prompt.lower() or "bug analysis" in prompt.lower():
            return """
            {
                "is_bug": true,
                "bug_type": "DATABASE_CONNECTION",
                "criticality": "HIGH",
                "confidence": 0.92,
                "reasoning": "Log mostra uma exceção de timeout de conexão com banco de dados, indicando um problema de infraestrutura crítico",
                "technical_details": {
                    "component": "DatabaseConnectionPool",
                    "error_type": "ConnectionTimeout",
                    "affected_service": "UserService"
                },
                "recommended_action": "INVESTIGATE"
            }
            """
        elif "rascunho de issue" in prompt.lower() or "issue draft" in prompt.lower():
            return """
            {
                "title": "Erro de conexão com banco de dados no serviço de autenticação",
                "description": "## Resumo\\n\\nO serviço de autenticação está apresentando falhas ao tentar conectar ao banco de dados, resultando em timeout após 30 segundos.\\n\\n## Detalhes\\n\\nO erro ocorre durante o processo de login de usuários, causando falhas de autenticação.",
                "labels": ["bug", "critical", "database"],
                "priority": "high",
                "assignees": [],
                "reproduction_steps": ["Tentar fazer login com credenciais válidas", "Observar erro de timeout"],
                "environment_info": {
                    "environment": "production",
                    "component": "UserService",
                    "version": "1.0"
                }
            }
            """
        elif "revisão" in prompt.lower() or "review" in prompt.lower():
            return """
            {
                "title_score": 4,
                "description_score": 3,
                "technical_score": 4,
                "reproduction_score": 3,
                "priority_score": 5,
                "formatting_score": 4,
                "overall_score": 3.8,
                "approved": true,
                "feedback": "Issue bem estruturada, mas a descrição poderia ter mais detalhes técnicos",
                "improvements": [
                    "Adicionar mais informações sobre o ambiente",
                    "Detalhar melhor os passos de reprodução"
                ]
            }
            """
        else:
            return """
            {
                "response": "Resposta genérica simulada para prompts não reconhecidos",
                "status": "success"
            }
            """

class BugFinderSystem:
    """
    Sistema principal do Bug Finder.
    Coordena todos os agentes e gerencia o processo completo.
    """
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger("BugFinderSystem")
        
        # Valida configurações
        if not validate_environment():
            self.logger.error("Falha na validação do ambiente")
            sys.exit(1)
        
        # Inicializa agentes
        self.initialize_agents()
        
        self.logger.info("Bug Finder System inicializado com sucesso")
    
    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=getattr(logging, settings.logging.level.value),
            format=settings.logging.format,
            datefmt=settings.logging.date_format
        )
        
        # Configuração adicional de arquivo se habilitado
        if settings.logging.log_to_file:
            file_handler = logging.FileHandler(settings.logging.log_file_path)
            file_handler.setFormatter(
                logging.Formatter(settings.logging.format, settings.logging.date_format)
            )
            logging.getLogger().addHandler(file_handler)
    
    def initialize_agents(self):
        """Inicializa todos os agentes do sistema"""
        try:
            # Cria um provedor de modelo de linguagem simulado
            llm_provider = MockLLMProvider()
            
            # Inicializa agentes
            self.log_receiver = LogReceiverAgent()
            self.bug_analyser = BugAnalyserAgent(llm_provider=llm_provider)
            self.issue_drafter = IssueDrafterAgent(llm_provider=llm_provider)
            self.issue_reviewer = IssueReviewerAgent(llm_provider=llm_provider)
            self.issue_refiner = IssueRefinerAgent()
            
            # Inicializa ferramentas e agentes que não usam IA
            from .tools.github_tool import GitHubTool, GitHubConfig
            from .tools.discord_tool import DiscordTool, DiscordConfig
            
            # Configurações simuladas para testes
            github_config = GitHubConfig(
                token="dummy_token",
                repository="acme/bug-finder"
            )
            
            discord_config = DiscordConfig(
                webhook_url="https://discord.com/api/webhooks/example"
            )
            
            github_tool = GitHubTool(github_config)
            discord_tool = DiscordTool(discord_config)
            
            self.issue_creator = IssueCreatorAgent(github_tool=github_tool)
            self.issue_notificator = IssueNotificatorAgent(discord_tool=discord_tool)
            
            # Agente maestro
            self.bug_finder = BugFinderAgent(
                log_receiver=self.log_receiver,
                bug_analyser=self.bug_analyser,
                issue_drafter=self.issue_drafter,
                issue_reviewer=self.issue_reviewer,
                issue_refiner=self.issue_refiner,
                issue_creator=self.issue_creator,
                issue_notificator=self.issue_notificator
            )
            
            self.logger.info("Todos os agentes inicializados")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar agentes: {str(e)}")
            raise
    
    async def process_log(self, log_content: str, **metadata) -> BugFinderProcess:
        """
        Processa um log através de todo o pipeline do Bug Finder.
        
        Args:
            log_content: Conteúdo do log a ser processado
            **metadata: Metadados adicionais do log
            
        Returns:
            BugFinderProcess: Resultado completo do processo
        """
        process_id = str(uuid.uuid4())
        self.logger.info(f"Iniciando processo {process_id}")
        
        # Cria o processo
        process = BugFinderProcess(
            process_id=process_id,
            start_time=datetime.now().isoformat()
        )
        
        try:
            # Adiciona contexto inicial
            process.context = ProcessContext(process_id=process_id)
            
            # Cria entry do log
            log_entry = LogModel(
                raw_content=log_content,
                message=log_content,
                level=metadata.get('level', LogLevel.ERROR),
                timestamp=datetime.fromisoformat(metadata.get('timestamp', datetime.now().isoformat())) if isinstance(metadata.get('timestamp'), str) else metadata.get('timestamp', datetime.now()),
                service_name=metadata.get('source', 'unknown'),
                environment=metadata.get('environment', 'production'),
                user_id=metadata.get('user_id'),
                request_id=metadata.get('request_id')
            )
            
            process.context.original_log = log_entry
            
            # Executa o processo através do agente maestro
            result = await self.bug_finder.process_bug_report(process)
            
            self.logger.info(f"Processo {process_id} concluído: {result.final_result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processo {process_id}: {str(e)}")
            process.complete_process(
                ProcessResult.SYSTEM_ERROR,
                f"Erro inesperado: {str(e)}"
            )
            return process
    
    async def process_log_from_json(self, log_data: dict) -> BugFinderProcess:
        """
        Processa um log a partir de dados JSON.
        
        Args:
            log_data: Dados do log em formato JSON
            
        Returns:
            BugFinderProcess: Resultado do processo
        """
        log_content = log_data.get('message', '')
        
        # Extrai metadados
        metadata = {
            'level': LogLevel(log_data.get('level', 'ERROR')),
            'timestamp': log_data.get('timestamp'),
            'source': log_data.get('source'),
            'environment': log_data.get('environment'),
            'user_id': log_data.get('user_id'),
            'session_id': log_data.get('session_id'), 
            'request_id': log_data.get('request_id'),
            'thread_id': log_data.get('thread_id'),
            'version': log_data.get('version')
        }
        
        # Remove valores None
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return await self.process_log(log_content, **metadata)
    
    def get_system_status(self) -> dict:
        """Retorna o status atual do sistema"""
        return {
            "status": "running",
            "environment": settings.environment.value,
            "config_valid": validate_environment(),
            "agents_initialized": hasattr(self, 'bug_finder'),
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """Função principal do programa"""
    print("🚀 Iniciando Bug Finder System...")
    print_config_summary()
    
    try:
        # Inicializa o sistema
        system = BugFinderSystem()
        
        # Exemplo de uso - processa um log de teste
        sample_log = """
2024-06-07 14:30:15 ERROR [UserService] Failed to authenticate user
java.sql.SQLException: Connection timeout after 30s
    at com.company.db.ConnectionPool.getConnection(ConnectionPool.java:145)
    at com.company.service.UserService.authenticateUser(UserService.java:67)
    at com.company.controller.AuthController.login(AuthController.java:34)
User ID: user123, Session: sess_abc789, Request: req_xyz456
        """
        
        print("\n📝 Processando log de exemplo...")
        
        # Processa o log
        result = await system.process_log(
            sample_log,
            level=LogLevel.ERROR,
            source="UserService",
            environment="production",
            user_id="user123",
            session_id="sess_abc789",
            request_id="req_xyz456"
        )
        
        # Exibe resultado
        print(f"\n📊 Resultado do processo:")
        print(f"Status: {result.current_status.value}")
        print(f"Resultado: {result.final_result.value if result.final_result else 'Em processamento'}")
        print(f"Duração: {result.total_duration_seconds:.2f}s")
        print(f"Passos executados: {result.steps_completed}")
        
        if result.is_successful():
            print(f"✅ {result.get_process_summary()}")
        else:
            print(f"❌ {result.get_process_summary()}")
        
        # Exibe métricas de performance
        metrics = result.get_performance_metrics()
        print(f"\n📈 Métricas de Performance:")
        for key, value in metrics.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
        
        print(f"\n🎯 Sistema Bug Finder funcionando corretamente!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
        sys.exit(1)


def run_web_server():
    """Inicia um servidor web para receber logs via HTTP (futura implementação)"""
    print("🌐 Servidor web não implementado ainda")
    print("💡 Para implementar: FastAPI + webhook endpoints")


def run_cli():
    """Interface de linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug Finder System")
    parser.add_argument("--mode", choices=["process", "server", "status"], 
                       default="process", help="Modo de execução")
    parser.add_argument("--log", help="Log para processar")
    parser.add_argument("--file", help="Arquivo com log para processar")
    parser.add_argument("--env", choices=["development", "staging", "production"],
                       help="Ambiente de execução")
    
    args = parser.parse_args()
    
    if args.env:
        import os
        os.environ["ENVIRONMENT"] = args.env
    
    if args.mode == "status":
        system = BugFinderSystem()
        status = system.get_system_status()
        print("📊 Status do Sistema:")
        for key, value in status.items():
            print(f"{key}: {value}")
        return
    
    if args.mode == "server":
        run_web_server()
        return
    
    # Modo process
    if args.file:
        with open(args.file, 'r') as f:
            log_content = f.read()
    elif args.log:
        log_content = args.log
    else:
        # Usa log de exemplo
        log_content = "Sample error log for testing"
    
    # Executa processamento
    asyncio.run(main())


if __name__ == "__main__":
    # Pode ser executado como script ou módulo
    if len(sys.argv) > 1:
        run_cli()
    else:
        asyncio.run(main())