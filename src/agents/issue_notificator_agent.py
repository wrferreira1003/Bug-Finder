"""
IssueNotificatorAgent - Agente de Notificação de Issues

Localização: src/agents/issue_notificator_agent.py

Responsabilidades:
- Notificar sobre issues criadas
- Enviar mensagens para canais específicos (Slack, Teams, etc.)
- Formatar notificações conforme o canal
- Controlar filtros de notificação (criticidade, componente, etc.)

Este agente atua como um "comunicador", garantindo que as equipes
relevantes sejam notificadas das issues críticas através de diversos canais.
"""

import json
import logging
from typing import Dict, Any, Protocol, List, Optional
from datetime import datetime

from ..models.issue_model import IssueModel, IssuePriority
from ..models.creation_model import IssueCreationResult, CreationStatus, GitHubIssueData
from ..models.notification_model import NotificationResult, NotificationStatus, DiscordMessage
from ..tools.discord_tool import DiscordTool, DiscordError
from ..config.settings import get_settings


class IssueNotificatorAgent:
    """
    Agente responsável por notificar a equipe sobre issues criadas.
    
    Este agente não depende de IA, focando na integração com
    Discord para enviar notificações formatadas e informativas.
    """
    
    def __init__(self, discord_tool: DiscordTool):
        """
        Inicializa o agente notificador.
        
        Args:
            discord_tool: Instância da ferramenta do Discord
        """
        self.discord_tool = discord_tool
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Configurações de notificação
        self.notification_config = {
            'default_channel': self.settings.get('discord_default_channel'),
            'high_priority_channel': self.settings.get('discord_high_priority_channel'),
            'mention_roles': self.settings.get('discord_mention_roles', {}),
            'max_retries': 3,
            'retry_delay': 5.0,
            'enable_embeds': True,
            'include_thumbnails': True
        }
        
        # Templates de mensagem por prioridade
        self.message_templates = {
            'high': {
                'color': 0xFF0000,  # Vermelho
                'emoji': '🚨',
                'urgency_text': 'CRÍTICO',
                'mention_role': self.notification_config['mention_roles'].get('critical', '@here')
            },
            'medium': {
                'color': 0xFF8C00,  # Laranja
                'emoji': '⚠️',
                'urgency_text': 'IMPORTANTE',
                'mention_role': self.notification_config['mention_roles'].get('medium', '')
            },
            'low': {
                'color': 0xFFD700,  # Amarelo
                'emoji': '💡',
                'urgency_text': 'INFORMATIVO',
                'mention_role': ''
            }
        }
    
    def notify_issue_created(self, creation_result: IssueCreationResult, issue_draft: IssueModel) -> NotificationResult:
        """
        Notifica a equipe sobre uma issue criada com sucesso.
        
        Args:
            creation_result: Resultado da criação da issue
            issue_draft: Rascunho original da issue
            
        Returns:
            Resultado da notificação
        """
        try:
            self.logger.info(f"Enviando notificação para Discord sobre issue: {creation_result.github_issue.url}")
            
            # Verifica se a issue foi criada com sucesso
            if creation_result.status != CreationStatus.SUCCESS:
                return self._notify_creation_failure(creation_result, issue_draft)
            
            # Preparação da mensagem
            discord_message = self._prepare_success_message(creation_result, issue_draft)
            
            # Determinação do canal apropriado
            target_channel = self._determine_target_channel(issue_draft)
            
            # Envio da notificação
            sent_message = self._send_discord_notification(discord_message, target_channel)
            
            # Criação do resultado de sucesso
            notification_result = self._create_success_notification_result(
                creation_result, issue_draft, sent_message, target_channel
            )
            
            self.logger.info(f"Notificação enviada com sucesso para canal: {target_channel}")
            
            return notification_result
            
        except DiscordError as e:
            self.logger.error(f"Erro do Discord: {str(e)}")
            return self._create_discord_error_result(creation_result, issue_draft, e)
        
        except Exception as e:
            self.logger.error(f"Erro inesperado durante notificação: {str(e)}")
            return self._create_generic_error_result(creation_result, issue_draft, e)
    
    def notify_creation_failure(self, creation_result: IssueCreationResult, issue_draft: IssueModel) -> NotificationResult:
        """
        Notifica sobre falha na criação de issue.
        
        Args:
            creation_result: Resultado da criação que falhou
            issue_draft: Rascunho que falhou
            
        Returns:
            Resultado da notificação de falha
        """
        try:
            self.logger.info("Enviando notificação de falha na criação de issue")
            
            # Preparação da mensagem de falha
            discord_message = self._prepare_failure_message(creation_result, issue_draft)
            
            # Canal para notificações de erro (pode ser diferente)
            error_channel = self.settings.get('discord_error_channel', self.notification_config['default_channel'])
            
            # Envio da notificação
            sent_message = self._send_discord_notification(discord_message, error_channel)
            
            # Criação do resultado
            notification_result = self._create_failure_notification_result(
                creation_result, issue_draft, sent_message, error_channel
            )
            
            self.logger.info(f"Notificação de falha enviada para canal: {error_channel}")
            
            return notification_result
            
        except Exception as e:
            self.logger.error(f"Erro ao notificar falha: {str(e)}")
            return self._create_generic_error_result(creation_result, issue_draft, e)
    
    def _prepare_success_message(self, creation_result: IssueCreationResult, issue_draft: IssueModel) -> DiscordMessage:
        """
        Prepara mensagem de sucesso para o Discord.
        """
        github_issue = creation_result.github_issue
        priority = issue_draft.priority.value.lower()
        template = self.message_templates.get(priority, self.message_templates['medium'])
        
        # Texto principal da mensagem
        main_text = f"{template['mention_role']} {template['emoji']} **Nova Issue Detectada - {template['urgency_text']}**"
        
        # Criação do embed rico
        embed = {
            'title': f"{template['emoji']} {github_issue.title}",
            'url': github_issue.url,
            'description': self._create_issue_summary(issue_draft),
            'color': template['color'],
            'fields': self._create_embed_fields(creation_result, issue_draft),
            'footer': {
                'text': f"BugFinder • Issue #{github_issue.number}",
                'icon_url': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Adiciona thumbnail se habilitado
        if self.notification_config['include_thumbnails']:
            embed['thumbnail'] = {
                'url': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
            }
        
        return DiscordMessage(
            content=main_text,
            embed=embed if self.notification_config['enable_embeds'] else None,
            username='BugFinder Bot',
            avatar_url='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
        )
    
    def _create_issue_summary(self, issue_draft: IssueModel) -> str:
        """
        Cria resumo da issue para o embed.
        """
        # Extrai primeiras linhas da descrição
        description_lines = issue_draft.description.split('\n')
        summary_lines = []
        
        for line in description_lines:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith('#') and not clean_line.startswith('*'):
                summary_lines.append(clean_line)
                if len(summary_lines) >= 2:  # Máximo 2 linhas
                    break
        
        summary = ' '.join(summary_lines)
        
        # Limita o tamanho do resumo
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        return summary or "Issue detectada automaticamente pelos logs do sistema."
    
    def _create_embed_fields(self, creation_result: IssueCreationResult, issue_draft: IssueModel) -> List[Dict[str, Any]]:
        """
        Cria campos do embed com informações da issue.
        """
        fields = []
        
        # Campo de prioridade
        priority_emoji = {
            'high': '🔴',
            'medium': '🟡', 
            'low': '🟢'
        }
        priority = issue_draft.priority.value.lower()
        fields.append({
            'name': '🎯 Prioridade',
            'value': f"{priority_emoji.get(priority, '⚪')} {priority.title()}",
            'inline': True
        })
        
        # Campo de labels
        if issue_draft.labels:
            labels_text = ', '.join([f"`{label}`" for label in issue_draft.labels[:3]])
            if len(issue_draft.labels) > 3:
                labels_text += f" +{len(issue_draft.labels) - 3} mais"
            fields.append({
                'name': '🏷️ Labels',
                'value': labels_text,
                'inline': True
            })
        
        # Campo de assignees
        if issue_draft.assignees:
            assignees_text = ', '.join([f"@{assignee}" for assignee in issue_draft.assignees[:2]])
            if len(issue_draft.assignees) > 2:
                assignees_text += f" +{len(issue_draft.assignees) - 2} mais"
            fields.append({
                'name': '👥 Responsáveis',
                'value': assignees_text,
                'inline': True
            })
        
        # Campo de informações técnicas
        technical_info = []
        if hasattr(issue_draft, 'source_log_id') and issue_draft.source_log_id:
            technical_info.append(f"Log ID: `{issue_draft.source_log_id[:8]}...`")
        
        env_info = issue_draft.environment_info
        if env_info and 'component' in env_info:
            technical_info.append(f"Componente: `{env_info['component']}`")
        
        if technical_info:
            fields.append({
                'name': '🔧 Detalhes Técnicos',
                'value': '\n'.join(technical_info),
                'inline': False
            })
        
        # Campo de ações rápidas
        actions = [
            f"[📋 Ver Issue]({creation_result.github_issue.url})",
            f"[🗂️ Repositório]({creation_result.github_issue.url.split('/issues/')[0]})"
        ]
        
        fields.append({
            'name': '⚡ Ações Rápidas',
            'value': ' • '.join(actions),
            'inline': False
        })
        
        return fields
    
    def _prepare_failure_message(self, creation_result: IssueCreationResult, issue_draft: IssueModel) -> DiscordMessage:
        """
        Prepara mensagem de falha na criação.
        """
        # Emoji e cor para erro
        error_emoji = '❌'
        error_color = 0xFF0000
        
        main_text = f"@here {error_emoji} **Falha na Criação de Issue**"
        
        # Embed de erro
        embed = {
            'title': f"{error_emoji} Erro ao Criar Issue",
            'description': f"**Título da Issue**: {issue_draft.title}\n**Erro**: {creation_result.message}",
            'color': error_color,
            'fields': [
                {
                    'name': '📊 Status',
                    'value': creation_result.status.value,
                    'inline': True
                },
                {
                    'name': '⏰ Timestamp',
                    'value': creation_result.created_at,
                    'inline': True
                }
            ],
            'footer': {
                'text': 'BugFinder • Requer Atenção Manual',
                'icon_url': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Adiciona detalhes do erro se disponíveis
        if creation_result.error_details:
            error_details = json.dumps(creation_result.error_details, indent=2)
            if len(error_details) > 1000:
                error_details = error_details[:997] + "..."
            
            embed['fields'].append({
                'name': '🔍 Detalhes do Erro',
                'value': f"```json\n{error_details}\n```",
                'inline': False
            })
        
        return DiscordMessage(
            content=main_text,
            embed=embed,
            username='BugFinder Bot',
            avatar_url='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
        )
    
    def _determine_target_channel(self, issue_draft: IssueModel) -> str:
        """
        Determina o canal apropriado baseado na prioridade da issue.
        """
        if issue_draft.priority == IssuePriority.HIGH:
            return (self.notification_config['high_priority_channel'] or 
                   self.notification_config['default_channel'])
        
        return self.notification_config['default_channel']
    
    def _send_discord_notification(self, message: DiscordMessage, channel: str) -> Dict[str, Any]:
        """
        Envia notificação para o Discord.
        """
        if not channel:
            raise DiscordError("Canal não configurado")
        
        return self.discord_tool.send_message(
            channel=channel,
            content=message.content,
            embed=message.embed,
            username=message.username,
            avatar_url=message.avatar_url
        )
    
    def _create_success_notification_result(self, creation_result: IssueCreationResult, 
                                          issue_draft: IssueModel, sent_message: Dict[str, Any], 
                                          channel: str) -> NotificationResult:
        """
        Cria resultado de notificação bem-sucedida.
        """
        return NotificationResult(
            status=NotificationStatus.SUCCESS,
            issue_creation_id=creation_result.issue_draft_id,
            github_issue_url=creation_result.github_issue.url,
            discord_message_id=sent_message.get('id'),
            discord_channel=channel,
            notification_timestamp=datetime.now().isoformat(),
            message="Notificação enviada com sucesso",
            details={
                'channel_used': channel,
                'message_type': 'success',
                'priority': issue_draft.priority.value,
                'embed_sent': self.notification_config['enable_embeds'],
                'notification_agent': 'IssueNotificatorAgent'
            }
        )
    
    def _create_failure_notification_result(self, creation_result: IssueCreationResult,
                                          issue_draft: IssueModel, sent_message: Dict[str, Any],
                                          channel: str) -> NotificationResult:
        """
        Cria resultado de notificação de falha.
        """
        return NotificationResult(
            status=NotificationStatus.SUCCESS,  # Notificação foi enviada, mesmo sendo sobre falha
            issue_creation_id=creation_result.issue_draft_id,
            github_issue_url=None,
            discord_message_id=sent_message.get('id'),
            discord_channel=channel,
            notification_timestamp=datetime.now().isoformat(),
            message="Notificação de falha enviada com sucesso",
            details={
                'channel_used': channel,
                'message_type': 'failure',
                'original_error': creation_result.message,
                'notification_agent': 'IssueNotificatorAgent'
            }
        )
    
    def _create_discord_error_result(self, creation_result: IssueCreationResult,
                                   issue_draft: IssueModel, error: DiscordError) -> NotificationResult:
        """
        Cria resultado de erro do Discord.
        """
        return NotificationResult(
            status=NotificationStatus.DISCORD_ERROR,
            issue_creation_id=creation_result.issue_draft_id,
            github_issue_url=creation_result.github_issue.url if creation_result.github_issue else None,
            discord_message_id=None,
            discord_channel=None,
            notification_timestamp=datetime.now().isoformat(),
            message=f"Erro do Discord: {str(error)}",
            error_details={
                'discord_error': str(error),
                'error_type': type(error).__name__
            }
        )
    
    def _create_generic_error_result(self, creation_result: IssueCreationResult,
                                   issue_draft: IssueModel, error: Exception) -> NotificationResult:
        """
        Cria resultado de erro genérico.
        """
        return NotificationResult(
            status=NotificationStatus.UNKNOWN_ERROR,
            issue_creation_id=creation_result.issue_draft_id,
            github_issue_url=creation_result.github_issue.url if creation_result.github_issue else None,
            discord_message_id=None,
            discord_channel=None,
            notification_timestamp=datetime.now().isoformat(),
            message=f"Erro inesperado: {str(error)}",
            error_details={
                'error': str(error),
                'error_type': type(error).__name__
            }
        )
    
    def _notify_creation_failure(self, creation_result: IssueCreationResult, issue_draft: IssueModel) -> NotificationResult:
        """
        Método auxiliar para notificar falhas na criação.
        """
        return self.notify_creation_failure(creation_result, issue_draft)
    
    def retry_failed_notification(self, notification_result: NotificationResult, 
                                 creation_result: IssueCreationResult, 
                                 issue_draft: IssueModel) -> NotificationResult:
        """
        Tenta reenviar uma notificação que falhou.
        
        Args:
            notification_result: Resultado anterior que falhou
            creation_result: Resultado da criação da issue
            issue_draft: Rascunho da issue
            
        Returns:
            Novo resultado da tentativa
        """
        self.logger.info("Tentando reenviar notificação após falha")
        
        # Se foi erro de configuração, não tenta novamente
        if 'configuração' in notification_result.message.lower():
            self.logger.warning("Não reenviando notificação com erro de configuração")
            return notification_result
        
        # Para outros tipos de erro, tenta novamente
        return self.notify_issue_created(creation_result, issue_draft)
    
    def get_notification_summary(self, notification_result: NotificationResult) -> Dict[str, Any]:
        """
        Gera resumo da notificação.
        """
        return {
            'status': notification_result.status.value,
            'success': notification_result.status == NotificationStatus.SUCCESS,
            'channel': notification_result.discord_channel,
            'message_id': notification_result.discord_message_id,
            'timestamp': notification_result.notification_timestamp,
            'github_issue': notification_result.github_issue_url,
            'details': notification_result.details or {}
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente.
        """
        return {
            'name': 'IssueNotificatorAgent',
            'version': '1.0.0',
            'description': 'Agente responsável por notificar equipe sobre issues criadas',
            'capabilities': [
                'Envio de notificações Discord',
                'Formatação de mensagens ricas (embeds)',
                'Personalização por prioridade',
                'Seleção de canal apropriado',
                'Notificação de falhas',
                'Retry de envios falhados',
                'Resumos de notificação'
            ],
            'input_formats': ['IssueCreationResult', 'IssueModel'],
            'output_format': 'NotificationResult',
            'requires_llm': False,
            'external_dependencies': ['Discord API'],
            'notification_config': {
                'default_channel': self.notification_config['default_channel'],
                'high_priority_channel': self.notification_config['high_priority_channel'],
                'embeds_enabled': self.notification_config['enable_embeds'],
                'max_retries': self.notification_config['max_retries']
            }
        }


# Exemplo de uso e testes
if __name__ == "__main__":
    from ..models.issue_model import IssueModel, IssuePriority
    from ..models.creation_model import IssueCreationResult, CreationStatus, GitHubIssueData
    from ..tools.discord_tool import MockDiscordTool
    
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Cria agente com ferramenta mock do Discord
    mock_discord = MockDiscordTool()
    agent = IssueNotificatorAgent(mock_discord)
    
    # Teste: Notificação de issue criada com sucesso
    test_github_issue = GitHubIssueData(
        number=123,
        title="Fix database connection timeout in UserService",
        url="https://github.com/empresa/repo/issues/123",
        state="open",
        labels=['bug', 'high-priority', 'database'],
        assignees=['dev-team'],
        created_at=datetime.now().isoformat()
    )
    
    success_result = IssueCreationResult(
        status=CreationStatus.SUCCESS,
        github_issue=test_github_issue,
        issue_draft_id="draft-123",
        created_at=datetime.now().isoformat(),
        message="Issue criada com sucesso",
        details={'repository': 'empresa/repo'}
    )
    
    test_draft = IssueModel(
        title="Fix database connection timeout in UserService",
        description="""## Bug Report
        
### Summary
Database connection timeouts during peak hours.

### Impact
Users cannot access the application.
""",
        labels=["bug", "automated"],
        priority=IssuePriority.HIGH,
        assignees=['dev-team'],
        environment_info={
            'component': 'UserService',
            'service_version': 'v2.1.4'
        }
    )
    
    print("Teste - Notificação de Sucesso:")
    notification_result = agent.notify_issue_created(success_result, test_draft)
    print(f"Status: {notification_result.status}")
    print(f"Mensagem: {notification_result.message}")
    print(f"Canal: {notification_result.discord_channel}")
    
    # Resumo da notificação
    summary = agent.get_notification_summary(notification_result)
    print(f"Resumo: {json.dumps(summary, indent=2)}")
    
    # Teste: Notificação de falha
    failure_result = IssueCreationResult(
        status=CreationStatus.GITHUB_ERROR,
        github_issue=None,
        issue_draft_id="draft-456",
        created_at=datetime.now().isoformat(),
        message="GitHub API rate limit exceeded",
        error_details={'api_error': 'Rate limit exceeded'}
    )
    
    print("\nTeste - Notificação de Falha:")
    failure_notification = agent.notify_creation_failure(failure_result, test_draft)
    print(f"Status: {failure_notification.status}")
    print(f"Mensagem: {failure_notification.message}")
    
    # Info do agente
    print(f"\nInfo do Agente:")
    print(json.dumps(agent.get_agent_info(), indent=2))