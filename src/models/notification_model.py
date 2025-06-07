"""
Modelo para representar notificações enviadas via Discord.
Define estruturas para mensagens, embeds e resultados de envio.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class NotificationStatus(Enum):
    """Status possíveis da notificação"""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class NotificationType(Enum):
    """Tipos de notificação"""
    NEW_BUG = "new_bug"
    CRITICAL_BUG = "critical_bug"
    BUG_UPDATE = "bug_update"
    SYSTEM_ALERT = "system_alert"


class NotificationPriority(Enum):
    """Níveis de prioridade da notificação"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DiscordEmbed:
    """Estrutura de um embed do Discord"""
    title: str
    description: str
    color: int = 0xFF0000  # Vermelho por padrão para bugs
    url: Optional[str] = None
    timestamp: Optional[str] = None
    
    # Campos do embed
    fields: List[Dict[str, Any]] = None
    
    # Footer e thumbnail
    footer_text: Optional[str] = None
    footer_icon_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def add_field(self, name: str, value: str, inline: bool = False):
        """Adiciona um campo ao embed"""
        self.fields.append({
            "name": name,
            "value": value,
            "inline": inline
        })
    
    def to_discord_format(self) -> Dict[str, Any]:
        """Converte para formato aceito pelo Discord"""
        embed_data = {
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "timestamp": self.timestamp,
            "fields": self.fields
        }
        
        if self.url:
            embed_data["url"] = self.url
        
        if self.footer_text:
            embed_data["footer"] = {"text": self.footer_text}
            if self.footer_icon_url:
                embed_data["footer"]["icon_url"] = self.footer_icon_url
        
        if self.thumbnail_url:
            embed_data["thumbnail"] = {"url": self.thumbnail_url}
        
        return embed_data


@dataclass
class DiscordMessage:
    """Estrutura de uma mensagem do Discord"""
    content: Optional[str] = None
    embeds: List[DiscordEmbed] = None
    
    # Configurações de menção
    mentions: List[str] = None  # IDs de usuários para mencionar
    role_mentions: List[str] = None  # IDs de roles para mencionar
    
    # Configurações avançadas
    tts: bool = False
    allowed_mentions: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.embeds is None:
            self.embeds = []
        if self.mentions is None:
            self.mentions = []
        if self.role_mentions is None:
            self.role_mentions = []
    
    def add_embed(self, embed: DiscordEmbed):
        """Adiciona um embed à mensagem"""
        self.embeds.append(embed)
    
    def add_mention(self, user_id: str):
        """Adiciona menção de usuário"""
        self.mentions.append(user_id)
        if self.content:
            self.content += f" <@{user_id}>"
        else:
            self.content = f"<@{user_id}>"
    
    def to_discord_payload(self) -> Dict[str, Any]:
        """Converte para payload do Discord webhook"""
        payload = {}
        
        if self.content:
            payload["content"] = self.content
        
        if self.embeds:
            payload["embeds"] = [embed.to_discord_format() for embed in self.embeds]
        
        if self.tts:
            payload["tts"] = self.tts
        
        if self.allowed_mentions:
            payload["allowed_mentions"] = self.allowed_mentions
        
        return payload


@dataclass
class NotificationAttempt:
    """Registro de uma tentativa de notificação"""
    attempt_number: int
    timestamp: str
    status: NotificationStatus
    response_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class NotificationResult:
    """Resultado completo do envio de notificação"""
    # Status da operação
    status: NotificationStatus
    success: bool
    
    # Dados da notificação
    notification_type: NotificationType
    priority: NotificationPriority
    
    # Dados do Discord
    channel_id: Optional[str] = None
    message_id: Optional[str] = None
    webhook_url: Optional[str] = None
    
    # Histórico de tentativas
    attempts: List[NotificationAttempt] = None
    
    # Metadados
    notifier_agent: str = "IssueNotificatorAgent"
    notification_timestamp: str = None
    total_attempts: int = 0
    
    # Dados da mensagem enviada
    message_content: Optional[str] = None
    embed_count: int = 0
    
    # Informações de erro
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []
        if self.notification_timestamp is None:
            self.notification_timestamp = datetime.now().isoformat()
        self.success = self.status == NotificationStatus.SENT
    
    def add_attempt(self, attempt: NotificationAttempt):
        """Adiciona uma nova tentativa ao histórico"""
        self.attempts.append(attempt)
        self.total_attempts = len(self.attempts)
        self.status = attempt.status
        
        if attempt.status == NotificationStatus.SENT:
            self.success = True
        elif attempt.status == NotificationStatus.FAILED:
            self.error_message = attempt.error_message
    
    def get_notification_summary(self) -> str:
        """Retorna um resumo da notificação"""
        if self.success:
            return f"✅ Notificação enviada com sucesso (ID: {self.message_id})"
        else:
            return f"❌ Falha no envio: {self.error_message}"
    
    def is_retryable(self) -> bool:
        """Verifica se a notificação pode ser tentada novamente"""
        retryable_statuses = [
            NotificationStatus.RATE_LIMITED,
            NotificationStatus.FAILED
        ]
        return self.status in retryable_statuses and self.total_attempts < 3


@dataclass
class NotificationTemplate:
    """Template para diferentes tipos de notificação"""
    notification_type: NotificationType
    title_template: str
    description_template: str
    color: int
    priority: NotificationPriority = NotificationPriority.MEDIUM
    
    # Configurações de menção
    mention_roles: List[str] = None
    mention_users: List[str] = None
    
    def __post_init__(self):
        if self.mention_roles is None:
            self.mention_roles = []
        if self.mention_users is None:
            self.mention_users = []
    
    def create_message(self, context: Dict[str, Any]) -> DiscordMessage:
        """Cria uma mensagem baseada no template"""
        # Substitui placeholders no template
        title = self.title_template.format(**context)
        description = self.description_template.format(**context)
        
        # Cria embed
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=self.color
        )
        
        # Adiciona URL se disponível
        if "issue_url" in context:
            embed.url = context["issue_url"]
        
        # Cria mensagem
        message = DiscordMessage()
        message.add_embed(embed)
        
        # Adiciona menções
        for role_id in self.mention_roles:
            if self.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
                message.content = (message.content or "") + f" <@&{role_id}>"
        
        return message


@dataclass
class NotificationConfig:
    """Configuração para notificações"""
    # Configurações do Discord
    webhook_url: str
    default_channel_id: str
    
    # Configurações de retry
    max_attempts: int = 3
    retry_delay_seconds: int = 30
    
    # Templates de notificação
    templates: Dict[NotificationType, NotificationTemplate] = None
    
    # Configurações de rate limiting
    respect_rate_limits: bool = True
    rate_limit_delay: int = 60
    
    def __post_init__(self):
        if self.templates is None:
            self.templates = self._create_default_templates()
    
    def _create_default_templates(self) -> Dict[NotificationType, NotificationTemplate]:
        """Cria templates padrão"""
        return {
            NotificationType.NEW_BUG: NotificationTemplate(
                notification_type=NotificationType.NEW_BUG,
                title_template="🐛 Novo Bug Detectado: {title}",
                description_template="**Criticidade:** {criticality}\n**Log:** {log_summary}\n\n[Ver Issue Completa]({issue_url})",
                color=0xFF6B6B,  # Vermelho claro
                priority=NotificationPriority.MEDIUM
            ),
            NotificationType.CRITICAL_BUG: NotificationTemplate(
                notification_type=NotificationType.CRITICAL_BUG,
                title_template="🚨 BUG CRÍTICO: {title}",
                description_template="**⚠️ ATENÇÃO: Bug de alta criticidade detectado!**\n\n**Log:** {log_summary}\n\n[RESOLVER IMEDIATAMENTE]({issue_url})",
                color=0xFF0000,  # Vermelho
                priority=NotificationPriority.CRITICAL
            )
        }


@dataclass
class NotificationMetrics:
    """Métricas de notificações"""
    total_notifications: int = 0
    successful_notifications: int = 0
    failed_notifications: int = 0
    rate_limited_attempts: int = 0
    average_send_time: float = 0.0
    
    # Métricas por tipo
    notifications_by_type: Dict[NotificationType, int] = None
    
    def __post_init__(self):
        if self.notifications_by_type is None:
            self.notifications_by_type = {}
    
    def success_rate(self) -> float:
        """Taxa de sucesso das notificações"""
        if self.total_notifications == 0:
            return 0.0
        return (self.successful_notifications / self.total_notifications) * 100
    
    def update_metrics(self, result: NotificationResult):
        """Atualiza métricas com novo resultado"""
        self.total_notifications += 1
        
        if result.success:
            self.successful_notifications += 1
        else:
            self.failed_notifications += 1
        
        # Conta por tipo
        notification_type = result.notification_type
        self.notifications_by_type[notification_type] = (
            self.notifications_by_type.get(notification_type, 0) + 1
        )
        
        # Conta rate limits
        rate_limited = sum(
            1 for attempt in result.attempts 
            if attempt.status == NotificationStatus.RATE_LIMITED
        )
        self.rate_limited_attempts += rate_limited