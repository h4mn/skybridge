# Agente Channel/Push - Pesquisa e Implementação

## Resumo Executivo

**VEREDITO: GO (Com Ressalvas)**

É possível criar um subagente/auxiliar que simula um "channel" de notificações funcionais para Claude Code, mas com **limitações importantes**:

1. **PUSH via MCP NÃO funciona** - Limitação do cliente Claude Code Desktop
2. **POLLING via MCP Tools funciona** - Implementação já existe no projeto
3. **File-based signaling funciona** - Pode ser usado como alternativa
4. **Subagentes NÃO enviam mensagens diretas** - Limitação arquitetural

**Recomendação:** Usar **Polling via MCP Tools** (já implementado em `discord-mcp-tool-polling-example.py`) + **File-based signaling** como backup.

---

## Iterações de Pesquisa

### Iteração 1: Arquitetura de Subagentes Claude Code

**Objetivo:** Entender como criar/lançar subagentes e suas capacidades.

**Descobertas:**
- Subagentes são criados via `Agent` tool
- Cada subagente roda em contexto isolado
- **COMUNICAÇÃO UNIDIRECIONAL:** Apenas sessão principal → subagente
- Subagente **NÃO pode enviar mensagens de volta** para a sessão principal
- Output do subagente vai apenas para o usuário (não para outras sessões)

**Limitação Crítica:**
```
Sessão Principal → [SendMessage] → Subagente
Subagente → [NÃO PODE] → Sessão Principal
```

**Conclusão:** Subagentes não servem para notificações push. Precisamos de outra abordagem.

---

### Iteração 2: Mecanismos de Comunicação

**Objetivo:** Descobrir alternativas para comunicação bidirecional.

**Opções Exploradas:**

1. **Tool Outputs**
   - Subagente retorna output via tool calls
   - Apenas quando solicitado pela sessão principal
   - **Problema:** Não é push, é pull

2. **Arquivos Compartilhados**
   - Várias sessões podem ler/escrever os mesmos arquivos
   - **Viável:** File-based signaling
   - **Desafio:** Needs polling ou watchdog

3. **IPC (Inter-Process Communication)**
   - Named pipes, sockets, shared memory
   - **Complexo:** Requer infraestrutura adicional

4. **MCP Notifications**
   - JSON-RPC 2.0 notifications (id: null)
   - **LIMITAÇÃO:** Cliente Claude Code Desktop não processa

**Conclusão:** File-based signaling é a opção mais viável.

---

### Iteração 3: Polling Eficiente

**Objetivo:** Determinar melhor estratégia de polling.

**Abordagens Comparadas:**

| Método | Latência | Overhead | Complexidade |
|--------|----------|----------|--------------|
| Polling arquivo (1s) | Baixa | Alto | Baixa |
| Polling arquivo (10s) | Média | Médio | Baixa |
| Watchdog (inotify) | Imediata | Baixo | Média |
| SQLite + trigger | Variável | Médio | Alta |

**Recomendação:**
- **Para testes/desenvolvimento:** Polling simples (1-5s)
- **Para produção:** Watchdog ou polling otimizado (10-30s)

**Trade-off Performance/Atualidade:**
```
1s polling  → Muito rápido, mas alto overhead
10s polling → Aceitável para maioria dos casos
30s polling → Lento, mas baixo overhead
```

---

### Iteração 4: File-Based Signaling

**Objetivo:** Implementar comunicação via arquivos.

**Implementações Possíveis:**

1. **Arquivo de Estado (JSON)**
```python
# discord_notifications.json
{
  "last_update": "2026-04-02T10:30:00",
  "notifications": [
    {"id": "1", "type": "button", "content": "..."}
  ]
}
```

2. **JSONL (Append-Only)**
```python
# discord_notifications.jsonl
{"id": "1", "type": "button", "content": "..."}
{"id": "2", "type": "message", "content": "..."}
```

3. **SQLite com Polling**
```python
# discord_notifications.db
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    type TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Vantagens File-Based:**
- Simples de implementar
- Fácil de debug (pode inspect arquivo)
- Persistência automática
- Multi-processo safe (com locks)

**Desvantagens:**
- Requer polling ou watchdog
- Overhead de I/O
- Concorrência precisa de cuidado

---

### Iteração 5: Agente "Channel" Design

**Objetivo:** Definir arquitetura do agente.

**Responsabilidades:**
1. Polling de fonte (Discord MCP, arquivo, etc.)
2. Filtragem e formatação de mensagens
3. Detecção de mudanças (hash/timestamp)
4. Entrega para sessão principal

**Arquitetura Recomendada:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Sessão Principal Claude Code              │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ polling (1-10s)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tool (get_notifications)              │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ stdio (JSON-RPC)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Discord MCP Server (Background)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Discord Bot ←→ Notification Queue (in-memory)        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Discord API                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Iteração 6: Implementação Prática

**Objetivo:** Código completo do agente.

**Status:** **JÁ IMPLEMENTADO** em `docs/research/discord-mcp-tool-polling-example.py`

**Como Funciona:**
1. Bot Discord captura interações
2. Armazena em fila (in-memory)
3. MCP Tool `get_discord_notifications` retorna fila
4. Claude Code chama tool periodicamente (polling)

**Exemplo de Uso:**
```python
# Claude Code prompt:
"Verifica se há novas notificações Discord e me resume."

# Tool call:
get_discord_notifications(limit=10, clear=True)

# Resposta:
{
  "count": 3,
  "notifications": [...],
  "summary": "3 button(s)"
}
```

---

### Iteração 7: Alternativas ao Polling

**Objetivo:** Explorar outras opções.

**Opções:**

1. **Webhooks Locais**
   - Requer servidor HTTP local
   - Claude Code precisa enviar para URL
   - **Complexo:** Claude Code não suporta nativamente

2. **Server-Sent Events (SSE)**
   - HTTP streaming de servidor → cliente
   - **LIMITAÇÃO:** MCP usa stdio, não HTTP
   - Não aplicável ao contexto

3. **WebSocket Bidirecional**
   - Comunicação full-duplex
   - **LIMITAÇÃO:** MCP usa stdio, não WebSocket
   - Não aplicável ao contexto

4. **Memcached/Redis Pub/Sub**
   - Infraestrutura adicional
   - **Overhead:** Requer serviço externo
   - Viável mas complexo

**Conclusão:** Polling via MCP Tools é a opção mais simples e funcional.

---

### Iteração 8: Casos de Uso Reais

**Objetivo:** Exemplos de produção.

**Projetos Similares:**

1. **GitHub CLI (gh)**
   - Usa polling para notificações
   - Intervalo: 2-5 minutos
   - Justificativa: Não precisa ser real-time

2. **Slack CLI**
   - Polling via API
   - Cache local para performance
   - Intervalo configurável

3. **Discord.py (self-bot)**
   - Event-based (WebSocket)
   - Não usa polling
   - **Nota:** Discord.py já é event-based!

**Lições Aprendidas:**
- Polling é aceitável para notificações não-críticas
- Cache local reduz overhead
- Event-based é melhor quando disponível
- Discord.py JÁ usa WebSocket (event-based)

---

### Iteração 9: Limitações e Riscos

**Objetivo:** O que PODE dar errado.

**Limitações Conhecidas:**

1. **Claude Code Desktop**
   - Não processa notificações MCP push
   - Apenas responde a tool calls
   - **Workaround:** Polling via tools

2. **Polling Overhead**
   - CPU/IO periódicos
   - **Mitigação:** Intervalo adequado (10-30s)

3. **Latência**
   - Não é real-time verdadeiro
   - **Aceitável:** Para maioria dos casos

4. **Escalabilidade**
   - In-memory queue não persiste
   - **Workaround:** SQLite/file-based

5. **Concorrência**
   - Múltiplas sessões podem competir
   - **Mitigação:** Locks ou filas separadas

**Riscos:**

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Polling excessivo | Média | Alto | Intervalo mínimo 5s |
| Perda de notificações | Baixa | Médio | Persistência (SQLite) |
| Race conditions | Média | Médio | Locks/file atomic ops |
| Crash do servidor | Baixa | Alto | Auto-restart + persistência |

---

### Iteração 10: Veredito Final e Plano

**VEREDITO: GO (COM RESSALVAS)**

**O QUE FUNCIONA:**
✅ Polling via MCP Tools
✅ File-based signaling
✅ Discord.py event-based (WebSocket)

**O QUE NÃO FUNCIONA:**
❌ Push notifications via MCP
❌ Subagentes enviando mensagens
❌ SSE/WebSocket com MCP stdio

**IMPLEMENTAÇÃO RECOMENDADA:**

```
┌──────────────────────────────────────────────────────────────┐
│  FASE 1: Polling via MCP Tools (JÁ IMPLEMENTADO)            │
├──────────────────────────────────────────────────────────────┤
│  - discord-mcp-tool-polling-example.py                       │
│  - Tool: get_discord_notifications()                         │
│  - Claude Code chama periodicamente (polling sob demanda)    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  FASE 2: File-Based Signaling (OPCIONAL)                     │
├──────────────────────────────────────────────────────────────┤
│  - Persistência em SQLite                                    │
│  - Watchdog para detecção instantânea                        │
│  - Multi-sessão safe                                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  FASE 3: Auto-Prompting (FUTURO)                            │
├──────────────────────────────────────────────────────────────┤
│  - Cron/scheduler para polling automático                    │
│  - Integração com loop principal Claude Code                 │
└──────────────────────────────────────────────────────────────┘
```

**PASSOS PRÁTICOS:**

1. **IMEDIATO:** Usar implementação polling existente
2. **CURTO PRAZO:** Adicionar persistência SQLite
3. **MÉDIO PRAZO:** Implementar watchdog (se necessário)
4. **LONGO PRAZO:** Aguardar suporte nativo push no Claude Code

**MÉTRICAS DE SUCESSO:**
- Latência < 10s (polling 5s)
- Zero perda de notificações (persistência)
- Overhead CPU < 1%
- Facilidade de uso (prompt simples)

---

## Implementação Completa

### Código: `agent_channel_implementation.py`

Ver arquivo `docs/research/agent_channel_implementation.py` para implementação completa com:

1. **File-based signaling** via SQLite
2. **Watchdog** para detecção instantânea
3. **Polling otimizado** com cache
4. **Multi-sessão safe** com locks
5. **Persistência** automática

---

## Guia de Uso

### Opção 1: Polling via MCP Tools (SIMPLES)

**Passo 1:** Iniciar servidor MCP
```bash
python discord_channel_mcp.py
```

**Passo 2:** No Claude Code, usar prompt:
```
"Verifica se há novas notificações Discord."
```

**Vantagens:**
- ✅ Já implementado
- ✅ Funciona imediatamente
- ✅ Sem dependências adicionais

**Desvantagens:**
- ❌ Requer polling manual
- ❌ Não é real-time

---

### Opção 2: File-Based Signaling (AVANÇADO)

**Passo 1:** Iniciar servidor com persistência
```bash
python agent_channel_implementation.py --mode file --path ~/.claude/notifications.db
```

**Passo 2:** Configurar watchdog (opcional)
```bash
python agent_channel_implementation.py --mode watchdog --interval 5
```

**Passo 3:** No Claude Code, usar tool:
```
"Monitora notificações Discord em background."
```

**Vantagens:**
- ✅ Persistência
- ✅ Multi-sessão
- ✅ Detecção instantânea (watchdog)

**Desvantagens:**
- ❌ Mais complexo
- ❌ Requer configuração

---

### Opção 3: Polling Automático (FUTURO)

**Passo 1:** Criar skill/schedule
```bash
# No Claude Code settings.json:
{
  "hooks": {
    "on_tick": "check_discord_notifications",
    "interval": 10
  }
}
```

**Passo 2:** Auto-prompting
```
"A cada 10 segundos, verifica notificações Discord."
```

**Vantagens:**
- ✅ Automático
- ✅ Sem intervenção manual

**Desvantagens:**
- ❌ Requer suporte nativo (não existe ainda)
- ❌ Pode ser intrusivo

---

## Veredito Final

### GO/NO-GO: **GO (COM RESSALVAS)**

**O QUE FUNCIONA HOJE:**
- ✅ Polling via MCP Tools (implementado)
- ✅ Discord.py event-based (WebSocket)
- ✅ File-based signaling (SQLite)

**O QUE NÃO FUNCIONA:**
- ❌ Push notifications via MCP
- ❌ Subagentes enviando mensagens
- ❌ Real-time verdadeiro

**RECOMENDAÇÃO FINAL:**

```
USAR: Polling via MCP Tools (discord-mcp-tool-polling-example.py)

POR QUÊ:
✅ Simples e funcional
✅ Já implementado
✅ Sem overhead adicional
✅ Funciona com Claude Code Desktop

MELHORIAS FUTURAS:
- Adicionar persistência SQLite (se necessário)
- Implementar watchdog (se latência for crítica)
- Aguardar suporte nativo push no Claude Code
```

**DECISÃO:**
Implementar **polling via MCP Tools** como solução principal, com **file-based signaling** (SQLite) como backup para persistência e multi-sessão.

---

## Referências

### Código Existente no Projeto

1. **`discord_channel_mcp.py`**
   - Servidor MCP com Discord bot
   - Notificações via `_notification_handler`
   - **LIMITAÇÃO:** Push não funciona no cliente

2. **`discord-mcp-tool-polling-example.py`**
   - Implementação POLLING funcional
   - MCP Tool `get_discord_notifications()`
   - **RECOMENDADO:** Usar este como base

3. **`run_discord_mcp.py`**
   - Script de inicialização
   - Carrega configuração de `.env`

### Conceitos Chave

- **MCP (Model Context Protocol):** stdio-based, JSON-RPC 2.0
- **Discord.py:** WebSocket event-based (já é real-time)
- **Polling:** Cliente pergunta periodicamente
- **Push:** Servidor envia sem solicitação
- **Watchdog:** Monitora mudanças em arquivos

### Limitações Técnicas

1. **Claude Code Desktop:**
   - stdio apenas (unidirecional)
   - Não processa notificações push
   - Apenas responde a tool calls

2. **MCP Protocol:**
   - JSON-RPC 2.0 via stdio
   - Server não pode iniciar mensagens
   - Apenas request/response

3. **Subagentes:**
   - Comunicação unidirecional
   - Não enviam mensagens de volta
   - Output vai apenas para usuário

---

## Conclusão

**É possível criar um agente de notificações funcionais para Claude Code usando polling via MCP Tools.**

**A solução já está implementada** em `discord-mcp-tool-polling-example.py` e pode ser usada imediatamente.

**Melhorias futuras:** Persistência SQLite, watchdog, e aguardar suporte nativo push no Claude Code.

> "A simplicidade é o último grau de sofisticação" – made by Sky 🚀
