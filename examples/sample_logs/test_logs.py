"""
Exemplos de logs para teste do Bug Finder System.
Inclui diferentes tipos de logs com vários níveis de criticidade.
"""

from datetime import datetime
from typing import Dict, List
import json

# Logs de exemplo organizados por criticidade
SAMPLE_LOGS = {
    "critical": [
        {
            "message": """2024-06-07 14:30:15 CRITICAL [DatabaseService] Database connection pool exhausted
java.sql.SQLException: Cannot get connection, pool exhausted
    at com.company.db.ConnectionPool.getConnection(ConnectionPool.java:145)
    at com.company.service.DatabaseService.execute(DatabaseService.java:89)
    at com.company.controller.UserController.getAllUsers(UserController.java:45)
All 50 connections in use. System unable to serve requests.""",
            "level": "CRITICAL",
            "source": "DatabaseService", 
            "environment": "production",
            "timestamp": "2024-06-07T14:30:15.123Z",
            "user_id": None,
            "session_id": None,
            "request_id": "req_critical_001"
        },
        {
            "message": """2024-06-07 15:45:30 CRITICAL [PaymentService] Payment processing failed - Transaction rollback error
java.sql.DataIntegrityViolationException: Unable to rollback transaction
    at com.company.payment.TransactionManager.rollback(TransactionManager.java:234)
    at com.company.service.PaymentService.processPayment(PaymentService.java:156)
CRITICAL: Customer payment of $1,250.00 may be in inconsistent state
Customer ID: cust_789, Payment ID: pay_abc123""",
            "level": "CRITICAL",
            "source": "PaymentService",
            "environment": "production", 
            "timestamp": "2024-06-07T15:45:30.567Z",
            "user_id": "cust_789",
            "session_id": "sess_payment_123",
            "request_id": "req_payment_456"
        }
    ],
    
    "high": [
        {
            "message": """2024-06-07 16:20:45 ERROR [AuthenticationService] JWT token validation failed
io.jsonwebtoken.ExpiredJwtException: JWT expired at 2024-06-07T16:15:00Z
    at io.jsonwebtoken.impl.DefaultJwtParser.parse(DefaultJwtParser.java:385)
    at com.company.auth.JwtTokenValidator.validate(JwtTokenValidator.java:67)
    at com.company.filter.AuthenticationFilter.doFilter(AuthenticationFilter.java:89)
User unable to access protected resources. Token expired 5 minutes ago.
User ID: user_456, Session: sess_xyz789""",
            "level": "ERROR",
            "source": "AuthenticationService",
            "environment": "production",
            "timestamp": "2024-06-07T16:20:45.234Z",
            "user_id": "user_456",
            "session_id": "sess_xyz789",
            "request_id": "req_auth_789"
        },
        {
            "message": """2024-06-07 17:10:12 ERROR [FileUploadService] File upload failed - Storage quota exceeded
java.io.IOException: No space left on device
    at java.io.FileOutputStream.writeBytes(Native Method)
    at java.io.FileOutputStream.write(FileOutputStream.java:326)
    at com.company.storage.FileUploadService.saveFile(FileUploadService.java:123)
Available space: 0 MB, Required: 15 MB
File: document_2024.pdf, Size: 15.2 MB, User: user_789""",
            "level": "ERROR",
            "source": "FileUploadService",
            "environment": "production",
            "timestamp": "2024-06-07T17:10:12.890Z",
            "user_id": "user_789",
            "session_id": "sess_upload_456",
            "request_id": "req_upload_123"
        }
    ],
    
    "medium": [
        {
            "message": """2024-06-07 18:30:20 WARN [EmailService] Email delivery delayed - SMTP server response slow
javax.mail.MessagingException: Read timeout
    at com.sun.mail.smtp.SMTPTransport.readServerResponse(SMTPTransport.java:2270)
    at com.company.notification.EmailService.sendEmail(EmailService.java:145)
Email queued for retry. Recipient: user@example.com
Subject: Welcome to our platform, Delivery attempt: 2/3""",
            "level": "WARNING",
            "source": "EmailService",
            "environment": "production",
            "timestamp": "2024-06-07T18:30:20.456Z",
            "user_id": "user_email_123",
            "session_id": "sess_email_789",
            "request_id": "req_email_456"
        },
        {
            "message": """2024-06-07 19:15:35 ERROR [SearchService] Search index update failed - Elasticsearch timeout
org.elasticsearch.client.ResponseException: timeout
    at org.elasticsearch.client.RestClient.performRequest(RestClient.java:569)
    at com.company.search.SearchIndexService.updateIndex(SearchIndexService.java:234)
Search results may be outdated. Last successful index: 2024-06-07T18:00:00Z
Index: product_catalog, Documents pending: 1,250""",
            "level": "ERROR",
            "source": "SearchService",
            "environment": "production",
            "timestamp": "2024-06-07T19:15:35.123Z",
            "user_id": None,
            "session_id": None,
            "request_id": "req_search_789"
        }
    ],
    
    "low": [
        {
            "message": """2024-06-07 20:45:10 WARN [CacheService] Cache miss rate above threshold
Cache statistics: Hit rate: 65%, Miss rate: 35%, Threshold: 30%
Recommended: Review cache configuration or increase memory allocation
Cache: user_sessions, Size: 50MB, Max: 100MB""",
            "level": "WARNING",
            "source": "CacheService", 
            "environment": "production",
            "timestamp": "2024-06-07T20:45:10.789Z",
            "user_id": None,
            "session_id": None,
            "request_id": "req_cache_monitoring"
        },
        {
            "message": """2024-06-07 21:20:25 INFO [UserService] User registration completed with validation warnings
User successfully created but some optional fields failed validation
User ID: user_new_456, Email: newuser@example.com
Warnings: Phone number format invalid, Profile picture upload skipped""",
            "level": "INFO",
            "source": "UserService",
            "environment": "production",
            "timestamp": "2024-06-07T21:20:25.345Z",
            "user_id": "user_new_456",
            "session_id": "sess_registration_123",
            "request_id": "req_registration_789"
        }
    ],
    
    "not_bugs": [
        {
            "message": """2024-06-07 22:00:00 INFO [ScheduledTask] Daily backup completed successfully
Backup duration: 45 minutes, Size: 2.3 GB
Files backed up: 15,432, Location: /backup/2024-06-07/
Next backup scheduled: 2024-06-08T22:00:00Z""",
            "level": "INFO",
            "source": "ScheduledTask",
            "environment": "production",
            "timestamp": "2024-06-07T22:00:00.000Z",
            "user_id": None,
            "session_id": None,
            "request_id": "req_backup_daily"
        },
        {
            "message": """2024-06-07 22:30:15 DEBUG [SecurityService] User login audit
User authentication successful via OAuth2
User ID: user_audit_123, IP: 192.168.1.100, Location: São Paulo, Brazil
Device: Chrome 115.0 on Windows 10, Session duration: 2h 15m""",
            "level": "DEBUG",
            "source": "SecurityService",
            "environment": "production", 
            "timestamp": "2024-06-07T22:30:15.567Z",
            "user_id": "user_audit_123",
            "session_id": "sess_audit_456",
            "request_id": "req_audit_789"
        }
    ]
}

# Logs mais complexos para testes avançados
COMPLEX_LOGS = {
    "multi_line_stack_trace": {
        "message": """2024-06-07 14:30:15 ERROR [OrderService] Order processing failed due to inventory inconsistency
com.company.exception.InventoryMismatchException: Product stock mismatch detected
    at com.company.service.InventoryService.validateStock(InventoryService.java:198)
    at com.company.service.OrderService.validateOrder(OrderService.java:145)
    at com.company.service.OrderService.processOrder(OrderService.java:89)
    at com.company.controller.OrderController.createOrder(OrderController.java:67)
    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
    at java.lang.reflect.Method.invoke(Method.java:498)
    at org.springframework.web.method.support.InvocableHandlerMethod.invoke(InvocableHandlerMethod.java:215)

Caused by: java.sql.SQLException: Deadlock detected
    at com.mysql.cj.jdbc.exceptions.SQLError.createSQLException(SQLError.java:129)
    at com.mysql.cj.jdbc.exceptions.SQLExceptionsMapping.translateException(SQLExceptionsMapping.java:122)
    at com.company.repository.InventoryRepository.updateStock(InventoryRepository.java:234)
    ... 8 more

Order Details:
- Order ID: ord_123456
- Customer ID: cust_789
- Products: [{"id": "prod_001", "quantity": 2, "available": 1}, {"id": "prod_002", "quantity": 1, "available": 0}]
- Total Value: $299.99
- Warehouse: WH_SP_001""",
        "level": "ERROR",
        "source": "OrderService",
        "environment": "production",
        "timestamp": "2024-06-07T14:30:15.123Z",
        "user_id": "cust_789",
        "session_id": "sess_order_456",
        "request_id": "req_order_123"
    },
    
    "json_structured_log": {
        "message": json.dumps({
            "level": "ERROR",
            "timestamp": "2024-06-07T15:45:30.567Z",
            "service": "ApiGateway",
            "event": "request_failed",
            "error": {
                "type": "TimeoutException",
                "message": "Downstream service timeout after 30s",
                "code": "GATEWAY_TIMEOUT",
                "details": {
                    "upstream_service": "UserService",
                    "endpoint": "/api/v1/users/profile",
                    "timeout_config": "30s",
                    "actual_duration": "30.125s"
                }
            },
            "request": {
                "id": "req_gateway_789",
                "method": "GET", 
                "path": "/api/v1/users/profile",
                "headers": {
                    "authorization": "Bearer ***",
                    "user-agent": "Mozilla/5.0...",
                    "x-request-id": "req_client_456"
                },
                "user_id": "user_profile_123",
                "session_id": "sess_gateway_789"
            },
            "response": {
                "status": 504,
                "duration_ms": 30125,
                "size_bytes": 0
            },
            "circuit_breaker": {
                "state": "HALF_OPEN",
                "failure_count": 5,
                "next_attempt": "2024-06-07T15:46:00.000Z"
            }
        }, indent=2),
        "level": "ERROR",
        "source": "ApiGateway",
        "environment": "production",
        "timestamp": "2024-06-07T15:45:30.567Z",
        "user_id": "user_profile_123",
        "session_id": "sess_gateway_789",
        "request_id": "req_gateway_789"
    }
}

def get_log_by_criticality(criticality: str) -> List[Dict]:
    """Retorna logs de uma criticidade específica"""
    return SAMPLE_LOGS.get(criticality.lower(), [])

def get_random_log(criticality: str = None) -> Dict:
    """Retorna um log aleatório, opcionalmente filtrado por criticidade"""
    import random
    
    if criticality:
        logs = get_log_by_criticality(criticality)
        if not logs:
            raise ValueError(f"Nenhum log encontrado para criticidade: {criticality}")
        return random.choice(logs)
    
    # Seleciona de qualquer criticidade
    all_logs = []
    for logs_list in SAMPLE_LOGS.values():
        all_logs.extend(logs_list)
    
    return random.choice(all_logs)

def get_complex_log(log_type: str) -> Dict:
    """Retorna um log complexo para testes avançados"""
    return COMPLEX_LOGS.get(log_type, {})

def generate_test_suite() -> List[Dict]:
    """Gera uma suíte completa de testes com logs variados"""
    test_suite = []
    
    # Adiciona pelo menos um log de cada criticidade
    for criticality, logs in SAMPLE_LOGS.items():
        test_suite.extend(logs)
    
    # Adiciona logs complexos
    for log_type, log_data in COMPLEX_LOGS.items():
        test_suite.append(log_data)
    
    return test_suite

def create_test_log(
    message: str,
    level: str = "ERROR",
    source: str = "TestService",
    environment: str = "test",
    user_id: str = None,
    session_id: str = None
) -> Dict:
    """Cria um log customizado para testes"""
    return {
        "message": message,
        "level": level,
        "source": source,
        "environment": environment,
        "timestamp": datetime.now().isoformat() + "Z",
        "user_id": user_id,
        "session_id": session_id,
        "request_id": f"req_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

def print_log_examples():
    """Imprime exemplos de logs para visualização"""
    print("📝 Exemplos de Logs por Criticidade")
    print("=" * 60)
    
    for criticality, logs in SAMPLE_LOGS.items():
        print(f"\n🔴 {criticality.upper()} ({len(logs)} exemplos)")
        print("-" * 40)
        for i, log in enumerate(logs, 1):
            print(f"\n{i}. {log['source']} - {log['timestamp']}")
            # Mostra apenas as primeiras linhas da mensagem
            message_lines = log['message'].split('\n')
            print(f"   {message_lines[0]}")
            if len(message_lines) > 1:
                print(f"   ...")
    
    print(f"\n🔧 Logs Complexos ({len(COMPLEX_LOGS)} exemplos)")
    print("-" * 40)
    for log_type, log_data in COMPLEX_LOGS.items():
        print(f"\n• {log_type}: {log_data['source']}")
        print(f"  Timestamp: {log_data['timestamp']}")

def export_logs_to_file(filename: str = "sample_logs.json"):
    """Exporta todos os logs para um arquivo JSON"""
    all_logs = {
        "sample_logs": SAMPLE_LOGS,
        "complex_logs": COMPLEX_LOGS,
        "metadata": {
            "total_samples": sum(len(logs) for logs in SAMPLE_LOGS.values()),
            "total_complex": len(COMPLEX_LOGS),
            "criticality_levels": list(SAMPLE_LOGS.keys()),
            "generated_at": datetime.now().isoformat()
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_logs, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Logs exportados para: {filename}")

if __name__ == "__main__":
    # Demonstração dos logs disponíveis
    print_log_examples()
    
    # Exemplo de uso
    print(f"\n🎲 Log aleatório crítico:")
    critical_log = get_random_log("critical")
    print(f"Fonte: {critical_log['source']}")
    print(f"Mensagem: {critical_log['message'][:100]}...")
    
    # Exporta para arquivo
    export_logs_to_file()