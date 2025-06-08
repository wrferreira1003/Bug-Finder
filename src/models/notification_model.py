from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from .issue_model import IssueModel


class NotificationChannel(str, Enum):
    DISCORD = "discord"
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class DiscordNotification(BaseModel):
    webhook_url: str = Field(..., description="URL do webhook do Discord")
    content: Optional[str] = Field(None, description="Conteúdo da mensagem")
    username: Optional[str] = Field("Bug Finder Bot", description="Nome do bot")
    avatar_url: Optional[str] = Field(None, description="URL do avatar do bot")
    
    # Embed data
    embed_title: Optional[str] = Field(None, description="Título do embed")
    embed_description: Optional[str] = Field(None, description="Descrição do embed")
    embed_color: Optional[int] = Field(None, description="Cor do embed (hex)")
    embed_fields: List[Dict[str, Any]] = Field(default_factory=list, description="Campos do embed")
    
    def add_field(self, name: str, value: str, inline: bool = False) -> None:
        self.embed_fields.append({
            "name": name,
            "value": value,
            "inline": inline
        })
    
    def set_color_by_priority(self, priority: NotificationPriority) -> None:
        color_map = {
            NotificationPriority.LOW: 0x00ff00,      # Verde
            NotificationPriority.NORMAL: 0xffff00,   # Amarelo
            NotificationPriority.HIGH: 0xff8000,     # Laranja
            NotificationPriority.URGENT: 0xff0000    # Vermelho
        }
        self.embed_color = color_map.get(priority, 0x808080)  # Cinza padrão


class NotificationModel(BaseModel):
    id: str = Field(..., description="ID único da notificação")
    issue_id: str = Field(..., description="ID da issue relacionada")
    
    # Configuração da notificação
    channel: NotificationChannel = Field(..., description="Canal de notificação")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Prioridade da notificação")
    
    # Conteúdo
    title: str = Field(..., description="Título da notificação")
    message: str = Field(..., description="Mensagem da notificação")
    summary: Optional[str] = Field(None, description="Resumo da notificação")
    
    # Dados específicos do canal
    discord_data: Optional[DiscordNotification] = Field(None, description="Dados específicos do Discord")
    
    # Status e timestamps
    status: NotificationStatus = Field(NotificationStatus.PENDING, description="Status da notificação")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp de criação")
    sent_at: Optional[datetime] = Field(None, description="Timestamp de envio")
    
    # Dados de resposta
    response_data: Optional[Dict[str, Any]] = Field(None, description="Dados de resposta do canal")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    retry_count: int = Field(0, description="Número de tentativas de reenvio")
    max_retries: int = Field(3, description="Máximo de tentativas")
    
    def mark_as_sent(self, response_data: Optional[Dict[str, Any]] = None) -> None:
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
        if response_data:
            self.response_data = response_data
    
    def mark_as_failed(self, error_message: str) -> None:
        self.status = NotificationStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
    
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries and self.status == NotificationStatus.FAILED
    
    def mark_for_retry(self) -> None:
        if self.can_retry():
            self.status = NotificationStatus.RETRYING
    
    def is_urgent(self) -> bool:
        return self.priority == NotificationPriority.URGENT
    
    def get_notification_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "channel": self.channel,
            "priority": self.priority,
            "status": self.status,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "sent_at": self.sent_at
        }


def create_discord_notification_from_issue(issue: IssueModel, webhook_url: str) -> NotificationModel:
    from uuid import uuid4
    
    # Determinar prioridade baseada na análise do bug
    priority_map = {
        "critical": NotificationPriority.URGENT,
        "high": NotificationPriority.HIGH,
        "medium": NotificationPriority.NORMAL,
        "low": NotificationPriority.LOW
    }
    priority = priority_map.get(issue.bug_analysis.severity, NotificationPriority.NORMAL)
    
    # Criar notificação Discord
    description = issue.draft.description[:500] + "..." if len(issue.draft.description) > 500 else issue.draft.description
    if issue.github_issue_url:
        description += f"\n\n[🔗 Abrir Issue]({issue.github_issue_url})"

    discord_data = DiscordNotification(
        webhook_url=webhook_url,
        embed_title=f"🐛 Nova Issue Criada: {issue.draft.title}",
        embed_description=description
    )
    
    # Definir cor baseada na prioridade
    discord_data.set_color_by_priority(priority)
    
    # Adicionar campos informativos
    discord_data.add_field("Severidade", issue.bug_analysis.severity.value.title(), True)
    discord_data.add_field("Categoria", issue.bug_analysis.category.value.replace("_", " ").title(), True)
    discord_data.add_field("Prioridade", issue.draft.priority.value.title(), True)
    discord_data.add_field("Impacto", issue.bug_analysis.impact.value.replace("_", " ").title(), True)
    
    if issue.github_issue_url:
        discord_data.add_field("GitHub", f"[Ver Issue]({issue.github_issue_url})", False)
    
    # Criar modelo de notificação
    notification = NotificationModel(
        id=str(uuid4()),
        issue_id=issue.id,
        channel=NotificationChannel.DISCORD,
        priority=priority,
        title=f"Nova Issue: {issue.draft.title}",
        message=f"Uma nova issue foi criada automaticamente pelo Bug Finder: {issue.draft.title}",
        summary=f"Bug {issue.bug_analysis.severity.value} detectado e issue criada",
        discord_data=discord_data
    )
    
    return notification