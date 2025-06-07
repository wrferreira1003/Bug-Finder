import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BugFinderSettings(BaseModel):
    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Environment the system is running in"
    )
    debug_mode: bool = Field(default=True, description="Enable debug mode")
    
    # API Keys and Tokens
    github_access_token: str = Field(..., description="GitHub personal access token")
    google_ai_api_key: str = Field(..., description="Google AI API key for Gemini")
    discord_webhook_url: Optional[str] = Field(None, description="Discord webhook URL for notifications")
    
    # GitHub Configuration
    github_repository_owner: str = Field(..., description="GitHub repository owner")
    github_repository_name: str = Field(..., description="GitHub repository name")
    github_default_labels: List[str] = Field(
        default=["bug", "auto-generated"],
        description="Default labels for created issues"
    )
    github_default_assignees: List[str] = Field(
        default_factory=list,
        description="Default assignees for created issues"
    )
    
    # Google AI Configuration
    gemini_model: str = Field(default="gemini-1.5-pro", description="Gemini model to use")
    gemini_temperature: float = Field(default=0.1, description="Temperature for AI responses")
    gemini_max_tokens: int = Field(default=8192, description="Maximum tokens for AI responses")
    gemini_timeout_seconds: int = Field(default=30, description="Timeout for AI requests")
    
    # Processing Configuration
    max_log_size_mb: float = Field(default=10.0, description="Maximum log size in MB")
    max_processing_time_minutes: int = Field(default=10, description="Maximum processing time per log")
    enable_parallel_processing: bool = Field(default=False, description="Enable parallel processing of logs")
    max_parallel_workers: int = Field(default=3, description="Maximum parallel workers")
    
    # Analysis Configuration
    minimum_confidence_score: float = Field(default=0.7, description="Minimum confidence to create issue")
    enable_duplicate_detection: bool = Field(default=True, description="Enable duplicate issue detection")
    duplicate_similarity_threshold: float = Field(default=0.8, description="Similarity threshold for duplicates")
    
    # Issue Creation Configuration
    max_issue_creation_retries: int = Field(default=3, description="Maximum retries for issue creation")
    issue_creation_retry_delay_seconds: int = Field(default=5, description="Delay between retries")
    enable_issue_review: bool = Field(default=True, description="Enable issue review process")
    max_review_iterations: int = Field(default=2, description="Maximum review iterations")
    
    # Notification Configuration
    enable_discord_notifications: bool = Field(default=True, description="Enable Discord notifications")
    notification_retry_attempts: int = Field(default=3, description="Notification retry attempts")
    notification_retry_delay_seconds: int = Field(default=10, description="Delay between notification retries")
    
    # Rate Limiting
    github_rate_limit_buffer: int = Field(default=100, description="GitHub rate limit buffer")
    discord_rate_limit_per_minute: int = Field(default=30, description="Discord rate limit per minute")
    ai_requests_per_minute: int = Field(default=60, description="AI requests per minute limit")
    
    # Logging Configuration
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    log_file_path: Optional[str] = Field(None, description="Path to log file")
    enable_structured_logging: bool = Field(default=True, description="Enable structured JSON logging")
    log_retention_days: int = Field(default=30, description="Log retention period in days")
    
    # System Configuration
    system_version: str = Field(default="1.0.0", description="Bug Finder system version")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_retention_days: int = Field(default=90, description="Metrics retention period")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @classmethod
    def from_env(cls) -> "BugFinderSettings":
        # Helper function to clean environment values
        def clean_env(key: str, default: str = "") -> str:
            value = os.getenv(key, default)
            return value.split('#')[0].strip() if value else default
        
        return cls(
            environment=Environment(clean_env("ENVIRONMENT", "development")),
            debug_mode=clean_env("DEBUG_MODE", "true").lower() == "true",
            
            # Required API keys
            github_access_token=clean_env("GITHUB_ACCESS_TOKEN"),
            google_ai_api_key=clean_env("GOOGLE_AI_API_KEY"),
            discord_webhook_url=clean_env("DISCORD_WEBHOOK_URL") or None,
            
            # GitHub settings
            github_repository_owner=clean_env("GITHUB_REPOSITORY_OWNER"),
            github_repository_name=clean_env("GITHUB_REPOSITORY_NAME"),
            github_default_labels=[l.strip() for l in clean_env("GITHUB_DEFAULT_LABELS", "bug,auto-generated").split(",")],
            github_default_assignees=[a.strip() for a in clean_env("GITHUB_DEFAULT_ASSIGNEES").split(",") if a.strip()],
            
            # Google AI settings
            gemini_model=clean_env("GEMINI_MODEL", "gemini-1.5-pro"),
            gemini_temperature=float(clean_env("GEMINI_TEMPERATURE", "0.1")),
            gemini_max_tokens=int(clean_env("GEMINI_MAX_TOKENS", "8192")),
            gemini_timeout_seconds=int(clean_env("GEMINI_TIMEOUT_SECONDS", "30")),
            
            # Processing settings
            max_log_size_mb=float(clean_env("MAX_LOG_SIZE_MB", "10.0")),
            max_processing_time_minutes=int(clean_env("MAX_PROCESSING_TIME_MINUTES", "10")),
            enable_parallel_processing=clean_env("ENABLE_PARALLEL_PROCESSING", "false").lower() == "true",
            max_parallel_workers=int(clean_env("MAX_PARALLEL_WORKERS", "3")),
            
            # Analysis settings
            minimum_confidence_score=float(clean_env("MINIMUM_CONFIDENCE_SCORE", "0.7")),
            enable_duplicate_detection=clean_env("ENABLE_DUPLICATE_DETECTION", "true").lower() == "true",
            duplicate_similarity_threshold=float(clean_env("DUPLICATE_SIMILARITY_THRESHOLD", "0.8")),
            
            # Issue creation settings
            max_issue_creation_retries=int(clean_env("MAX_ISSUE_CREATION_RETRIES", "3")),
            issue_creation_retry_delay_seconds=int(clean_env("ISSUE_CREATION_RETRY_DELAY_SECONDS", "5")),
            enable_issue_review=clean_env("ENABLE_ISSUE_REVIEW", "true").lower() == "true",
            max_review_iterations=int(clean_env("MAX_REVIEW_ITERATIONS", "2")),
            
            # Notification settings
            enable_discord_notifications=clean_env("ENABLE_DISCORD_NOTIFICATIONS", "true").lower() == "true",
            notification_retry_attempts=int(clean_env("NOTIFICATION_RETRY_ATTEMPTS", "3")),
            notification_retry_delay_seconds=int(clean_env("NOTIFICATION_RETRY_DELAY_SECONDS", "10")),
            
            # Rate limiting
            github_rate_limit_buffer=int(clean_env("GITHUB_RATE_LIMIT_BUFFER", "100")),
            discord_rate_limit_per_minute=int(clean_env("DISCORD_RATE_LIMIT_PER_MINUTE", "30")),
            ai_requests_per_minute=int(clean_env("AI_REQUESTS_PER_MINUTE", "60")),
            
            # Logging
            log_level=LogLevel(clean_env("LOG_LEVEL", "INFO")),
            log_file_path=clean_env("LOG_FILE_PATH") or None,
            enable_structured_logging=clean_env("ENABLE_STRUCTURED_LOGGING", "true").lower() == "true",
            log_retention_days=int(clean_env("LOG_RETENTION_DAYS", "30")),
            
            # System
            system_version=clean_env("SYSTEM_VERSION", "1.0.0"),
            enable_metrics=clean_env("ENABLE_METRICS", "true").lower() == "true",
            metrics_retention_days=int(clean_env("METRICS_RETENTION_DAYS", "90"))
        )
    
    def validate_required_settings(self) -> List[str]:
        errors = []
        
        if not self.github_access_token:
            errors.append("GITHUB_ACCESS_TOKEN is required")
        
        if not self.google_ai_api_key:
            errors.append("GOOGLE_AI_API_KEY is required")
        
        if not self.github_repository_owner:
            errors.append("GITHUB_REPOSITORY_OWNER is required")
        
        if not self.github_repository_name:
            errors.append("GITHUB_REPOSITORY_NAME is required")
        
        if self.enable_discord_notifications and not self.discord_webhook_url:
            errors.append("DISCORD_WEBHOOK_URL is required when Discord notifications are enabled")
        
        # Validate ranges
        if not (0.0 <= self.gemini_temperature <= 2.0):
            errors.append("GEMINI_TEMPERATURE must be between 0.0 and 2.0")
        
        if not (0.0 <= self.minimum_confidence_score <= 1.0):
            errors.append("MINIMUM_CONFIDENCE_SCORE must be between 0.0 and 1.0")
        
        if not (0.0 <= self.duplicate_similarity_threshold <= 1.0):
            errors.append("DUPLICATE_SIMILARITY_THRESHOLD must be between 0.0 and 1.0")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "system_version": self.system_version,
            "github_repository": f"{self.github_repository_owner}/{self.github_repository_name}",
            "gemini_model": self.gemini_model,
            "notifications_enabled": self.enable_discord_notifications,
            "review_enabled": self.enable_issue_review,
            "parallel_processing": self.enable_parallel_processing
        }


# Global settings instance
_settings: Optional[BugFinderSettings] = None


def get_settings() -> BugFinderSettings:
    global _settings
    if _settings is None:
        _settings = BugFinderSettings.from_env()
    return _settings


def reload_settings() -> BugFinderSettings:
    global _settings
    _settings = BugFinderSettings.from_env()
    return _settings