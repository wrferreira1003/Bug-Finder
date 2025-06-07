# Google AI Agent Development Kit Setup

## 📦 Instalação do Google AI ADK

### 1. Instalar o SDK (quando disponível):

```bash
pip install google-ai-adk
```

### 2. Configurar credenciais:

```bash
# Configurar Google Cloud credentials
gcloud auth application-default login

# Ou definir variável de ambiente
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### 3. Inicializar projeto ADK:

```bash
# Criar novo projeto ADK
google-ai-adk init bug-finder-project

# Ou migrar projeto existente
google-ai-adk migrate --project-path /path/to/bug-finder
```

## 🚀 Comandos do Google AI ADK

### Desenvolvimento:

```bash
# Executar com ADK
google-ai-adk run --project bug-finder

# Interface de desenvolvimento
google-ai-adk dev --ui

# Debug mode
google-ai-adk debug --verbose

# Hot reload
google-ai-adk dev --watch
```

### Deploy:

```bash
# Deploy para Google Cloud
google-ai-adk deploy --env production

# Deploy local
google-ai-adk serve --port 8080

# Deploy com interface
google-ai-adk deploy --with-ui
```

### Monitoramento:

```bash
# Logs em tempo real
google-ai-adk logs --follow

# Métricas
google-ai-adk metrics --dashboard

# Health check
google-ai-adk health
```

## 🔧 Integração com Projeto Atual

### 1. Estrutura de arquivos ADK:

```
bug-finder/
├── adk.yaml              # Configuração ADK
├── agents/               # Agentes existentes
├── tools/               # Ferramentas existentes
├── models/              # Modelos de dados
└── web/                 # Interface web
```

### 2. Arquivo de configuração `adk.yaml`:

```yaml
name: bug-finder
version: 1.0.0
runtime: python3.11

agents:
  - name: BugFinderAgent
    file: src/agents/bug_finder_agent.py
    entrypoint: BugFinderAgent

  - name: BugAnalyserAgent
    file: src/agents/bug_analyser_agent.py
    entrypoint: BugAnalyserAgent

tools:
  - name: GitHubTool
    file: src/tools/github_tool.py

  - name: DiscordTool
    file: src/tools/discord_tool.py

interface:
  enabled: true
  port: 8000
  static_files: web/static

environment:
  GEMINI_API_KEY: ${GEMINI_API_KEY}
  GITHUB_TOKEN: ${GITHUB_TOKEN}
  DISCORD_WEBHOOK_URL: ${DISCORD_WEBHOOK_URL}
```

### 3. Script de migração:

```python
# scripts/migrate_to_adk.py
import os
import yaml
from pathlib import Path

def create_adk_config():
    config = {
        'name': 'bug-finder',
        'version': '1.0.0',
        'runtime': 'python3.11',
        'agents': [
            {
                'name': 'BugFinderAgent',
                'file': 'src/agents/bug_finder_agent.py',
                'entrypoint': 'BugFinderAgent'
            }
        ],
        'tools': [
            {
                'name': 'GitHubTool',
                'file': 'src/tools/github_tool.py'
            }
        ],
        'interface': {
            'enabled': True,
            'port': 8000
        }
    }

    with open('adk.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

if __name__ == "__main__":
    create_adk_config()
    print("✅ Configuração ADK criada!")
```
