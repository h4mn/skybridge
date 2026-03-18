## Context

**Estado Atual:**
O `ClaudeChatAdapter` cria uma nova instância do `ClaudeSDKClient` a cada chamada de `respond()`, usando `async with` que cria e destrói o cliente imediatamente. A configuração atual usa `max_turns=1` e `allowed_tools=[]`.

**Arquitetura Atual:**
```
ChatScreen → ClaudeChatAdapter.respond() → _call_claude_sdk()
                                              ↓
                                        async with ClaudeSDKClient (NOVA instância)
```

**Restrições:**
- API `respond()` deve manter compatibilidade retrocompatível
- Uso do Textual `@work(exclusive=True)` exige operações assíncronas
- Cliente SDK já usa `claude_agent_sdk` como dependência

**Stakeholders:**
- Usuários do Sky Chat (TUI e CLI)
- Desenvolvedores que mantêm `ClaudeChatAdapter`

## Goals / Non-Goals

**Goals:**
- Manter única instância do `ClaudeSDKClient` durante sessão de chat
- Habilitar ferramentas `Read`, `Glob`, `Grep` para descoberta de projeto
- Permitir multi-turno removendo limite de `max_turns=1`
- Fornecer cleanup adequado via método `close()`

**Non-Goals:**
- Modificar UI Textual (ChatScreen permanece igual)
- Adicionar ferramentas de escrita (`Write`, `Edit`) - escopo futuro
- Persistência de sessão entre reinícios da aplicação
- Modificar sistema de memória RAG existente

## Decisions

### 1. Cliente SDK Lazy com Async Context Manager

**Decisão:** Manter `ClaudeSDKClient` como atributo de instância, inicializado lazy na primeira chamada de `respond()`.

**Racional:**
- **Async context manager:** SDK usa `async with` que exige `__aenter__`/`__aexit__`
- **Lazy initialization:** Evita criar SDK se nunca houver mensagens
- **Reutilização:** Cliente persiste entre chamadas de `respond()`

**Alternativas Consideradas:**
| Alternativa | Vantagens | Desvantagens | Decisão |
|-------------|-----------|--------------|----------|
| Singleton global | Fácil acesso | Estado compartilhado entre sessões | ❌ |
| Criar no `__init__` | Simples | Custo mesmo sem uso | ❌ |
| Lazy em `respond()` | Eficiente | Requer checagem de null | ✅ |

**Implementação:**
```python
class ClaudeChatAdapter:
    def __init__(self, ...):
        self._sdk_client: ClaudeSDKClient | None = None

    async def _ensure_client(self):
        if self._sdk_client is None:
            options = ClaudeAgentOptions(...)
            self._sdk_client = ClaudeSDKClient(options=options)
            await self._sdk_client.__aenter__()
```

### 2. Ferramentas de Leitura Apenas

**Decisão:** Habilitar `["Read", "Glob", "Grep"]` e excluir `Write`, `Edit`, `Bash`.

**Racional:**
- Chat é **read-only** - Sky descobre, não modifica código
- `Bash` é perigoso em contexto de chat sem aprovação explícita
- Ferramentas de leitura são suficientes para responder perguntas sobre o projeto

**Alternativas Consideradas:**
| Alternativa | Risco | Decisão |
|-------------|-------|----------|
| Todas as ferramentas | Sky pode modificar acidentalmente | ❌ |
| Read-only + Bash com approval | Complexo de implementar | ❌ |
| Read-only apenas | Seguro e suficiente | ✅ |

### 3. max_turns=None vs Valor Alto

**Decisão:** Usar `max_turns=None` (sem limite) em vez de um valor numérico alto.

**Racional:**
- SDK gerencia conclusão automaticamente
- Limite arbitrário pode interromper respostas complexas
- Textual `@work(exclusive=True)` já previne concorrência

**Alternativas Consideradas:**
| Alternativa | Problema | Decisão |
|-------------|----------|----------|
| `max_turns=50` | Arbitrário, pode truncar | ❌ |
| `max_turns=None` | Confia no SDK | ✅ |

### 4. Ciclo de Vida com close()

**Decisão:** Adicionar método `close()` que chama `__aexit__` do cliente SDK.

**Racional:**
- Limpa recursos adequadamente
- Permite reentrada (nova mensagem após close cria novo cliente)
- Seguro para chamadas múltiplas (idempotente)

**Implementação:**
```python
async def close(self):
    if self._sdk_client is not None:
        await self._sdk_client.__aexit__(None, None, None)
        self._sdk_client = None
```

## Risks / Trade-offs

### Risco 1: Cliente SDK Nunca Fechado
**Risco:** Se usuário fecha app sem chamar `close()`, recursos podem vazar.

**Mitigação:**
- Python GC libera recursos ao encerrar processo
- Futuro: usar `asyncio.atexit` ou contexto da app Textual

### Risco 2: Exceção Durante __aenter__
**Risco:** Se `__aenter__` falhar, `_sdk_client` pode ficar em estado inconsistente.

**Mitigação:**
```python
try:
    await self._sdk_client.__aenter__()
except Exception:
    self._sdk_client = None  # Reset para tentar novamente
    raise
```

### Trade-off: Memória vs Latência
**Decisão:** Manter cliente na memória vs criar/destruir a cada mensagem.

**Justificativa:**
- Custo de criação do SDK >> custo de memória
- Sessões de chat são tipicamente curtas (minutos)
- SDK já mantém cache interno que se perde ao destruir

## Migration Plan

### Fase 1: Modificar ClaudeChatAdapter
1. Adicionar `_sdk_client: None` em `__init__`
2. Criar `_ensure_client()` com lazy initialization
3. Modificar `_call_claude_sdk()` para usar cliente persistente
4. Adicionar método `close()`

### Fase 2: Integração ChatScreen
1. Chamar `close()` ao encerrar screen (opcional mas recomendado)
2. Testar multi-turno com perguntas que usam ferramentas

### Fase 3: Testes
1. Teste unitário: primeira mensagem cria cliente
2. Teste unitário: mensagens subsequentes reutilizam
3. Teste unitário: close() libera recursos
4. Teste de integração: Sky usa Read para descobrir nome do projeto

### Rollback
- Reverter `ClaudeChatAdapter` para implementação anterior
- Remover `close()` se adicionado em ChatScreen

## Open Questions

1. **ChatScreen deve chamar close() explicitamente?**
   - **Status:** Aberto
   - **Opções:** (a) Sim no `on_unmount()`, (b) Não, confiar no GC
   - **Decisão Pendente:** Testar primeiro sem close explícito

2. **Devemos adicionar timeout para operações de ferramenta?**
   - **Status:** Fora de escopo inicial
   - **Futuro:** Se Sky travar esperando Read/Grep

3. **Como lidar com erros de ferramenta (arquivo não encontrado)?**
   - **Status:** SDK já trata erros internamente
   - **Decisão:** Deixar SDK tratar, sem código adicional
