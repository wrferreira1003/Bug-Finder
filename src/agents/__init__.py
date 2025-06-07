"""
Módulo de agentes do Bug Finder.
Centraliza todos os agentes especializados do sistema.
"""

# Agente principal (maestro)
from .bug_finder_agent import BugFinderAgent

# Agentes especializados
from .log_receiver_agent import LogReceiverAgent
from .bug_analyser_agent import BugAnalyserAgent
from .issue_drafter_agent import IssueModelerAgent
from .issue_reviewer_agent import IssueReviewerAgent
from .issue_refiner_agent import IssueRefinerAgent
from .issue_creator_agent import IssueCreatorAgent
from .issue_notificator_agent import IssueNotificatorAgent

# Lista de todos os agentes exportados
__all__ = [
    "BugFinderAgent",
    "LogReceiverAgent",
    "BugAnalyserAgent", 
    "IssueModelerAgent",
    "IssueReviewerAgent",
    "IssueRefinerAgent",
    "IssueCreatorAgent",
    "IssueNotificatorAgent"
]

# Versão do módulo
__version__ = "1.0.0"

# Metadados dos agentes
AGENT_INFO = {
    "BugFinderAgent": {
        "role": "Maestro",
        "description": "Coordena todo o processo e delega tarefas",
        "inputs": ["LogModel"],
        "outputs": ["BugFinderProcess"]
    },
    "LogReceiverAgent": {
        "role": "Porteiro", 
        "description": "Recebe e valida logs de entrada",
        "inputs": ["raw_log"],
        "outputs": ["LogModel"]
    },
    "BugAnalyserAgent": {
        "role": "Detetive",
        "description": "Analisa logs para identificar bugs reais",
        "inputs": ["LogModel"],
        "outputs": ["BugAnalysis"]
    },
    "IssueModelerAgent": {
        "role": "Escritor",
        "description": "Cria rascunhos de issues bem estruturadas",
        "inputs": ["BugAnalysis", "LogModel"],
        "outputs": ["IssueModel"]
    },
    "IssueReviewerAgent": {
        "role": "Crítico",
        "description": "Revisa qualidade das issues antes da publicação",
        "inputs": ["IssueModel"],
        "outputs": ["IssueReview"]
    },
    "IssueRefinerAgent": {
        "role": "Editor",
        "description": "Refina issues baseado no feedback de revisão",
        "inputs": ["IssueModel", "IssueReview"],
        "outputs": ["IssueModel"]
    },
    "IssueCreatorAgent": {
        "role": "Publicador",
        "description": "Cria issues no GitHub via API",
        "inputs": ["IssueModel"],
        "outputs": ["IssueCreationResult"]
    },
    "IssueNotificatorAgent": {
        "role": "Mensageiro",
        "description": "Envia notificações para Discord",
        "inputs": ["IssueCreationResult"],
        "outputs": ["NotificationResult"]
    }
}

def get_agent_info(agent_name: str) -> dict:
    """
    Retorna informações sobre um agente específico.
    
    Args:
        agent_name: Nome da classe do agente
        
    Returns:
        dict: Informações do agente
    """
    return AGENT_INFO.get(agent_name, {})

def list_all_agents() -> list:
    """
    Retorna lista de todos os agentes disponíveis.
    
    Returns:
        list: Lista com nomes de todos os agentes
    """
    return list(AGENT_INFO.keys())

def get_agent_pipeline() -> list:
    """
    Retorna a ordem de execução dos agentes no pipeline.
    
    Returns:
        list: Lista ordenada dos agentes
    """
    return [
        "LogReceiverAgent",
        "BugAnalyserAgent", 
        "IssueModelerAgent",
        "IssueReviewerAgent",
        "IssueRefinerAgent",  # Executado condicionalmente
        "IssueCreatorAgent",
        "IssueNotificatorAgent"
    ]

def validate_agent_dependencies() -> bool:
    """
    Valida se todos os agentes necessários estão disponíveis.
    
    Returns:
        bool: True se todos os agentes estão disponíveis
    """
    try:
        # Tenta importar todos os agentes
        for agent_name in __all__:
            globals()[agent_name]
        return True
    except ImportError:
        return False

def create_agent_instance(agent_name: str, **kwargs):
    """
    Cria uma instância de um agente específico.
    
    Args:
        agent_name: Nome da classe do agente
        **kwargs: Parâmetros para inicialização
        
    Returns:
        Instance do agente solicitado
    """
    if agent_name not in __all__:
        raise ValueError(f"Agente {agent_name} não encontrado")
    
    agent_class = globals()[agent_name]
    return agent_class(**kwargs)

def get_system_architecture() -> dict:
    """
    Retorna uma visão da arquitetura do sistema de agentes.
    
    Returns:
        dict: Estrutura da arquitetura
    """
    return {
        "coordinator": {
            "agent": "BugFinderAgent",
            "role": "Orquestra todo o processo"
        },
        "pipeline": [
            {
                "step": 1,
                "agent": "LogReceiverAgent", 
                "action": "Recebe e valida log"
            },
            {
                "step": 2,
                "agent": "BugAnalyserAgent",
                "action": "Analisa se é bug real"
            },
            {
                "step": 3,
                "agent": "IssueModelerAgent",
                "action": "Cria rascunho da issue"
            },
            {
                "step": 4,
                "agent": "IssueReviewerAgent", 
                "action": "Revisa qualidade"
            },
            {
                "step": 5,
                "agent": "IssueRefinerAgent",
                "action": "Aplica melhorias (se necessário)"
            },
            {
                "step": 6,
                "agent": "IssueCreatorAgent",
                "action": "Publica no GitHub"
            },
            {
                "step": 7,
                "agent": "IssueNotificatorAgent",
                "action": "Notifica no Discord"
            }
        ],
        "flow_control": {
            "conditional_steps": ["IssueRefinerAgent"],
            "retry_logic": ["IssueCreatorAgent", "IssueNotificatorAgent"],
            "early_exit": ["BugAnalyserAgent"]
        }
    }

# Funções de conveniência para debugging
def print_agent_info():
    """Imprime informações de todos os agentes"""
    print("🤖 Agentes do Bug Finder System")
    print("=" * 50)
    
    for agent_name, info in AGENT_INFO.items():
        print(f"\n{agent_name} ({info['role']})")
        print(f"  📝 {info['description']}")
        print(f"  📥 Entrada: {', '.join(info['inputs'])}")
        print(f"  📤 Saída: {', '.join(info['outputs'])}")

def print_system_flow():
    """Imprime o fluxo do sistema"""
    architecture = get_system_architecture()
    
    print("🔄 Fluxo do Sistema Bug Finder")
    print("=" * 50)
    
    print(f"\n🎯 Coordenador: {architecture['coordinator']['agent']}")
    print(f"   {architecture['coordinator']['role']}")
    
    print(f"\n📋 Pipeline de Execução:")
    for step in architecture['pipeline']:
        print(f"  {step['step']}. {step['agent']}")
        print(f"     → {step['action']}")
    
    print(f"\n⚙️  Controle de Fluxo:")
    flow = architecture['flow_control']
    print(f"  🔀 Passos condicionais: {', '.join(flow['conditional_steps'])}")
    print(f"  🔄 Com retry: {', '.join(flow['retry_logic'])}")
    print(f"  🚪 Saída antecipada: {', '.join(flow['early_exit'])}")