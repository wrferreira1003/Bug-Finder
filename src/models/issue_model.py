"""
Modelo que representa uma issue do GitHub a ser criada pelo sistema.

Este modelo padroniza como as issues são estruturadas antes de serem
enviadas para o GitHub, garantindo qualidade e consistência.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class IssueStatus(Enum):
    """
    Status de uma issue no fluxo de trabalho do Bug Finder.
    
    Representa o estado atual da issue no processo de criação.
    """
    DRAFT = "draft"                    # Rascunho inicial
    UNDER_REVIEW = "under_review"      # Em revisão pelo agente revisor
    NEEDS_REFINEMENT = "needs_refinement"  # Precisa ser melhorada
    APPROVED = "approved"              # Aprovada para publicação
    CREATED = "created"                # Criada no GitHub
    NOTIFIED = "notified"              # Equipe foi notificada

class IssuePriority(Enum):
    """
    Prioridades de issue seguindo padrões comuns da indústria.
    """
    P0 = "P0"  # Crítica - Sistema parado ou problema de segurança
    P1 = "P1"  # Alta - Funcionalidade importante quebrada
    P2 = "P2"  # Média - Bug que afeta experiência mas tem workaround
    P3 = "P3"  # Baixa - Melhoria ou bug menor

@dataclass
class IssueModel:
    """
    Representa uma issue completa a ser criada no GitHub.
    
    Esta classe contém todas as informações necessárias para criar
    uma issue bem documentada e útil para os desenvolvedores.
    
    Attributes:
        title (str): Título claro e conciso da issue
        description (str): Descrição detalhada do problema
        steps_to_reproduce (List[str]): Passos para reproduzir o bug
        expected_behavior (str): Comportamento esperado
        actual_behavior (str): Comportamento atual (com problema)
        environment_info (Dict[str, str]): Informações do ambiente
        priority (IssuePriority): Prioridade da issue
        labels (List[str]): Labels/tags para a issue
        assignees (List[str]): Pessoas para serem assignadas
        milestone (Optional[str]): Milestone do projeto
        component (Optional[str]): Componente afetado
        version (Optional[str]): Versão onde o bug foi encontrado
        browser_info (Optional[str]): Informações de navegador (se web)
        error_details (Dict[str, Any]): Detalhes técnicos do erro
        stack_trace (Optional[str]): Stack trace completo
        logs_snippet (Optional[str]): Trecho relevante dos logs
        impact_assessment (str): Avaliação do impacto
        suggested_fix (Optional[str]): Sugestão de correção
        related_issues (List[str]): Issues relacionadas
        attachments (List[str]): Links para screenshots, logs, etc.
        reporter_info (Dict[str, str]): Info sobre quem reportou
        status (IssueStatus): Status atual da issue
        created_at (datetime): Quando a issue foi criada
        updated_at (datetime): Última atualização
        metadata (Dict[str, Any]): Metadados adicionais
    """
    
    # Campos obrigatórios para qualquer issue
    title: str
    description: str
    priority: IssuePriority
    
    # Informações técnicas detalhadas
    steps_to_reproduce: Optional[List[str]] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    environment_info: Optional[Dict[str, str]] = None
    
    # Organização e gestão
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    milestone: Optional[str] = None
    component: Optional[str] = None
    version: Optional[str] = None
    
    # Detalhes técnicos específicos
    browser_info: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    logs_snippet: Optional[str] = None
    
    # Análise e contexto
    impact_assessment: Optional[str] = None
    suggested_fix: Optional[str] = None
    related_issues: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    
    # Metadados
    reporter_info: Optional[Dict[str, str]] = None
    status: IssueStatus = IssueStatus.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """
        Inicialização e validação após criação do objeto.
        """
        # Define timestamps se não fornecidos
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
        
        # Inicializa listas vazias se None
        if self.steps_to_reproduce is None:
            self.steps_to_reproduce = []
        if self.labels is None:
            self.labels = []
        if self.assignees is None:
            self.assignees = []
        if self.related_issues is None:
            self.related_issues = []
        if self.attachments is None:
            self.attachments = []
        if self.environment_info is None:
            self.environment_info = {}
        if self.error_details is None:
            self.error_details = {}
        if self.reporter_info is None:
            self.reporter_info = {}
        if self.metadata is None:
            self.metadata = {}
        
        # Validações básicas
        if not self.title.strip():
            raise ValueError("título não pode estar vazio")
        if not self.description.strip():
            raise ValueError("descrição não pode estar vazia")
        
        # Limpa espaços em branco
        self.title = self.title.strip()
        self.description = self.description.strip()
        
        # Adiciona label de prioridade automaticamente
        priority_label = f"priority-{self.priority.value.lower()}"
        if priority_label not in self.labels:
            self.labels.append(priority_label)
    
    @property
    def is_critical(self) -> bool:
        """
        Verifica se a issue é crítica (P0).
        
        Returns:
            bool: True se é P0
        """
        return self.priority == IssuePriority.P0
    
    @property
    def is_ready_for_github(self) -> bool:
        """
        Verifica se a issue está pronta para ser criada no GitHub.
        
        Returns:
            bool: True se está pronta
        """
        return self.status == IssueStatus.APPROVED
    
    @property
    def github_body(self) -> str:
        """
        Gera o corpo da issue formatado em Markdown para GitHub.
        
        Returns:
            str: Corpo da issue em formato Markdown
        """
        sections = []
        
        # Descrição principal
        sections.append("## 📝 Descrição")
        sections.append(self.description)
        
        # Comportamento esperado vs atual
        if self.expected_behavior or self.actual_behavior:
            sections.append("## 🎯 Comportamento")
            if self.expected_behavior:
                sections.append("**Esperado:**")
                sections.append(self.expected_behavior)
            if self.actual_behavior:
                sections.append("**Atual:**")
                sections.append(self.actual_behavior)
        
        # Passos para reproduzir
        if self.steps_to_reproduce:
            sections.append("## 🔄 Passos para Reproduzir")
            for i, step in enumerate(self.steps_to_reproduce, 1):
                sections.append(f"{i}. {step}")
        
        # Informações do ambiente
        if self.environment_info:
            sections.append("## 🌍 Ambiente")
            for key, value in self.environment_info.items():
                sections.append(f"- **{key}:** {value}")
        
        # Detalhes técnicos
        if self.error_details:
            sections.append("## 🔧 Detalhes Técnicos")
            for key, value in self.error_details.items():
                sections.append(f"- **{key}:** {value}")
        
        # Stack trace
        if self.stack_trace:
            sections.append("## 📊 Stack Trace")
            sections.append("```")
            sections.append(self.stack_trace)
            sections.append("```")
        
        # Logs
        if self.logs_snippet:
            sections.append("## 📋 Logs Relevantes")
            sections.append("```")
            sections.append(self.logs_snippet)
            sections.append("```")
        
        # Avaliação de impacto
        if self.impact_assessment:
            sections.append("## 📈 Impacto")
            sections.append(self.impact_assessment)
        
        # Sugestão de correção
        if self.suggested_fix:
            sections.append("## 💡 Sugestão de Correção")
            sections.append(self.suggested_fix)
        
        # Issues relacionadas
        if self.related_issues:
            sections.append("## 🔗 Issues Relacionadas")
            for issue in self.related_issues:
                sections.append(f"- {issue}")
        
        # Metadados
        sections.append("---")
        sections.append("*Issue criada automaticamente pelo Bug Finder*")
        if self.metadata.get('analysis_confidence'):
            confidence = self.metadata['analysis_confidence']
            sections.append(f"*Confiança da análise: {confidence:.1%}*")
        
        return "\n\n".join(sections)
    
    def add_label(self, label: str) -> None:
        """
        Adiciona uma label à issue.
        
        Args:
            label (str): Label a ser adicionada
        """
        if label and label not in self.labels:
            self.labels.append(label)
            self._update_timestamp()
    
    def remove_label(self, label: str) -> None:
        """
        Remove uma label da issue.
        
        Args:
            label (str): Label a ser removida
        """
        if label in self.labels:
            self.labels.remove(label)
            self._update_timestamp()
    
    def add_assignee(self, username: str) -> None:
        """
        Adiciona um assignee à issue.
        
        Args:
            username (str): Username do GitHub
        """
        if username and username not in self.assignees:
            self.assignees.append(username)
            self._update_timestamp()
    
    def update_status(self, new_status: IssueStatus) -> None:
        """
        Atualiza o status da issue.
        
        Args:
            new_status (IssueStatus): Novo status
        """
        if self.status != new_status:
            self.status = new_status
            self._update_timestamp()
    
    def _update_timestamp(self) -> None:
        """
        Atualiza o timestamp de última modificação.
        """
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a issue para dicionário.
        
        Returns:
            Dict[str, Any]: Representação em dicionário
        """
        return {
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'steps_to_reproduce': self.steps_to_reproduce,
            'expected_behavior': self.expected_behavior,
            'actual_behavior': self.actual_behavior,
            'environment_info': self.environment_info,
            'labels': self.labels,
            'assignees': self.assignees,
            'milestone': self.milestone,
            'component': self.component,
            'version': self.version,
            'browser_info': self.browser_info,
            'error_details': self.error_details,
            'stack_trace': self.stack_trace,
            'logs_snippet': self.logs_snippet,
            'impact_assessment': self.impact_assessment,
            'suggested_fix': self.suggested_fix,
            'related_issues': self.related_issues,
            'attachments': self.attachments,
            'reporter_info': self.reporter_info,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IssueModel':
        """
        Cria uma IssueModel a partir de dicionário.
        
        Args:
            data (Dict[str, Any]): Dados da issue
            
        Returns:
            IssueModel: Nova instância
        """
        return cls(
            title=data['title'],
            description=data['description'],
            priority=IssuePriority(data['priority']),
            steps_to_reproduce=data.get('steps_to_reproduce'),
            expected_behavior=data.get('expected_behavior'),
            actual_behavior=data.get('actual_behavior'),
            environment_info=data.get('environment_info'),
            labels=data.get('labels'),
            assignees=data.get('assignees'),
            milestone=data.get('milestone'),
            component=data.get('component'),
            version=data.get('version'),
            browser_info=data.get('browser_info'),
            error_details=data.get('error_details'),
            stack_trace=data.get('stack_trace'),
            logs_snippet=data.get('logs_snippet'),
            impact_assessment=data.get('impact_assessment'),
            suggested_fix=data.get('suggested_fix'),
            related_issues=data.get('related_issues'),
            attachments=data.get('attachments'),
            reporter_info=data.get('reporter_info'),
            status=IssueStatus(data.get('status', 'draft')),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            metadata=data.get('metadata')
        )
    
    def __str__(self) -> str:
        """
        Representação em string da issue.
        """
        return f"IssueModel({self.priority.value}: {self.title[:50]}...)"
    
    def __repr__(self) -> str:
        """
        Representação técnica da issue.
        """
        return (f"IssueModel(title='{self.title}', priority={self.priority.value}, "
                f"status={self.status.value})")


# Funções utilitárias

def create_basic_issue(title: str, 
                      description: str, 
                      priority: IssuePriority = IssuePriority.P2) -> IssueModel:
    """
    Cria uma issue básica com informações mínimas.
    
    Args:
        title (str): Título da issue
        description (str): Descrição da issue
        priority (IssuePriority): Prioridade da issue
        
    Returns:
        IssueModel: Nova issue básica
    """
    return IssueModel(
        title=title,
        description=description,
        priority=priority
    )


def create_issue_from_analysis(analysis, log_model) -> IssueModel:
    """
    Cria uma issue a partir de uma análise de bug e log.
    
    Args:
        analysis: BugAnalysis com resultado da análise
        log_model: LogModel com log original
        
    Returns:
        IssueModel: Issue criada a partir da análise
    """
    # Mapeia severidade para prioridade
    severity_to_priority = {
        "critical": IssuePriority.P0,
        "high": IssuePriority.P1,
        "medium": IssuePriority.P2,
        "low": IssuePriority.P3
    }
    
    priority = severity_to_priority.get(
        analysis.severity.value if analysis.severity else "medium", 
        IssuePriority.P2
    )
    
    # Constrói informações do ambiente
    env_info = {}
    if log_model.service_name:
        env_info['Serviço'] = log_model.service_name
    if log_model.environment:
        env_info['Ambiente'] = log_model.environment
    if log_model.user_id:
        env_info['Usuário Afetado'] = log_model.user_id
    if log_model.request_id:
        env_info['Request ID'] = log_model.request_id
    
    # Constrói detalhes do erro
    error_details = {
        'Timestamp': log_model.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'Nível': log_model.level.value.upper()
    }
    
    # Adiciona dados extras se houver
    if log_model.additional_data:
        error_details.update(log_model.additional_data)
    
    # Constrói labels baseadas na análise
    labels = ['bug', 'auto-generated']
    if analysis.category:
        labels.append(f"category-{analysis.category.value}")
    if analysis.suggested_tags:
        labels.extend(analysis.suggested_tags)
    
    issue = IssueModel(
        title=analysis.title or f"Erro detectado: {log_model.message[:100]}",
        description=analysis.description or log_model.message,
        priority=priority,
        actual_behavior=log_model.message,
        environment_info=env_info,
        labels=labels,
        error_details=error_details,
        stack_trace=log_model.stack_trace,
        logs_snippet=log_model.raw_content[:1000],  # Primeiros 1000 chars
        impact_assessment=analysis.impact_description,
        suggested_fix=None,  # Será preenchido pelo agente drafting
        reporter_info={'source': 'Bug Finder', 'type': 'automated'},
        metadata={
            'analysis_confidence': analysis.confidence,
            'bug_category': analysis.category.value if analysis.category else None,
            'original_log_level': log_model.level.value
        }
    )
    
    return issue