# 🧪 Logs de Teste Rápido para Bug Finder

Use estes logs para testar o sistema na **interface web** ou **CLI**.

## 🔥 Log Crítico - Banco de Dados

```
ERROR 2024-01-20 10:30:45 - app.py:142 - Database connection failed
Traceback (most recent call last):
  File "app.py", line 142, in connect_db
    connection = psycopg2.connect(DATABASE_URL)
psycopg2.OperationalError: could not connect to server: Connection refused
User ID: user_12345
Session ID: sess_abc123
```

**Esperado:** Issue crítica criada automaticamente

---

## ⚠️ Log Alto - Erro de Autenticação

```
CRITICAL 2024-01-20 11:15:22 - auth.py:78 - Authentication failed for user
Exception: Invalid JWT token signature
  at validateToken (auth.js:45:12)
  at authenticateUser (auth.js:120:5)
User: john.doe@company.com
IP: 192.168.1.100
```

**Esperado:** Issue de segurança criada

---

## 💰 Log Médio - Erro de API de Pagamento

```
ERROR 2024-01-20 12:45:33 - payment_service.py:89 - Payment API request failed
HTTPError: 503 Service Unavailable
URL: https://api.payment-gateway.com/v1/charge
Amount: $159.99
Customer ID: cust_567890
```

**Esperado:** Issue de integração criada

---

## ⏱️ Log Médio - Timeout de Query

```
ERROR 2024-01-20 14:05:48 - search_service.py:156 - Search query timeout
TimeoutError: Query execution exceeded 30 seconds
Query: SELECT * FROM products WHERE description LIKE '%complex search term%'
Execution time: 31.245 seconds
```

**Esperado:** Issue de performance criada

---

## 💾 Log Crítico - Espaço em Disco

```
CRITICAL 2024-01-20 15:30:12 - system_monitor.py:67 - Disk space critically low
DiskSpaceError: Available disk space: 2.1 GB (5% remaining)
Mount point: /var/log
Services affected: logging, backup, temp-files
```

**Esperado:** Issue crítica de infraestrutura

---

## ℹ️ Log Informativo - NÃO deve criar issue

```
INFO 2024-01-20 16:45:30 - user_activity.py:23 - User login successful
User: alice@company.com
Login method: SSO
IP: 10.0.1.45
```

**Esperado:** Análise sem criação de issue

---

## 🌐 Log Alto - Erro de Rede

```
ERROR 2024-01-20 17:22:18 - api_client.py:134 - External service connection failed
ConnectionError: HTTPSConnectionPool(host='external-api.com', port=443): Max retries exceeded
Timeout: 10.0 seconds
Service: DataSyncService
```

**Esperado:** Issue de conectividade criada

---

## 📝 Como Testar

### Interface Web

1. Acesse: `http://localhost:8000`
2. Cole um dos logs acima
3. Observe a análise e issue criada

### CLI

```bash
adk run agents/bug_finder
# Cole o log no prompt e pressione Enter
```

### Python

```python
from src.agents import BugFinderSystem
bf = BugFinderSystem()
result = bf.process_log("COLE_O_LOG_AQUI")
print(result)
```
