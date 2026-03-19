# ADR-026: Problema "Cancel Scope in Different Task"

**Data:** 2026-03-18
**Status:** 🔴 Crítico - Bloqueia TTS na arquitetura event-driven
**Contexto:** Refatoração chat event-driven (refactor-chat-event-driven)

---

## O Problema em Detalhes

### Mensagem de Erro
```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

### Onde Acontece
```python
File "B:\Programas\Python\Python311\Lib\site-packages\claude_agent_sdk\_internal\client.py", line 121, in process_query
    yield parse_message(data)  # ← Generator que precisa de cleanup
GeneratorExit

File "B:\Programas\Python\Python311\Lib\site-packages\claude_agent_sdk\_internal\client.py", line 124, in process_query
    await query.close()  # ← Tenta sair do cancel scope
File "B:\Programas\Python311\Lib\site-packages\anyio\_backends\_asyncio.py", line 461, in __aexit__
    raise RuntimeError("Attempted to exit cancel scope in a different task...")
```

---

## Anatomia do Problema

### 1. anyio Task Groups (O que é um Cancel Scope?)

```python
import anyio

async def exemplo():
    # anyio cria um "cancel scope" que precisa ser limpo na MESMA task
    async with anyio.create_task_group() as tg:
        # Código aqui pode criar subtasks
        async def subtask():
            pass
        tg.start_soon(subtask)

    # ← Quando este bloco termina, anyio faz cleanup das subtasks
```

**Cancel Scope:** Um contexto que rastreia tasks criadas dentro dele. Quando o contexto sai, **todas as tasks precisam ser canceladas ou completadas** antes de sair do escopo.

### 2. Claude Agent SDK Internals

```python
# client.py (SDK)
async def process_query(...):
    # SDK cria um task group internamente
    async with anyio.create_task_group() as tg:
        # Faz requisições HTTP, processa resposta
        async for chunk in parse_message(data):
            yield chunk  # ← Generator!
    # ← Quando generator fecha, SDK tenta limpar task group
```

### 3. Textual @work Decorator

```python
from textual import work

@work(exclusive=True)
async def _processar_mensagem(self, mensagem: str):
    # @work cria uma TASK SEPARADA em background
    async for chunk in self._chat.stream_response(mensagem):
        print(chunk)
```

**O que @work faz:**
1. Cria uma `asyncio.Task` em background
2. Executa o método nessa task
3. Retorna imediatamente (non-blocking)

---

## O Conflito: Task Mismatch

```
┌─────────────────────────────────────────────────────────────────────┐
│ TASK 1 (Main)                    │  TASK 2 (Worker @work)              │
├───────────────────────────────────┼──────────────────────────────────┤
│ app.run()                          │ _processar_mensagem()             │
│   ↓                                │   ↓                                 │
│ MainScreen mounted                  │   ↓                                 │
│   ↓                                │   async for chunk in                 │
│ _processar_mensagem() ← CHAMA     │       chat.stream_response()        │
│   ↓                                │       ↓                                 │
│ @work creates TASK 2 ──────────────┼──┐   ↓                                 │
│   ↓                                │   │   SDK cria task_group:           │
│   ↓                                │   │   │   ↓                                 │
│ continua (non-blocking)            │   │   │   yield chunk                     │
│                                   │   │   │   ↓                                 │
│                                   │   │   │   generator fecha                 │
│                                   │   │   │   ↓                                 │
│                                   │   │   │   await query.close()             │
│                                   │   │   │   ↓                                 │
│                                   │   │   └── anyio tenta sair de           │
│                                   │   │       task_group ← ERRO!          │
│                                   │   │         (task group criado        │
│                                   │   │          na TASK 1, não TASK 2!)   │
│                                   │   │                                     │
└───────────────────────────────────┴───────────────────────────────────┘
```

**Por que o erro acontece:**

1. **TASK 1 (Main):** `stream_response()` cria um `anyio task_group`
2. **TASK 2 (Worker):** @work cria task separada para processar
3. **Conflito:** O generator SDK é consumido na TASK 2, mas o `task_group` foi criado na TASK 1
4. **Erro:** Quando o generator fecha, SDK tenta fazer `__aexit__` do `task_group`
5. **Verificação:** anyio verifica: "Esta task (TASK 2) é a mesma que criou o cancel scope? **NÃO!** → RuntimeError

---

## Por que Tudo Funciona sem @work?

**Código Síncrono (funciona):**
```python
async def _processar_mensagem(self, mensagem: str):
    # Processa na MESMA task do Main
    async for chunk in self._chat.stream_response(mensagem):
        # stream_response() cria task_group nesta task
        # generator fecha nesta task
        # cleanup acontece nesta task ✓
        print(chunk)
```

**Por que funciona:**
- `stream_response()` é chamado na task principal
- `task_group` é criado na task principal
- Generator fecha na task principal
- Cleanup `task_group.__aexit__()` acontece na mesma task ✓

**Com @work (não funciona):**
```python
@work(exclusive=True)
async def _processar_mensagem(self, mensagem: str):
    # @work cria TASK SEPARADA
    async for chunk in self.chat.stream_response(mensagem):
        # stream_response() cria task_group na TASK 1 (Main)
        # mas processamento está na TASK 2 (Worker)
        # generator fecha na TASK 2
        # cleanup tenta acontecer na TASK 2
        # mas task_group foi criado na TASK 1 ✗
        print(chunk)
```

---

## Soluções Exploradas

### Solução 1: Consumir Stream Primeiro (Tentada - Falhou)
```python
async def process_turn(self, user_message, turn_id):
    # Coletar todos chunks PRIMEIRO
    all_chunks = []
    async for chunk in chat.stream_response(user_message):
        all_chunks.append(chunk)
    # Stream fecha aqui, cleanup na mesma task ✓

    # Depois processar
    for chunk in all_chunks:
        yield chunk
```

**Por que falhou:** A coleta aconteceu na TASK do Worker, não na task Main. O `task_group` foi criado na task Main ainda.

### Solução 2: Remover @work (SOTA - Implementando)
```python
async def _processar_mensagem(self, mensagem: str):
    # Processa DIRETO na task principal (sem @work)
    async for chunk in self.chat.stream_response(mensagem):
        print(chunk)
```

**Vantagens:**
- ✅ Elimina race condition completamente
- ✅ Cleanup acontece na mesma task
- ✅ Simples e direto

**Desvantagens:**
- ❌ Bloqueia processamento (uma mensagem por vez)
- ❌ UI não responsiva durante processamento
- ❌ Não segue boas práticas de async design

### Solução 3: Threading (Não implementada)
Processar em thread separada mas usando `call_from_thread` para atualizar UI.

**Problemas:**
- Complexidade aumenta drasticamente
- GIL Python pode ser gargalo
- Debugging muito mais difícil

---

## Conclusão

**Raiz do problema:** anyio task groups **devem ser limpos na mesma task** onde foram criados. O `@work` decorator do Textual cria tasks separadas, quebrando essa invariant.

**Solução SOTA escolhida:** Remover `@work` e processar sincronamente na task principal.

**Pragmatismo > Perfeição:** Às vezes, a solução "feia" que funciona é melhor que a arquitetura "perfeita" que não funciona.

---

> "A engenharia é a arte de fazer o que funciona, não o que seria elegante em tese" – made by Sky 🔧
