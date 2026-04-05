# MCP SSE/HTTP Transport - Síntese Crítica

**Data:** 2026-04-02
**Status:** 🔄 Evolução da Pesquisa
**Base:** Pesquisas anteriores + Análise código MCP SDK real

---

## Resumo Executivo

**Veredito Atualizado:** ⚠️ **Mudança de Estratégia**

A pesquisa anterior identificou SSE como solução, mas análise do código real do MCP SDK revelou:

1. ✅ **SSE funciona** para push notifications (confirmado no código)
2. ❌ **SSE está deprecated** - documentação oficial recomenda `streamable_http`
3. ✅ **`streamable_http.py` existe** no SDK instalado
4. ⚠️ **Migração é possível** mas requer ajustes na proposta original

---

## 4 Caminhos de Evolução

### A — Tools + Resources (Implementar Agora)

**Status:** ✅ **Viável Imediato**

Combinação de MCP tools com `send_resource_updated()`:

```python
# Quando mensagem chega no Discord
await self._notification_system.on_message(notification)

# Notifica cliente sobre resource atualizado
await session.send_resource_updated("discord://channels/1487929503073173727/messages")
```

**Vantagens:**
- ✅ Funciona via stdio
- ✅ Padrão oficial MCP
- ✅ Cliente pode ler resource quando necessário
- ✅ Multi-canal com URIs separadas

**Implementação:** 2-4 horas

---

### B — Sampling Capability (Subestimado)

**Status:** ⚠️ **Experimental**

Protocolo MCP tem capability `sampling` onde servidor pede ao cliente para gerar completion:

```python
# Quando chega mensagem
await session.create_message(
    messages=[{"role": "user", "content": notification}]
)
```

**Problemas:**
- ⚠️ Mal documentado no Claude Code
- ⚠️ Suporte incerto em versões atuais
- ⚠️ Não é push verdadeiro

**Recomendação:** Aguardar melhor documentação

---

### C — SSE/HTTP Transport (Solução Real)

**Status:** ✅ **GO - Com Correção**

**Descoberta Crítica:** SSE está **deprecated**.

**Transporte Correto:** `streamable_http`

#### Análise Código MCP SDK Real

**Arquivo:** `B:\Programas\Python\Python311\Lib\site-packages\mcp\server\streamable_http.py`

**Diferença Fundamental:**

```python
# stdio: escreve e vai embora
await stdout.write(json + "\n")
await stdout.flush()

# SSE: loop contínuo em task group
async for session_message in write_stream_reader:
    await sse_stream_writer.send({"event": "message", "data": ...})

# streamable_http: HTTP persistente com stream bidirecional
# (código real do SDK instalado)
```

#### Configuração Claude Code

**Antes (stdio):**
```json
{
  "mcpServers": {
    "discord": {
      "command": "python",
      "args": ["run_discord_mcp.py"]
    }
  }
}
```

**Depois (HTTP):**
```bash
claude mcp add --transport http discord http://localhost:8765/mcp
```

Ou via config:
```json
{
  "mcpServers": {
    "discord": {
      "type": "http",
      "url": "http://localhost:8765/mcp",
      "transport": "streamable_http"
    }
  }
}
```

**Mudança de Arquitetura:**

| Aspecto | stdio | HTTP/Streamable |
|---------|-------|-----------------|
| Quem inicia | Claude Code | Manual/daemon |
| Push notifications | ❌ Ignoradas | ✅ Funcionam |
| Múltiplos clientes | ❌ Impossível | ✅ Suportado |
| Reconexão | N/A | ✅ Automática |

---

### D — Daemon Externo (Engenharia de Sistema)

**Status:** ✅ **Viável**

Processo Python separado monitora arquivo JSONL com `watchfiles` e dispara notificações nativas do OS:

```python
# Discord → JSONL → watchdog → win10toast → Notificação Windows
```

**Vantagens:**
- ✅ Completamente desacoplado do MCP
- ✅ Notificações nativas do sistema
- ✅ Zero dependência de capabilities do cliente

**Desvantagens:**
- ⚠️ Requer setup adicional
- ⚠️ Usuário precisa voltar ao Claude Code manualmente

**Implementação:** 3-5 horas

---

## Implementação streamable_http

### 1. Mudanças em `server.py`

#### 1a. Broadcast para múltiplas conexões

```python
class DiscordMCPServer:
    def __init__(self):
        # ... código existente ...
        self._write_stream = None              # stdio (compatibilidade)
        self._http_write_streams: list = []    # HTTP: múltiplos clientes
```

#### 1b. `send_notification()` agnóstico

```python
async def send_notification(self, method: str, params: dict) -> None:
    notification = JSONRPCNotification(
        jsonrpc="2.0",
        method=method,
        params=params,
    )
    message = JSONRPCMessage(notification)

    # HTTP mode: broadcast para todos
    if self._http_write_streams:
        dead = []
        for ws in list(self._http_write_streams):
            try:
                await ws.send(message)
            except Exception as e:
                logger.warning(f"HTTP stream morto: {e}")
                dead.append(ws)
        for ws in dead:
            self._http_write_streams.remove(ws)
        return

    # stdio mode: fallback
    if self._write_stream is None:
        logger.warning("Nenhum write_stream disponível")
        return
    try:
        await self._write_stream.send(message)
    except Exception as e:
        logger.error(f"Erro stdio: {e}")
```

#### 1c. Novo método `run_http()`

```python
async def run_http(
    self,
    token: str,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """
    Executa servidor com HTTP transport (streamable).

    Alternativa ao run() (stdio) que habilita push notifications reais.
    """
    from mcp.server.streamable_http import streamable_http
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    import uvicorn

    # Handlers Discord (idêntico ao run())
    # [código omitido - igual ao stdio]

    # Handlers MCP (idêntico ao run())
    # [código omitido - igual ao stdio]

    # ============================================================================
    # HTTP Transport
    # ============================================================================
    async def handle_root(request):
        return await streamable_http(request, self.mcp_server)

    app = Starlette(
        routes=[
            Route("/", endpoint=handle_root, methods=["POST", "GET"]),
        ],
    )

    # Inicia servidor
    sys.stderr.write(f"[HTTP] Iniciando em http://{host}:{port}\n")
    sys.stderr.flush()

    await self.discord_client.login(token)

    uv_config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
    )
    uv_server = uvicorn.Server(uv_config)

    # Tasks paralelas
    poller_task = asyncio.create_task(approval_poller())
    message_poller_task = asyncio.create_task(self._poll_messages())

    try:
        await asyncio.gather(
            uv_server.serve(),
            self.discord_client.connect(),
        )
    finally:
        self._shutdown = True
        poller_task.cancel()
        message_poller_task.cancel()
```

### 2. Novo Runner

```python
#!/usr/bin/env python
# run_discord_mcp_http.py
"""
Discord MCP Server — HTTP Transport.

Uso:
    python run_discord_mcp_http.py [--host 127.0.0.1] [--port 8765]

Configure no Claude Code:
    claude mcp add --transport http discord http://localhost:8765/mcp
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Carrega .env
state_dir = Path(os.environ.get("DISCORD_STATE_DIR",
    Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

token = os.environ.get("DISCORD_BOT_TOKEN")
if not token:
    sys.stderr.write("DISCORD_BOT_TOKEN não encontrado\n")
    sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=8765)
args = parser.parse_args()

from src.core.discord.server import DiscordMCPServer

server = DiscordMCPServer()

try:
    asyncio.run(server.run_http(token, host=args.host, port=args.port))
except KeyboardInterrupt:
    pass
except Exception as e:
    sys.stderr.write(f"[FATAL] {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
```

---

## Plano de Implementação

### Fase 1: Tools + Resources (Esta semana)
- [ ] Implementar `send_resource_updated()` no servidor
- [ ] Criar resources por canal: `discord://channels/{id}/messages`
- [ ] Testar com Claude Code Desktop
- **Esforço:** 2-4 horas
- **Risco:** Baixo

### Fase 2: HTTP Transport (Este mês)
- [ ] Implementar `run_http()` em `server.py`
- [ ] Criar `run_discord_mcp_http.py`
- [ ] Testar push notifications reais
- [ ] Atualizar documentação
- **Esforço:** 8-12 horas
- **Risco:** Médio

### Fase 3: Daemon Externo (Se necessário)
- [ ] Implementar watchdog com `watchfiles`
- [ ] Integrar com `win10toast`/`winotify`
- [ ] Setup como serviço Windows
- **Esforço:** 3-5 horas
- **Risco:** Baixo

---

## Recomendação Final

**Imediato:** Implementar **Tools + Resources** (Fase 1)

**Curto Prazo:** Migrar para **HTTP Transport** (Fase 2)

**Futuro:** Considerar **Daemon Externo** se notificações nativas forem críticas

---

## Correções à Pesquisa Original

| Afirmação Original | Status | Correção |
|--------------------|--------|----------|
| SSE resolve push | ✅ Correta | Mas SSE está deprecated |
| SseServerTransport é API certa | ⚠️ Parcial | Use `streamable_http` |
| Claude Code suporta --transport sse | ✅ Correta | Mas --transport http é recomendado |
| Push funciona com SSE | ✅ Correta | Confirmado no código |

---

## Referências

**Código MCP SDK Real:**
- `streamable_http.py` - `B:\Programas\Python\Python311\Lib\site-packages\mcp\server\streamable_http.py`
- `sse.py` - `B:\Programas\Python\Python311\Lib\site-packages\mcp\server\sse.py`
- `stdio.py` - `B:\Programas\Python\Python311\Lib\site-packages\mcp\server\stdio.py`

**Documentação:**
- Claude Code: code.claude.com
- MCP Spec: modelcontextprotocol.io

---

> "A verdade está no código, não na documentação" – made by Sky 🔍

> "Saber admitir erro é tão importante quanto acertar" – made by Sky 🎯
