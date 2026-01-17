# Guia de Setup - Webhooks Reais do GitHub

Este guia explica como configurar webhooks reais do GitHub para testar a integração com Trello.

## 📋 Pré-requisitos

- [x] Python 3.11+
- [x] Conta no GitHub com acesso ao repositório
- [x] Conta no Trello com API credentials
- [x] ngrok instalado (https://ngrok.com/download)

## 🚀 Passo a Passo

### 1. Configurar Variáveis de Ambiente

No arquivo `.env` da worktree `kanban`:

```bash
# Trello Credentials (já configurado)
TRELLO_API_KEY=24a326b2de02792242770f6a1fea202b
TRELLO_API_TOKEN=ATTA331f896c26e8bcbc836488a24b013fa0b480ad0cafaf0a486acc6819cb04e796DEC6FBEA
TRELLO_BOARD_ID=696aadc544fecc164175024c

# GitHub Webhook Secret (opcional, mas recomendado)
GITHUB_WEBHOOK_SECRET=your-random-secret-here

# Server
HOST=0.0.0.0
PORT=8000
```

**Gerar secret seguro:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Instalar Dependências

```bash
cd B:\_repositorios\skybridge-worktrees\kanban
pip install fastapi uvicorn
```

### 3. Iniciar ngrok

Em um terminal separado:

```bash
ngrok http 8000
```

**Copie a URL HTTPS** gerada, exemplo:
```
https://abc1-230-45-67-89.ngrok-free.app
```

### 4. Iniciar Servidor Webhook

No terminal principal:

```bash
cd B:\_repositorios\skybridge-worktrees\kanban
python src/core/webhooks/infrastructure/github_webhook_server.py
```

Você deve ver:
```
🚀 SKYBRIDGE WEBHOOK SERVER
================================================================================

Este servidor recebe webhooks do GitHub e cria cards no Trello.

📋 Configuração:
  Trello: ✅ Configurado
  Webhook Secret: ✅ Configurado

🔗 Para configurar webhook no GitHub:
  ...
```

### 5. Configurar Webhook no GitHub

1. Vá ao repositório no GitHub
2. **Settings** → **Webhooks** → **Add webhook**
3. Preencha:

| Campo | Valor |
|-------|-------|
| **Payload URL** | `https://SEU-NGROK-URL.ngrok-free.app/webhook/github` |
| **Content type** | `application/json` |
| **Secret** | (opcional) mesmo valor de `GITHUB_WEBHOOK_SECRET` |
| **Events** | Issues → Select "Issues only" → Check "opened", "edited", "closed" |

4. Clique em **Add webhook**

### 6. Testar

No GitHub, crie uma issue nova ou reabra uma issue existente.

**O que deve acontecer:**
1. GitHub envia webhook para seu servidor via ngrok
2. Servidor recebe e processa
3. Card criado no Trello automaticamente
4. Logs no terminal mostram o progresso

**Logs esperados:**
```
📨 Webhook recebido: issues.opened | delivery: 12345678-1234-1234-1234-123456789abc
✅ Card Trello criado: 696bxxxx para issue #42
✅ Webhook processado: job_id=github-issues.opened-abc12345
```

### 7. Verificar no Trello

Vá ao board do Trello configurado e veja:
- Card criado com título da issue
- Descrição com metadados (issue URL, autor, etc)
- Comentário inicial "Aguardando processamento..."

## 🔧 Troubleshooting

### ngrok não funciona
- Verifique se você tem conta no ngrok (gratuita)
- Autentique: `ngrok config add-authtoken YOUR_TOKEN`

### Webhook retorna 401
- Verifique se `GITHUB_WEBHOOK_SECRET` é igual no .env e na configuração do GitHub

### Webhook retorna 422
- Verifique os logs no terminal para ver o erro específico
- Pode ser que o payload não tem os campos esperados

### Card não é criado no Trello
- Verifique se `TRELLO_API_KEY`, `TRELLO_API_TOKEN` e `TRELLO_BOARD_ID` estão corretos
- Verifique se o board existe e você tem acesso

### Erro "ModuleNotFoundError"
- Certifique-se de estar no diretório correto: `B:\_repositorios\skybridge-worktrees\kanban`
- Instale as dependências: `pip install fastapi uvicorn python-dotenv httpx`

## 🎯 Próximos Passos

Após testar webhooks reais:

1. **Verificar JobOrchestrator** - Modificar para atualizar cards durante execução
2. **Adicionar tratamento de erros** - Atualizar cards quando jobs falham
3. **Documentar arquitetura** - Criar ADR sobre a integração

## 📚 Referências

- GitHub Webhooks: https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks
- FastAPI: https://fastapi.tiangolo.com/
- ngrok: https://ngrok.com/docs
