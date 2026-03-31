# Como Debugar MCP - Discord Server

## 1. Logs de Console (Print Statements)

O código já tem vários prints de debug:

```python
# server.py
print(f"[DEBUG on_interaction_create] Interaction type: {interaction.type}")
print(f"[DEBUG] É componente! Fazendo defer...")
print(f"[DEBUG] Chamando adapter...")
print(f"[DEBUG] Notificação MCP enviada: {custom_id}")
```

**Ver em tempo real:**
```bash
python run_discord_mcp.py
```

---

## 2. Arquivo de Debug de Interações

```python
# server.py:377
debug_log = Path("discord_interaction_debug.log")
debug_log.write_text(f"[{datetime.now().isoformat()}] HANDLER CHAMADO! Type: {interaction.type}\n", mode='a')
```

**Monitorar em tempo real:**
```bash
tail -f discord_interaction_debug.log
```

---

## 3. MCP Server Logs

**Ativar logging detalhado:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Ou em variável de ambiente:**
```bash
MCP_LOG_LEVEL=DEBUG python run_discord_mcp.py
```

---

## 4. Stdio Stream Capture

O MCP usa stdio para comunicação. Para ver o que está sendo enviado:

```python
# server.py:312-343 - send_notification()
async def send_notification(self, method: str, params: dict) -> None:
    print(f"[DEBUG send_notification] Method: {method}, Params: {params}")

    if self._write_stream is None:
        print("[WARNING] write_stream é None!")
        return

    notification = JSONRPCNotification(
        jsonrpc="2.0",
        method=method,
        params=params,
    )

    try:
        message = JSONRPCMessage(notification)
        print(f"[DEBUG] Enviando mensagem pelo stream...")
        await self._write_stream.send(message)
        print(f"[DEBUG] Mensagem enviada!")
    except Exception as e:
        print(f"[ERROR] Erro ao enviar: {e}")
        import traceback
        traceback.print_exc()
```

---

## 5. Claude Code MCP Dialog

**Ver status de conexão:**

```
/mcp
```

**Reconectar:**
```
/mcp
Reconnected to discord.
```

**Ver servidor configurado:**
```bash
cat .mcp.json
```

---

## 6. Testar Tools MCP Individualmente

**Via Claude Code:**
```
Use o reply tool para enviar "teste de debug"
Use fetch_messages para ver histórico
Use send_buttons para criar botões de teste
```

**Ver resposta no Discord:**
- Mensagem chega?
- Botões aparecem?
- Clique funciona?

---

## 7. Verificar Processo

```bash
# Ver se está rodando
ps aux | grep discord

# Ver PID salvo
cat discord_mcp.pid

# Mat processo se necessário
kill $(cat discord_mcp.pid)
```

---

## 8. Debug de Notification

**Problema:** Notificação enviada mas Claude Code não recebe.

**Verificar:**

1. **write_stream é None?**
```python
if self._write_stream is None:
    logger.warning("write_stream não disponível")
    return  # ❌ Notificação perdida
```

2. **Capability declarada?**
```python
# server.py:505-507
experimental_capabilities = {
    "claude/channel": {},  # ← Deve existir!
}
```

3. **Method correto?**
```python
# ✅ Correto
await server.send_notification("notifications/claude/channel", notification)

# ❌ Errado (ninguém escuta)
await server.send_notification("notifications/claude/xyz", notification)
```

---

## 9. Fluxo Completo de Debug

```
Usuário clica botão
    ↓
[DISCORD] Evento chega?
    ↓ (tail -f discord_interaction_debug.log)
[HANDLER] on_interaction_create chamado?
    ↓ (print no console)
[ADAPTER] MCPButtonAdapter processou?
    ↓ (print "[DEBUG] Adapter result")
[NOTIFICATION] send_notification chamado?
    ↓ (print "[DEBUG] Notificação MCP enviada")
[STREAM] Mensagem enviada via write_stream?
    ↓
[CLAUDE] <channel> tag aparece?
```

---

## 10. Comandos Úteis

```bash
# Monitorar tudo
tail -f discord_interaction_debug.log &

# Iniciar com logs visíveis
python run_discord_mcp.py 2>&1 | tee mcp_debug.log

# Ver última notificação
grep "Notificação MCP enviada" mcp_debug.log | tail -1

# Ver erros
grep "ERROR" mcp_debug.log

# Limpar logs
rm discord_interaction_debug.log mcp_debug.log
```

---

## 11. Debug Botões vs Mensagens

| Tipo | Handler | Notificação |
|------|---------|-------------|
| Texto | `on_message` | `notifications/claude/channel` |
| Botão | `on_interaction_create` | `notifications/claude/channel` |

**Verificar se handler foi chamado:**
```bash
grep "HANDLER CHAMADO" discord_interaction_debug.log
```

---

## 12. Exemplo Prático de Debug

**Problema:** Botão não funciona.

```bash
# 1. Ver se handler foi chamado
tail -f discord_interaction_debug.log
# Output esperado: [2026-03-30...] HANDLER CHAMADO! Type: 3

# 2. Ver console para prints
# [DEBUG on_interaction_create] Interaction type: 3
# [DEBUG] Não é componente, retornando  ← ❌ Problema!

# 3. InteractionType.component = 3
# Se o tipo não for 3, retorna sem processar

# 4. Solução: Verificar se interaction.type está correto
```

---

## Checklist de Debug

- [ ] Servidor MCP está rodando?
- [ ] `write_stream` não é None?
- [ ] Capability `claude/channel` declarada?
- [ ] Handler foi chamado? (log file)
- [ ] Debug prints aparecem no console?
- [ ] Notificação tem formato correto?
- [ ] Claude Code reconectou ao MCP?

---

> "Debug é arte de eliminar o impossível até sobrar o óbvio" – made by Sky 🔍✨
