"""
LogReceiverAgent - Agente Recebedor de Logs

Localização: src/agents/log_receiver_agent.py

Responsabilidades:
- Receber logs de diversas fontes (texto simples, JSON)
- Validar e estruturar o formato dos logs
- Preparar dados para análise pelos próximos agentes

Este agente atua como o "porteiro" do sistema, garantindo que apenas 
logs válidos e bem formatados passem para a próxima etapa.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

from ..models.log_model import LogModel, LogLevel
from ..config.settings import get_settings

class LogReceiverAgent:
    """
    Agente responsável por receber e processar logs de entrada.
    
    Este agente é independente de modelo de IA, focando apenas na
    validação e estruturação dos dados de entrada.
    """

    def __init__(self):
        """Inicializa o agente recebedor de logs."""
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()

    # Recebe um log bruto e o converte para um objeto LogModel estruturado.
    def receive_log(self, raw_log: Union[str, Dict[str, Any]]) -> Optional[LogModel]:
        """
        Recebe um log bruto e o converte para um objeto LogModel estruturado.
        
        Args:
            raw_log: Log bruto que pode ser string ou dicionário
            
        Returns:
            LogModel estruturado ou None se inválido
        """
        try:
            self.logger.info("Recebendo novo log para processamento")
            
            # Se for string, tenta interpretar como JSON primeiro
            if isinstance(raw_log, str):
                processed_log = self._process_string_log(raw_log)
            elif isinstance(raw_log, dict):
                processed_log = self._process_dict_log(raw_log)
            else:
                self.logger.error(f"Tipo de log não suportado: {type(raw_log)}")
                return None
                
            # Valida o log processado
            if self._validate_log(processed_log):
                log_entry = self._create_log_entry(processed_log)
                self.logger.info(f"Log processado com sucesso: {log_entry.id}")
                return log_entry
            else:
                self.logger.warning("Log não passou na validação")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao processar log: {str(e)}")
            return None
        
    def _process_string_log(self, log_string: str) -> Dict[str, Any]:
        """
        Processa um log em formato string.
        
        Tenta primeiro interpretar como JSON, senão trata como texto simples.
        """
        log_string = log_string.strip()
        
        # Tenta interpretar como JSON
        try:
            return json.loads(log_string)
        except json.JSONDecodeError:
            # Se não for JSON, trata como log de texto simples
            return self._parse_text_log(log_string)
        
    def _parse_text_log(self, text: str) -> Dict[str, Any]:
        """
        Faz parsing básico de um log em texto simples.
        
        Busca por padrões comuns em logs (timestamp, level, message).
        """
        # Padrões comuns de log
        patterns = [
            # [2024-01-15 10:30:45] ERROR: Erro na aplicação
            r'^\[([^\]]+)\]\s+(\w+):\s*(.+)$',
            # 2024-01-15 10:30:45 ERROR Erro na aplicação  
            r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)$',
            # ERROR: Erro na aplicação
            r'^(\w+):\s*(.+)$',
        ]
        
        import re
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # timestamp, level, message
                    return {
                        'timestamp': groups[0],
                        'level': groups[1].upper(),
                        'message': groups[2],
                        'raw_log': text
                    }
                elif len(groups) == 2:  # level, message
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'level': groups[0].upper(),
                        'message': groups[1],
                        'raw_log': text
                    }
        
        # Se não conseguir fazer parsing, trata como mensagem simples
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'UNKNOWN',
            'message': text,
            'raw_log': text
        }
    
    def _process_dict_log(self, log_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um log que já está em formato de dicionário.
        
        Normaliza as chaves e valores para o formato padrão.
        """
        # Mapeamento de chaves comuns para formato padrão
        key_mappings = {
            'msg': 'message',
            'text': 'message',
            'error': 'message',
            'description': 'message',
            'ts': 'timestamp',
            'time': 'timestamp',
            'datetime': 'timestamp',
            'created_at': 'timestamp',
            'severity': 'level',
            'priority': 'level',
            'type': 'level',
            'app': 'source',
            'service': 'source',
            'application': 'source',
            'component': 'component',
            'module': 'component',
            'stack': 'stack_trace',
            'stacktrace': 'stack_trace',
            'trace': 'stack_trace',
        }
        
        # Normaliza as chaves
        normalized = {}
        for key, value in log_dict.items():
            normalized_key = key_mappings.get(key.lower(), key.lower())
            normalized[normalized_key] = value
        
        # Garante campos obrigatórios
        if 'timestamp' not in normalized:
            normalized['timestamp'] = datetime.now().isoformat()
            
        if 'level' not in normalized:
            normalized['level'] = 'INFO'
            
        if 'message' not in normalized:
            # Tenta construir mensagem a partir de outros campos
            if 'error' in normalized:
                normalized['message'] = str(normalized['error'])
            else:
                normalized['message'] = str(log_dict)
        
        # Preserva o log original
        normalized['raw_log'] = log_dict
        
        return normalized
    
    def _validate_log(self, log_data: Dict[str, Any]) -> bool:
        """
        Valida se o log tem os campos mínimos necessários.
        """
        required_fields = ['timestamp', 'level', 'message']
        
        for field in required_fields:
            if field not in log_data or not log_data[field]:
                self.logger.warning(f"Campo obrigatório ausente: {field}")
                return False
        
        # Valida se o level é reconhecido
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical', 'fatal']
        if log_data['level'].lower() not in valid_levels:
            self.logger.warning(f"Nível de log não reconhecido: {log_data['level']}")
            # Não rejeita, apenas avisa
        
        return True
    
    def _create_log_entry(self, log_data: Dict[str, Any]) -> LogModel:
        """
        Cria um objeto LogModel a partir dos dados processados.
        """
        # Converte string de level para enum
        try:
            level = LogLevel(log_data['level'].lower())
        except (KeyError, ValueError):
            level = LogLevel.ERROR  # Default to error for unknown levels
        
        # Extract service name from source if available
        service_name = None
        if 'source' in log_data:
            service_name = log_data['source']
        
        # Handle timestamp conversion
        timestamp = log_data['timestamp']
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.now()
        
        return LogModel(
            raw_content=str(log_data.get('raw_log', log_data['message'])),
            timestamp=timestamp,
            level=level,
            message=log_data['message'],
            service_name=service_name,
            environment=log_data.get('environment'),
            stack_trace=log_data.get('stack_trace'),
            user_id=log_data.get('user_id'),
            request_id=log_data.get('request_id'),
            additional_data=log_data.get('context', {})
        )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente.
        """
        return {
            'name': 'LogReceiverAgent',
            'version': '1.0.0',
            'description': 'Agente responsável por receber e estruturar logs de entrada',
            'capabilities': [
                'Processar logs em formato texto',
                'Processar logs em formato JSON',
                'Validar estrutura de logs',
                'Normalizar formatos diferentes',
                'Criar objetos LogModel estruturados'
            ],
            'input_formats': ['string', 'dict'],
            'output_format': 'LogModel'
        }


# Exemplo de uso e testes
if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    agent = LogReceiverAgent()
    
    # Teste 1: Log em formato JSON
    json_log = {
        "timestamp": "2024-01-15T10:30:45Z",
        "level": "ERROR",
        "message": "Falha na conexão com banco de dados",
        "source": "API",
        "component": "DatabaseService",
        "context": {"connection_string": "postgres://..."}
    }
    
    print("Teste 1 - Log JSON:")
    result1 = agent.receive_log(json_log)
    print(f"Resultado: {result1}")
    
    # Teste 2: Log em formato texto simples
    text_log = "[2024-01-15 10:30:45] ERROR: Usuário não encontrado ID: 12345"
    
    print("\nTeste 2 - Log Texto:")
    result2 = agent.receive_log(text_log)
    print(f"Resultado: {result2}")
    
    # Teste 3: Log malformado
    bad_log = None
    
    print("\nTeste 3 - Log Inválido:")
    result3 = agent.receive_log(bad_log)
    print(f"Resultado: {result3}")
    
    # Info do agente
    print(f"\nInfo do Agente:")
    print(json.dumps(agent.get_agent_info(), indent=2))