#!/usr/bin/env python3
"""
Logs de exemplo para testar o Bug Finder.
Use estes logs na interface web ou CLI para ver o sistema funcionando.
"""

# Log 1: Erro crítico de banco de dados
DATABASE_ERROR = """
ERROR 2024-01-20 10:30:45 - app.py:142 - Database connection failed
Traceback (most recent call last):
  File "app.py", line 142, in connect_db
    connection = psycopg2.connect(DATABASE_URL)
  File "/opt/python/lib/python3.11/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
psycopg2.OperationalError: could not connect to server: Connection refused
	Is the server running on host "localhost" (127.0.0.1) and accepting
	TCP/IP connections on port 5432?
User ID: user_12345
Session ID: sess_abc123
Request ID: req_789xyz
"""

# Log 2: Erro de autenticação
AUTH_ERROR = """
ERROR 2024-01-20 11:15:22 - auth.py:78 - Authentication failed for user
Exception: Invalid JWT token signature
  at validateToken (auth.js:45:12)
  at authenticateUser (auth.js:120:5)
  at /app/routes/api.js:23:3
User: john.doe@company.com
IP: 192.168.1.100
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
"""

# Log 3: Erro de API externa
API_ERROR = """
ERROR 2024-01-20 12:45:33 - payment_service.py:89 - Payment API request failed
HTTPError: 503 Service Unavailable
Response: {"error": "Service temporarily unavailable", "retry_after": 60}
URL: https://api.payment-gateway.com/v1/charge
Method: POST
Amount: $159.99
Customer ID: cust_567890
Order ID: order_abc123
"""

# Log 4: Erro de validação (menos crítico)
VALIDATION_ERROR = """
WARNING 2024-01-20 13:20:15 - forms.py:234 - Form validation failed
ValidationError: Email format is invalid
Field: email
Value: "not-an-email"
User input: {"name": "John", "email": "not-an-email", "age": 25}
Form: UserRegistrationForm
"""

# Log 5: Erro de performance/timeout
TIMEOUT_ERROR = """
ERROR 2024-01-20 14:05:48 - search_service.py:156 - Search query timeout
TimeoutError: Query execution exceeded 30 seconds
Query: SELECT * FROM products WHERE description LIKE '%complex search term%'
Execution time: 31.245 seconds
Database: products_db
Connection pool: 15/20 active connections
"""

# Log 6: Erro de sistema/infraestrutura
SYSTEM_ERROR = """
CRITICAL 2024-01-20 15:30:12 - system_monitor.py:67 - Disk space critically low
DiskSpaceError: Available disk space: 2.1 GB (5% remaining)
Mount point: /var/log
Total size: 50 GB
Used: 47.9 GB
Critical threshold: 10%
Services affected: logging, backup, temp-files
"""

# Log 7: Log informativo (não deve criar issue)
INFO_LOG = """
INFO 2024-01-20 16:45:30 - user_activity.py:23 - User login successful
User: alice@company.com
Login method: SSO
IP: 10.0.1.45
Session duration: 8h 15m
Last login: 2024-01-19 08:30:22
"""

# Log 8: Erro de rede/conectividade
NETWORK_ERROR = """
ERROR 2024-01-20 17:22:18 - api_client.py:134 - External service connection failed
ConnectionError: HTTPSConnectionPool(host='external-api.com', port=443): 
Max retries exceeded with url: /api/v2/data (Caused by ConnectTimeoutError)
Timeout: 10.0 seconds
Retry attempts: 3
Service: DataSyncService
Last successful sync: 2024-01-20 15:30:00
"""

# Dicionário com todos os logs para fácil acesso
SAMPLE_LOGS = {
    "database_error": DATABASE_ERROR,
    "auth_error": AUTH_ERROR, 
    "api_error": API_ERROR,
    "validation_error": VALIDATION_ERROR,
    "timeout_error": TIMEOUT_ERROR,
    "system_error": SYSTEM_ERROR,
    "info_log": INFO_LOG,
    "network_error": NETWORK_ERROR
}

def print_all_logs():
    """Imprime todos os logs de exemplo."""
    for name, log in SAMPLE_LOGS.items():
        print(f"\n{'='*50}")
        print(f"LOG: {name.upper()}")
        print('='*50)
        print(log.strip())

def get_log(name: str) -> str:
    """Retorna um log específico pelo nome."""
    return SAMPLE_LOGS.get(name, "Log não encontrado")

if __name__ == "__main__":
    print("🧪 LOGS DE EXEMPLO PARA TESTE DO BUG FINDER")
    print("=" * 60)
    print("\nUse estes logs para testar:")
    print("1. Interface Web: http://localhost:8000")
    print("2. CLI: adk run agents/bug_finder")
    print("3. Python: BugFinderSystem().process_log(log)")
    
    print_all_logs()