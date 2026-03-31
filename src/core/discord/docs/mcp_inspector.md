# Como Usar MCP Inspector

## O que é?

**MCP Inspector** é uma ferramenta interativa de desenvolvimento para testar e debugar servidores MCP (Model Context Protocol).

**Funcionalidades:**
- Conectar a servidores MCP (stdio ou HTTP)
- Listar resources, prompts e tools
- Testar tools com inputs customizados
- Monitorar notifications em tempo real
- Interface web interativa

---

## Instalação

```bash
# Via npx (recomendado)
npx @modelcontextprotocol/inspector --help

# Ou instalar globalmente
npm install -g @modelcontextprotocol/inspector
```

---

## Usando com Servidor Python (Discord MCP)

### Método 1: Python com uv

```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory src/core/discord \
  run \
  discord-server \
  # ou o nome do módulo principal
```

### Método 2: Python direto

```bash
npx @modelcontextprotocol/inspector \
  python \
  -m \
  src.core.discord.server \
  --token $DISCORD_TOKEN
```

### Método 3: Script wrapper

```bash
npx @modelcontextprotocol/inspector \
  python \
  run_discord_mcp.py
```

---

## Interface do Inspector

Após rodar o comando, uma interface web abrirá em `http://localhost:5173`

### Abas Disponíveis

| Aba | Função |
|-----|--------|
| **Resources** | Lista resources disponíveis, mostra metadata, permite inspecionar conteúdo |
| **Prompts** | Mostra prompt templates, argumentos, permite testar e ver preview |
| **Tools** | Lista tools, schemas, descriptions; permite testar com inputs customizados |
| **Notifications** | Agrega logs e notifications recebidas do servidor |

---

## Testando Discord MCP

### 1. Conectar ao Servidor

```bash
npx @modelcontextprotocol/inspector python run_discord_mcp.py
```

O Inspector irá:
- Iniciar o servidor Discord MCP
- Abrir interface web em `http://localhost:5173`
- Conectar automaticamente ao servidor

### 2. Explorar Tools

Na aba **Tools**, você verá:

| Tool | Descrição | Schema |
|------|-----------|--------|
| `reply` | Envia mensagem para canal Discord | chat_id, text, files, reply_to |
| `fetch_messages` | Busca histórico de mensagens | chat_id, limit |
| `send_buttons` | Envia embed com botões | chat_id, title, buttons |
| `react` | Adiciona emoji reaction | chat_id, message_id, emoji |
| `edit_message` | Edita mensagem do bot | chat_id, message_id, content |

### 3. Testar uma Tool

1. Clique na tool (ex: `send_buttons`)
2. Preencha os argumentos:
```json
{
  "chat_id": "1487521449781756066",
  "title": "Teste Inspector",
  "description": "Botão de teste",
  "buttons": [
    {"label": "OK", "style": "success", "custom_id": "ok"},
    {"label": "Cancel", "style": "danger", "custom_id": "cancel"}
  ]
}
```
3. Clique **Execute**
4. Veja o resultado no Discord e na response do Inspector

### 4. Monitorar Notifications

Na aba **Notifications**, você verá em tempo real:
- Logs do servidor
- Notificações MCP enviadas
- Erros e warnings

---

## Debugando com Inspector

### Problema: Tool não aparece

**Verificar:**
1. Tool está registrada no `server.py`?
```python
@self.mcp_server.list_tools()
async def list_tools():
    return get_tool_definitions()
```

2. Tool está em `TOOL_HANDLERS`?
```python
# presentation/tools/__init__.py
TOOL_HANDLERS = {
    "reply": (handle_reply, TOOL_DEFINITION),
    # ...
}
```

### Problema: Tool falha na execução

**No Inspector:**
1. Clique na tool
2. Execute com argumentos de teste
3. Veja o erro na response

**Ver logs:**
- Aba **Notifications** mostra stack trace
- Console do Inspector mostra stderr

### Problema: Notification não chega

**No Inspector:**
1. Aba **Notifications**
2. Procure por `notifications/claude/channel`
3. Verifique o payload enviado

---

## Comandos Úteis

```bash
# Inspector com porta customizada
npx @modelcontextprotocol/inspector --port 3000 python run_discord_mcp.py

# Ver versão
npx @modelcontextprotocol/inspector --version

# Help
npx @modelcontextprotocol/inspector --help

# Modo verbose
MCP_LOG_LEVEL=debug npx @modelcontextprotocol/inspector python run_discord_mcp.py
```

---

## Comparação: Inspector vs Debug Manual

| Aspecto | Inspector | Debug Manual |
|---------|-----------|--------------|
| Testar tools | Interface visual, preenche JSON | Editar código, print statements |
| Ver notifications | Aba dedicada, tempo real | Tail de log files |
| Explorar schema | Documentation integrada | Ler código fonte |
| Testar rápido | Click & execute | Requer restart do servidor |
| Stack trace | Visual colorido | Console preto e branco |

---

## Exemplo Completo: Testar send_buttons

1. **Iniciar Inspector:**
```bash
npx @modelcontextprotocol/inspector python run_discord_mcp.py
```

2. **Abrir:** `http://localhost:5173`

3. **Aba Tools → Clicar em `send_buttons`**

4. **Preencher arguments:**
```json
{
  "chat_id": "SEU_CHAT_ID",
  "title": "Teste via Inspector",
  "buttons": [
    {"id": "test1", "label": "Opção 1", "style": "primary"},
    {"id": "test2", "label": "Opção 2", "style": "success"}
  ]
}
```

5. **Clicar "Execute"**

6. **Verificar:**
   - Discord: Botões aparecem?
   - Inspector: Response mostra sucesso?
   - Notifications: Notificação MCP enviada?

---

## Referências

- **Doc oficial:** https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/docs/tools/inspector.mdx
- **Repo:** https://www.npmjs.com/package/@modelcontextprotocol/inspector

---

> "Inspector é o browser dev tools do MCP" – made by Sky 🕵️✨
