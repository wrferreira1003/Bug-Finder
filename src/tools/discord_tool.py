import os
import requests
import time
from typing import Optional, Dict, Any, List
import logging

from ..models.notification_model import DiscordNotification, NotificationModel, NotificationStatus


class DiscordTool:
    def __init__(self, default_webhook_url: Optional[str] = None):
        self.default_webhook_url = default_webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.rate_limit_per_minute = 30
        self.rate_limit_window = 60  # seconds
        self.request_timestamps = []
    
    def _check_rate_limit(self) -> bool:
        current_time = time.time()
        
        # Remove timestamps older than the window
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < self.rate_limit_window
        ]
        
        # Check if we're within the rate limit
        if len(self.request_timestamps) >= self.rate_limit_per_minute:
            self.logger.warning("Discord rate limit reached, waiting...")
            return False
        
        self.request_timestamps.append(current_time)
        return True
    
    def _wait_for_rate_limit(self) -> None:
        if not self._check_rate_limit():
            # Wait until the oldest request is outside the window
            if self.request_timestamps:
                oldest_request = min(self.request_timestamps)
                wait_time = self.rate_limit_window - (time.time() - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time + 1)  # Add 1 second buffer
    
    def send_notification(self, notification: NotificationModel) -> bool:
        if not notification.discord_data:
            self.logger.error("No Discord data provided in notification")
            return False
        
        return self.send_discord_message(notification.discord_data, notification)
    
    def send_discord_message(self, discord_data: DiscordNotification, 
                           notification: Optional[NotificationModel] = None) -> bool:
        webhook_url = discord_data.webhook_url or self.default_webhook_url
        
        if not webhook_url:
            error_msg = "No Discord webhook URL provided"
            self.logger.error(error_msg)
            if notification:
                notification.mark_as_failed(error_msg)
            return False
        
        # Check rate limiting
        self._wait_for_rate_limit()
        
        try:
            # Prepare payload
            payload = self._build_payload(discord_data)
            
            self.logger.info(f"Sending Discord notification: {discord_data.embed_title or 'Message'}")
            
            # Send request
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            # Check response
            if response.status_code == 204:  # Discord webhook success
                self.logger.info("Discord notification sent successfully")
                if notification:
                    notification.mark_as_sent({"status_code": response.status_code})
                return True
            else:
                error_msg = f"Discord webhook failed with status {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                if notification:
                    notification.mark_as_failed(error_msg)
                return False
                
        except requests.exceptions.Timeout:
            error_msg = "Discord webhook request timed out"
            self.logger.error(error_msg)
            if notification:
                notification.mark_as_failed(error_msg)
            return False
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Discord webhook request failed: {str(e)}"
            self.logger.error(error_msg)
            if notification:
                notification.mark_as_failed(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error sending Discord notification: {str(e)}"
            self.logger.error(error_msg)
            if notification:
                notification.mark_as_failed(error_msg)
            return False
    
    def _build_payload(self, discord_data: DiscordNotification) -> Dict[str, Any]:
        payload = {}
        
        # Basic message content
        if discord_data.content:
            payload["content"] = discord_data.content
        
        if discord_data.username:
            payload["username"] = discord_data.username
        
        if discord_data.avatar_url:
            payload["avatar_url"] = discord_data.avatar_url
        
        # Build embed if we have embed data
        if (discord_data.embed_title or discord_data.embed_description or 
            discord_data.embed_fields or discord_data.embed_color):
            
            embed = {}
            
            if discord_data.embed_title:
                embed["title"] = discord_data.embed_title
            
            if discord_data.embed_description:
                embed["description"] = discord_data.embed_description
            
            if discord_data.embed_color:
                embed["color"] = discord_data.embed_color
            
            if discord_data.embed_fields:
                embed["fields"] = discord_data.embed_fields
            
            # Add timestamp
            embed["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            payload["embeds"] = [embed]
        
        return payload
    
    def send_simple_message(self, message: str, webhook_url: Optional[str] = None, 
                          username: Optional[str] = None) -> bool:
        discord_data = DiscordNotification(
            webhook_url=webhook_url or self.default_webhook_url,
            content=message,
            username=username
        )
        
        if not discord_data.webhook_url:
            self.logger.error("No webhook URL provided for simple message")
            return False
        
        return self.send_discord_message(discord_data)
    
    def send_embed_message(self, title: str, description: str, 
                          color: Optional[int] = None, fields: Optional[List[Dict[str, Any]]] = None,
                          webhook_url: Optional[str] = None, username: Optional[str] = None) -> bool:
        discord_data = DiscordNotification(
            webhook_url=webhook_url or self.default_webhook_url,
            username=username,
            embed_title=title,
            embed_description=description,
            embed_color=color,
            embed_fields=fields or []
        )
        
        if not discord_data.webhook_url:
            self.logger.error("No webhook URL provided for embed message")
            return False
        
        return self.send_discord_message(discord_data)
    
    def send_bug_notification(self, title: str, description: str, severity: str,
                            github_url: Optional[str] = None, webhook_url: Optional[str] = None) -> bool:
        # Color mapping for severity
        color_map = {
            "low": 0x00ff00,      # Green
            "medium": 0xffff00,   # Yellow  
            "high": 0xff8000,     # Orange
            "critical": 0xff0000  # Red
        }
        
        color = color_map.get(severity.lower(), 0x808080)  # Default gray
        
        # Build fields
        fields = [
            {"name": "Severidade", "value": severity.title(), "inline": True}
        ]
        
        if github_url:
            fields.append({"name": "GitHub Issue", "value": f"[Ver Issue]({github_url})", "inline": False})
        
        # Add additional context fields
        fields.append({"name": "Sistema", "value": "Bug Finder", "inline": True})
        fields.append({"name": "Timestamp", "value": time.strftime("%Y-%m-%d %H:%M:%S"), "inline": True})
        
        return self.send_embed_message(
            title=f"🐛 {title}",
            description=description,
            color=color,
            fields=fields,
            webhook_url=webhook_url,
            username="Bug Finder Bot"
        )
    
    def test_webhook(self, webhook_url: Optional[str] = None) -> bool:
        test_url = webhook_url or self.default_webhook_url
        
        if not test_url:
            self.logger.error("No webhook URL provided for testing")
            return False
        
        return self.send_simple_message(
            message="🧪 Bug Finder Discord integration test - Conexão funcionando!",
            webhook_url=test_url,
            username="Bug Finder Test"
        )
    
    def get_webhook_info(self, webhook_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        url = webhook_url or self.default_webhook_url
        
        if not url:
            return None
        
        try:
            # Discord webhook URLs have a specific format
            # https://discord.com/api/webhooks/{id}/{token}
            parts = url.split('/')
            if len(parts) >= 2:
                webhook_id = parts[-2]
                webhook_token = parts[-1]
                
                # Get webhook info (without token for security)
                info_url = f"https://discord.com/api/webhooks/{webhook_id}"
                response = requests.get(info_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "channel_id": data.get("channel_id"),
                        "guild_id": data.get("guild_id"),
                        "type": data.get("type"),
                        "user": data.get("user", {}).get("username") if data.get("user") else None
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get webhook info: {e}")
        
        return None
    
    def validate_webhook_url(self, webhook_url: str) -> bool:
        if not webhook_url:
            return False
        
        # Basic URL format validation
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            return False
        
        # Try to extract ID and token
        try:
            parts = webhook_url.split('/')
            if len(parts) < 2:
                return False
            
            webhook_id = parts[-2]
            webhook_token = parts[-1]
            
            # Basic validation of ID and token format
            if not webhook_id.isdigit() or len(webhook_id) < 17:
                return False
            
            if len(webhook_token) < 60:  # Discord tokens are typically longer
                return False
            
            return True
            
        except Exception:
            return False