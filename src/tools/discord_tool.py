import os
import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DiscordConfig:
    """Configuração para integração com Discord"""
    webhook_url: str
    channel_id: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3

class DiscordError(Exception):
    """Erro específico para operações com Discord"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}

class DiscordTool:
    """
    Ferramenta para envio de notificações via Discord.
    
    Suporta mensagens simples, embeds ricos e diferentes tipos
    de notificação para a equipe de desenvolvimento.
    """
    def __init__(self, config: DiscordConfig):
        self.config = config

    # Envia notificação de bug para o Discord
    def send_bug_notification(
        self, 
        issue_url: str, 
        issue_title: str, 
        severity: str,
        description: str,
        additional_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Envia notificação de bug para o Discord.
        
        Args:
            issue_url: URL da issue criada no GitHub
            issue_title: Título da issue
            severity: Criticidade do bug (high, medium, low)
            description: Descrição resumida do problema
            additional_info: Informações adicionais opcionais
            
        Returns:
            Dict com resultado da operação
        """
        
        # Cores baseadas na severidade
        color_map = {
            "high": 0xFF0000,    # Vermelho
            "medium": 0xFFA500,  # Laranja  
            "low": 0xFFFF00      # Amarelo
        }
        
        # Emojis baseados na severidade
        emoji_map = {
            "high": "🚨",
            "medium": "⚠️", 
            "low": "⚡"
        }
        
        embed = {
            "title": f"{emoji_map.get(severity, '🐛')} Novo Bug Detectado",
            "description": f"**{issue_title}**\n\n{description}",
            "color": color_map.get(severity, 0x808080),
            "fields": [
                {
                    "name": "Severidade",
                    "value": severity.upper(),
                    "inline": True
                },
                {
                    "name": "Issue GitHub",
                    "value": f"[Clique aqui para ver]({issue_url})",
                    "inline": True
                },
                {
                    "name": "Detectado em",
                    "value": datetime.now().strftime("%d/%m/%Y às %H:%M"),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Bug Finder System",
                "icon_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
            }
        }

        #Adicionar informações extras se fornecidas
        if additional_info:
            for key, value in additional_info.items():
                embed["fields"].append({
                    "name": key.replace('_', ' ').title(),
                    "value": str(value),
                    "inline": True
                })
        
        payload = {
            "embeds": [embed],
            "username": "Bug Finder Bot"
        }
        
        return self._send_webhook(payload)
    
    def send_simple_message(self, message: str, mention_users: List[str] = None) -> Dict[str, Any]:
        """
        Envia uma mensagem simples para o Discord.
        
        Args:
            message: Texto da mensagem
            mention_users: Lista de IDs de usuários para mencionar
            
        Returns:
            Dict com resultado da operação
        """
        content = message
        
        # Adicionar menções se especificadas
        if mention_users:
            mentions = " ".join([f"<@{user_id}>" for user_id in mention_users])
            content = f"{mentions}\n\n{message}"
        
        payload = {
            "content": content,
            "username": "Bug Finder Bot"
        }
        
        return self._send_webhook(payload)
    
    def send_status_update(self, status: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envia atualização de status do sistema.
        
        Args:
            status: Status atual (success, warning, error)
            details: Detalhes do status
            
        Returns:
            Dict com resultado da operação
        """
        
        status_config = {
            "success": {
                "color": 0x00FF00,
                "emoji": "✅",
                "title": "Sistema Funcionando"
            },
            "warning": {
                "color": 0xFFA500,
                "emoji": "⚠️",
                "title": "Atenção Necessária"
            },
            "error": {
                "color": 0xFF0000,
                "emoji": "❌",
                "title": "Erro no Sistema"
            }
        }
        
        config = status_config.get(status, status_config["warning"])
        
        embed = {
            "title": f"{config['emoji']} {config['title']}",
            "color": config["color"],
            "fields": [],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Bug Finder System Status"
            }
        }
        
        # Adicionar detalhes como campos
        for key, value in details.items():
            embed["fields"].append({
                "name": key.replace('_', ' ').title(),
                "value": str(value),
                "inline": True
            })
        
        payload = {
            "embeds": [embed],
            "username": "Bug Finder Bot"
        }
        
        return self._send_webhook(payload)
    
    def _send_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método interno para enviar webhook para o Discord.
        
        Args:
            payload: Dados da mensagem
            
        Returns:
            Dict com resultado da operação
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.config.retry_attempts):
            try:
                response = requests.post(
                    self.config.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 204:
                    return {
                        "success": True,
                        "message": "Mensagem enviada com sucesso para o Discord",
                        "attempt": attempt + 1
                    }
                elif response.status_code == 429:
                    # Rate limit - tentar novamente
                    retry_after = response.json().get("retry_after", 1)
                    if attempt < self.config.retry_attempts - 1:
                        import time
                        time.sleep(retry_after)
                        continue
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "message": f"Erro ao enviar mensagem: {response.text}",
                        "attempt": attempt + 1
                    }
                    
            except requests.exceptions.Timeout:
                if attempt < self.config.retry_attempts - 1:
                    continue
                return {
                    "success": False,
                    "error": "timeout",
                    "message": "Timeout ao enviar mensagem para Discord"
                }
                
            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Erro de rede: {str(e)}"
                }
        
        return {
            "success": False,
            "error": "max_retries_exceeded",
            "message": f"Falha após {self.config.retry_attempts} tentativas"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com o Discord enviando mensagem de teste.
        
        Returns:
            Dict com resultado do teste
        """
        test_message = {
            "content": "🧪 Teste de conexão do Bug Finder - Sistema operacional!",
            "username": "Bug Finder Bot"
        }
        
        result = self._send_webhook(test_message)
        
        if result["success"]:
            result["message"] = "Conexão com Discord funcionando corretamente"
        
        return result