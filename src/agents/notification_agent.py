import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

import google.generativeai as genai

from ..models import (
    IssueModel, NotificationModel, NotificationChannel, 
    NotificationPriority, create_discord_notification_from_issue
)
from ..config import get_settings, get_prompt
from ..tools import DiscordTool


class NotificationAgent:
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Ensure API key is available
        if not self.settings.google_ai_api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required but not found in environment")
        
        # Configure Google AI with explicit API key
        genai.configure(api_key=self.settings.google_ai_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_model)
        
        # Generation config
        self.generation_config = {
            "temperature": self.settings.gemini_temperature,
            "max_output_tokens": self.settings.gemini_max_tokens,
        }
        
        # Discord tool
        self.discord_tool = DiscordTool()
    
    def send_issue_notification(self, issue: IssueModel) -> bool:
        """
        Envia notificação sobre a issue criada.
        Decide automaticamente quais canais usar e cria mensagens apropriadas.
        """
        try:
            self.logger.info(f"Starting notification process for issue: {issue.id}")
            
            # Verificar se notificações estão habilitadas
            if not self.settings.enable_discord_notifications:
                self.logger.info("Discord notifications are disabled")
                return True
            
            # Verificar se é um caso que precisa notificação
            if not self._should_notify(issue):
                self.logger.info("Issue doesn't meet notification criteria")
                return True
            
            # Criar e enviar notificação Discord
            if self.settings.discord_webhook_url:
                discord_sent = self._send_discord_notification(issue)
                if discord_sent:
                    self.logger.info("Discord notification sent successfully")
                else:
                    self.logger.error("Failed to send Discord notification")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in notification process: {str(e)}")
            return False
    
    def _should_notify(self, issue: IssueModel) -> bool:
        """Determina se a issue deve gerar notificação."""
        # Sempre notificar para bugs críticos e altos
        if issue.bug_analysis.severity.value in ["critical", "high"]:
            return True
        
        # Notificar para bugs médios se tiver alta confiança
        if (issue.bug_analysis.severity.value == "medium" and 
            issue.bug_analysis.confidence_score >= 0.8):
            return True
        
        # Notificar se requer atenção imediata
        if issue.bug_analysis.requires_immediate_attention():
            return True
        
        # Não notificar para bugs baixos por padrão
        return False
    
    def _send_discord_notification(self, issue: IssueModel) -> bool:
        """Cria e envia notificação personalizada para Discord."""
        try:
            # Gerar conteúdo da notificação usando IA
            notification_content = self._generate_notification_content(issue)
            if not notification_content:
                self.logger.error("Failed to generate notification content")
                return False
            
            # Criar notificação Discord
            notification = create_discord_notification_from_issue(
                issue, 
                self.settings.discord_webhook_url
            )
            
            # Personalizar com conteúdo gerado pela IA
            if notification.discord_data:
                notification.discord_data.embed_title = notification_content.get("title", notification.discord_data.embed_title)
                notification.discord_data.embed_description = notification_content.get("message", notification.discord_data.embed_description)
                
                # Adicionar campos personalizados
                custom_fields = notification_content.get("fields", [])
                for field in custom_fields:
                    notification.discord_data.add_field(
                        field.get("name", ""),
                        field.get("value", ""),
                        field.get("inline", False)
                    )
            
            # Tentar enviar com retry
            max_attempts = self.settings.notification_retry_attempts
            
            for attempt in range(max_attempts):
                self.logger.info(f"Discord notification attempt {attempt + 1}/{max_attempts}")
                
                if self.discord_tool.send_notification(notification):
                    issue.mark_as_notified(notification.response_data.get("message_id", "unknown"))
                    return True
                
                # Se falhou mas pode tentar novamente
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(self.settings.notification_retry_delay_seconds)
                    notification.mark_for_retry()
                    continue
                else:
                    break
            
            self.logger.error("All Discord notification attempts failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending Discord notification: {e}")
            return False
    
    def _generate_notification_content(self, issue: IssueModel) -> Optional[Dict[str, Any]]:
        """Gera conteúdo personalizado da notificação usando IA."""
        try:
            # Preparar contexto para geração de notificação
            issue_summary = f"""**Título:** {issue.draft.title}
**Descrição:** {issue.draft.description[:300] + '...' if len(issue.draft.description) > 300 else issue.draft.description}
**Severidade:** {issue.bug_analysis.severity.value}
**Categoria:** {issue.bug_analysis.category.value}
**Prioridade:** {issue.draft.priority.value}
**GitHub URL:** {issue.github_issue_url or 'Pendente'}
**Confiança:** {issue.bug_analysis.confidence_score}
**Impacto:** {issue.bug_analysis.impact.value}"""
            
            bug_analysis = f"""**É Crítico:** {'Sim' if issue.bug_analysis.requires_immediate_attention() else 'Não'}
**Componentes Afetados:** {', '.join(issue.bug_analysis.affected_components)}
**Score de Prioridade:** {issue.bug_analysis.priority_score}
**Hipótese da Causa Raiz:** {issue.bug_analysis.root_cause_hypothesis}"""
            
            context = {
                "issue_summary": issue_summary,
                "bug_analysis": bug_analysis
            }
            
            # Gerar prompt e solicitar conteúdo
            prompt = get_prompt("issue_notificator", **context)
            
            self.logger.debug("Sending notification content generation request to AI")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse da resposta
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            result = json.loads(response_text)
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse notification content response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error generating notification content: {e}")
            return None
    
    def send_test_notification(self) -> bool:
        """Envia uma notificação de teste para verificar conectividade."""
        try:
            if not self.settings.discord_webhook_url:
                self.logger.error("No Discord webhook URL configured")
                return False
            
            return self.discord_tool.test_webhook(self.settings.discord_webhook_url)
            
        except Exception as e:
            self.logger.error(f"Error sending test notification: {e}")
            return False
    
    def send_system_notification(self, title: str, message: str, 
                                priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """Envia notificação de sistema (não relacionada a bugs)."""
        try:
            if not self.settings.enable_discord_notifications or not self.settings.discord_webhook_url:
                return False
            
            # Determinar cor baseada na prioridade
            color_map = {
                NotificationPriority.LOW: 0x00ff00,      # Verde
                NotificationPriority.NORMAL: 0x0099ff,   # Azul
                NotificationPriority.HIGH: 0xff8000,     # Laranja
                NotificationPriority.URGENT: 0xff0000    # Vermelho
            }
            
            color = color_map.get(priority, 0x808080)
            
            return self.discord_tool.send_embed_message(
                title=f"🔔 {title}",
                description=message,
                color=color,
                fields=[
                    {"name": "Sistema", "value": "Bug Finder", "inline": True},
                    {"name": "Prioridade", "value": priority.value.title(), "inline": True},
                    {"name": "Timestamp", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
                ],
                webhook_url=self.settings.discord_webhook_url,
                username="Bug Finder System"
            )
            
        except Exception as e:
            self.logger.error(f"Error sending system notification: {e}")
            return False
    
    def send_error_notification(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Envia notificação de erro do sistema."""
        try:
            title = "❌ Erro no Bug Finder"
            
            # Preparar mensagem com contexto
            message = f"Ocorreu um erro no sistema Bug Finder:\n\n**Erro:** {error_message}"
            
            if context:
                message += f"\n\n**Contexto:**\n"
                for key, value in context.items():
                    message += f"- {key}: `{value}`\n"
            
            return self.send_system_notification(
                title=title,
                message=message,
                priority=NotificationPriority.HIGH
            )
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
    
    def get_notification_status(self) -> Dict[str, Any]:
        """Retorna status das configurações de notificação."""
        return {
            "discord_enabled": self.settings.enable_discord_notifications,
            "discord_configured": bool(self.settings.discord_webhook_url),
            "retry_attempts": self.settings.notification_retry_attempts,
            "retry_delay": self.settings.notification_retry_delay_seconds,
            "rate_limit": self.settings.discord_rate_limit_per_minute
        }