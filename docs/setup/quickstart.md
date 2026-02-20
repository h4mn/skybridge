# Quickstart Skybridge - PRD026

**Tempo estimado:** 15-30 minutos
**Pré-requisitos:** Python 3.11+, Git

---

## 🚀 Setup Rápido

### 1. Clonar e Entrar no Diretório

```bash
git clone <repo-url>
cd skybridge-prd026
```

### 2. Criar Ambiente Virtual

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar Dependências

```bash
pip install -e ".[cli,api,webhooks,kanban,trelloat]"
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar .env com suas credenciais
```

**Variáveis OBRIGATÓRIAS (mínimo para rodar):**

```bash
# Servidor
SERVER_PORT=8000
ENVIRONMENT=development

# GitHub (opcional - para webhooks reais)
GITHUB_WEBHOOK_SECRET=your_secret_here

# Trello (opcional - para sincronização Kanban)
TRELLO_API_KEY=your_key_here
TRELLO_API_TOKEN=your_token_here
TRELLO_BOARD_ID=your_board_id_here
```

### 5. Iniciar o Servidor

```bash
python -m apps.server.main
```

Você deverá ver:

```
[INFO] Iniciando Skybridge Server v0.13.0.dev
[INFO] KanbanJobEventHandler iniciado e inscrito no EventBus
[INFO] Uvicorn running on http://0.0.0.0:8000
```

### 6. Verificar Health Check

Abra no navegador: http://localhost:8000/docs

---

## ✅ Validação Rápida

### Teste 1: Verificar Kanban Auto-Inicialização

O servidor deve criar automaticamente `workspace/core/data/kanban.db` com 6 listas:

```
Listas criadas:
- 📥 Issues
- 🧠 Brainstorm
- 📋 A Fazer
- 🚧 Em Andamento
- 👁️ Em Revisão
- 🚀 Publicar
```

### Teste 2: Enviar Webhook de Teste

```bash
curl -X POST http://localhost:8000/api/webhooks/github \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "issue": {
      "number": 999,
      "title": "Teste Quickstart"
    },
    "repository": {"full_name": "test/repo"},
    "sender": {"login": "test"}
  }'
```

### Teste 3: Verificar Card Criado

```bash
python -c "
import sqlite3
conn = sqlite3.connect('workspace/core/data/kanban.db')
cursor = conn.cursor()
cursor.execute('SELECT title FROM cards')
print('Cards:', cursor.fetchall())
conn.close()
"
```

---

## 📋 Estrutura de Projeto

```
skybridge-prd026/
├── apps/
│   ├── api/          # FastAPI server
│   └── cli/          # CLI interface
├── docs/
│   ├── setup/        # Setup docs
│   ├── adr/          # Architecture Decision Records
│   └── prd/          # Product Requirements
├── src/
│   ├── core/         # Domain logic
│   ├── infra/        # Infrastructure
│   └── runtime/      # Bootstrap & config
├── tests/
│   ├── unit/         # Unit tests
│   ├── integration/  # Integration tests
│   └── e2e/          # End-to-end tests
└── workspace/        # Multi-workspace data
```

---

## 🔧 Troubleshooting

### Erro: "Porta 8000 em uso"

**Solução:** Matar processo ou mudar porta

```bash
# Mudar porta no .env
SERVER_PORT=8001
```

### Erro: "TRELLO_API_KEY não configurado"

**Solução:** O sistema funciona sem Trello! Apenas a sincronização bidirecional será desabilitada.

Para habilitar Trello:
1. Acesse https://trello.com/app-key
2. Copie API Key
3. Clique em "Token" para gerar token
4. Adicione ao `.env`

### Erro: "Module not found"

**Solução:** Reinstalar dependências

```bash
pip install -e ".[cli,api,webhooks,kanban,trelloat]"
```

---

## 📖 Próximos Passos

1. **Ler a documentação:**
   - `docs/prd/PRD026.md` - Integração Kanban com Fluxo Real
   - `docs/adr/ADR022.md` - Servidor Unificado

2. **Rodar os testes:**
   ```bash
   pytest tests/ -v
   ```

3. **Explorar a API:**
   - http://localhost:8000/docs - Swagger UI
   - http://localhost:8000/api/kanban/cards - Kanban Cards API

---

## 💡 Dicas

- **Hot Reload:** O servidor recarrega automaticamente quando você modifica arquivos
- **Logs:** Logs estruturados com cores para facilitar debug
- **Multi-workspace:** Cada workspace tem seu `kanban.db` isolado

---

> "A simplicidade é o último grau de sofisticação" – made by Sky 🚀
