from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogModel(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp do log")
    level: LogLevel = Field(..., description="Nível do log")
    message: str = Field(..., description="Mensagem principal do log")
    source: Optional[str] = Field(None, description="Origem do log (arquivo, módulo, etc)")
    function_name: Optional[str] = Field(None, description="Nome da função onde ocorreu o erro")
    line_number: Optional[int] = Field(None, description="Número da linha onde ocorreu o erro")
    stack_trace: Optional[str] = Field(None, description="Stack trace completo do erro")
    user_id: Optional[str] = Field(None, description="ID do usuário relacionado ao erro")
    session_id: Optional[str] = Field(None, description="ID da sessão")
    request_id: Optional[str] = Field(None, description="ID da requisição")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais do contexto")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def is_error(self) -> bool:
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]
    
    def is_critical(self) -> bool:
        return self.level == LogLevel.CRITICAL
    
    def has_stack_trace(self) -> bool:
        return self.stack_trace is not None and len(self.stack_trace.strip()) > 0
    
    def get_error_context(self) -> Dict[str, Any]:
        context = {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message
        }
        
        if self.source:
            context["source"] = self.source
        if self.function_name:
            context["function"] = self.function_name
        if self.line_number:
            context["line"] = self.line_number
        if self.user_id:
            context["user_id"] = self.user_id
        if self.session_id:
            context["session_id"] = self.session_id
        if self.request_id:
            context["request_id"] = self.request_id
        if self.additional_data:
            context["additional_data"] = self.additional_data
            
        return context


class ProcessedLog(BaseModel):
    raw_log: str = Field(..., description="Log original recebido")
    parsed_log: LogModel = Field(..., description="Log processado e estruturado")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do processamento")
    is_valid: bool = Field(True, description="Indica se o log foi processado com sucesso")
    validation_errors: Optional[List[str]] = Field(None, description="Erros de validação, se houver")
    
    def has_errors(self) -> bool:
        return not self.is_valid or (self.validation_errors and len(self.validation_errors) > 0)