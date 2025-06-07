# 🐛 Bug Finder System

Sistema automatizado inteligente para análise de logs, detecção de bugs e criação automática de issues no GitHub usando Google AI Agent Development Kit (ADK).

## ⚡ Início Rápido

```bash
# 1. Instalar e configurar
pip install -r requirements.txt
cp .env.example .env  # Configure suas chaves API

# 2. Executar interface web
adk web agents
# Abra http://localhost:8000

# 3. Ou usar CLI interativo
adk run agents/bug_finder
```

## ✨ Funcionalidades

- 🔍 **Análise Inteligente de Logs** - AI analisa logs e identifica bugs reais
- 🎯 **Detecção Automática** - Classifica severidade, categoria e impacto
- 📋 **Criação de Issues** - Gera issues detalhadas no GitHub automaticamente
- 🔄 **Revisão Automática** - Revisa e refina issues antes da publicação
- 🔔 **Notificações Discord** - Alerta a equipe sobre bugs críticos
- 🖥️ **Interface Web** - UI moderna via Google ADK para teste e monitoramento

## 🚀 Instalação e Execução

### 1. Pré-requisitos
- Python 3.10+
- Conta GitHub com token de acesso
- Chave API do Google AI (Gemini)
- Webhook Discord (opcional)

### 2. Configuração Rápida

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves (veja seção abaixo)
```

### 3. Variáveis Obrigatórias no .env

```bash
# GitHub (obrigatório)
GITHUB_ACCESS_TOKEN=ghp_your_token_here
GITHUB_REPOSITORY_OWNER=your_username  
GITHUB_REPOSITORY_NAME=your_repo

# Google AI (obrigatório)
GOOGLE_AI_API_KEY=your_google_ai_key_here

# Discord (opcional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

#### 🔑 Como Obter as Chaves API

**GitHub Token:**
1. Vá para [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Clique "Generate new token (classic)"
3. Selecione permissões: `repo`, `issues`, `write:repo_hook`
4. Copie o token gerado

**Google AI API Key:**
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Clique "Create API Key"
3. Copie a chave gerada

**Discord Webhook (Opcional):**
1. No Discord, vá para Server Settings > Integrations > Webhooks
2. Clique "New Webhook"
3. Copie a webhook URL

### 4. 🎯 Como Executar

#### **Interface Web (Recomendado) 🌐**
```bash
adk web agents
# Abra http://localhost:8000 no navegador
```

#### **CLI Interativo 💻**
```bash
adk run agents/bug_finder
# Digite logs para análise diretamente no terminal
```

#### **Modo Standalone 🔧**
```bash
python main.py
# Para desenvolvimento e testes
```

### 5. ⚡ Uso Rápido

```bash
# Testar o sistema
echo "ERROR: Database connection failed" | python -c "
from src.agents import BugFinderSystem
bf = BugFinderSystem()
print(bf.run('ERROR: Database connection failed'))
"
```

## 💻 Como Usar

### 🌐 Interface Web ADK (Recomendado)

1. Execute: `adk web agents`
2. Abra **http://localhost:8000** no navegador
3. Na interface você pode:
   - ✅ Enviar logs para análise completa
   - 📊 Ver status e estatísticas do sistema
   - 🧪 Testar integrações (GitHub, Discord, AI)
   - 📋 Monitorar issues criadas
   - ⚙️ Verificar configurações

### 💻 CLI Interativo

```bash
# Iniciar CLI
adk run agents/bug_finder

# Exemplos de uso no CLI:
> ERROR 2024-01-01 Database connection failed
> status
> test
```

### 🔧 Modo Programático

```python
from src.agents import BugFinderSystem

# Criar sistema
bug_finder = BugFinderSystem()

# Processar log completo (análise + issue + notificação)
result = bug_finder.process_log("""
ERROR 2024-01-01 10:30:45 - Database connection failed
psycopg2.OperationalError: could not connect to server
""")

# Apenas analisar (sem criar issue)
analysis = bug_finder.analyze_sample_log("ERROR: App crashed")

# Ver status do sistema
status = bug_finder.get_system_status()
print(f"Logs processados: {status['statistics']['logs_processed']}")
```

### 📱 Comandos Rápidos

```bash
# Status do sistema
python -c "from src.agents import BugFinderSystem; print(BugFinderSystem().get_system_status())"

# Testar integrações
python -c "from src.agents import BugFinderSystem; print(BugFinderSystem().test_integrations())"

# Processar log específico
python -c "from src.agents import BugFinderSystem; print(BugFinderSystem().process_log('ERROR: Test error'))"
```

## 🏗️ Arquitetura

O sistema usa **3 agentes especializados** para máxima eficiência:

### 1. 🔍 BugAnalyserAgent
- Processa logs brutos
- Analisa se são bugs reais  
- Classifica severidade e categoria
- **Combina**: LogReceiver + BugAnalyser (economiza custos AI)

### 2. 📋 IssueManagerAgent  
- Cria rascunho da issue
- Revisa qualidade automaticamente
- Refina baseado em feedback
- Publica no GitHub
- **Combina**: IssueDrafter + Reviewer + Refiner + Creator (economiza custos AI)

### 3. 🔔 NotificationAgent
- Gera notificações personalizadas
- Envia para Discord/Slack
- Gerencia retry automático

### 🎼 BugFinderSystem (Orquestrador)
- Coordena todo o fluxo
- Integração com Google ADK
- Interface web e CLI
- Monitoramento e métricas

## ⚙️ Configurações Avançadas

### Análise de Qualidade

```bash
# Confiança mínima para criar issue
MINIMUM_CONFIDENCE_SCORE=0.7

# Habilitar revisão automática
ENABLE_ISSUE_REVIEW=true
MAX_REVIEW_ITERATIONS=2

# Detecção de duplicatas
ENABLE_DUPLICATE_DETECTION=true
```

### Rate Limiting

```bash
# GitHub API
GITHUB_RATE_LIMIT_BUFFER=100

# Discord
DISCORD_RATE_LIMIT_PER_MINUTE=30

# Google AI
AI_REQUESTS_PER_MINUTE=60
```

### Processamento

```bash
# Tamanho máximo de log
MAX_LOG_SIZE_MB=10.0

# Timeout por log
MAX_PROCESSING_TIME_MINUTES=10

# Processamento paralelo (experimental)
ENABLE_PARALLEL_PROCESSING=false
```

## 🧪 Exemplos de Uso

### Log de Erro de Banco

```
log: ERROR 2024-01-20 10:30:45 - Database connection failed
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Resultado**: Issue criada com severidade HIGH, categoria DATABASE_ERROR

### Log de Exceção JavaScript

```
log: Uncaught TypeError: Cannot read property 'length' of undefined
    at processData (app.js:45:12)
    at main (app.js:120:5)
```

**Resultado**: Issue criada com passos de reprodução e detalhes técnicos

### Log Informativo

```
log: INFO 2024-01-20 User login successful for user@example.com
```

**Resultado**: Não cria issue (análise identifica como informativo)

## 📊 Monitoramento

### Status do Sistema

```bash
curl -X POST http://localhost:8000/process \
  -d '{"message": "status"}' \
  -H "Content-Type: application/json"
```

### Teste de Integrações

```bash
curl -X POST http://localhost:8000/process \
  -d '{"message": "test"}' \
  -H "Content-Type: application/json"
```

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
bug-finder/
├── src/
│   ├── agents/          # Agentes especializados
│   ├── models/          # Modelos de dados
│   ├── tools/           # Integrações (GitHub, Discord)
│   └── config/          # Configurações e prompts
├── tests/               # Testes unitários
├── examples/            # Exemplos de uso
├── main.py             # Ponto de entrada ADK
└── adk_config.py       # Configuração ADK
```

### Executar Testes

```bash
# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Cobertura
pytest --cov=src tests/
```

### Adicionar Novos Agentes

1. Criar arquivo em `src/agents/`
2. Herdar de `Agent` (ADK)
3. Implementar `@tool` métodos
4. Atualizar `__init__.py`

## 🔍 Troubleshooting

### Erro: "GitHub access token invalid"

```bash
# Verificar token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Gerar novo token em: GitHub Settings > Developer settings > Personal access tokens
# Permissões necessárias: repo, issues
```

### Erro: "Google AI API key invalid"

```bash
# Verificar chave em: https://makersuite.google.com/app/apikey
# Testar API:
curl -X POST https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=YOUR_KEY
```

### Discord webhook não funciona

```bash
# Testar webhook
curl -X POST YOUR_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"content": "Teste do Bug Finder"}'
```

### Performance lenta

- Verificar `GEMINI_TEMPERATURE` (menor = mais rápido)
- Ajustar `GEMINI_MAX_TOKENS`
- Desabilitar `ENABLE_ISSUE_REVIEW` temporariamente

## 📈 Roadmap

- [ ] **Multi-modelo AI** - Suporte Claude, GPT-4
- [ ] **Webhooks** - Receber logs via HTTP
- [ ] **Slack Integration** - Notificações Slack
- [ ] **Métricas** - Dashboard de analytics  
- [ ] **ML Pipeline** - Treinar modelos customizados
- [ ] **Auto-fix** - Sugestões automáticas de correção

## 🤝 Contribuindo

1. Fork o projeto
2. Crie feature branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para branch (`git push origin feature/nova-funcionalidade`)
5. Crie Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Google AI Team** - Agent Development Kit
- **GitHub API** - Integração robusta
- **Discord** - Sistema de notificações
- **Comunidade Open Source** - Inspiração e feedback

## 📋 Resumo dos Comandos

### Comandos Principais
```bash
# Interface Web (Recomendado)
adk web agents                    # Inicia UI em http://localhost:8000

# CLI Interativo 
adk run agents/bug_finder         # Terminal interativo

# Desenvolvimento
python main.py                    # Modo standalone para debug
```

### Testes Rápidos
```bash
# Status do sistema
python -c "from src.agents import BugFinderSystem; print(BugFinderSystem().get_system_status())"

# Testar integrações
python -c "from src.agents import BugFinderSystem; print(BugFinderSystem().test_integrations())"
```

---

🐛 **Bug Finder** - Transformando logs em insights, bugs em soluções!