## Context

**Estado atual**: O chat tem código misturado em `MainScreen` (~500 linhas), gerenciando UI, business logic (chat, TTS, voice), workers, e estado mutável compartilhado (`_tts_queue`, `_tts_task`, `_turno_atual`). Isso causa race conditions quando o stream SDK termina simultaneamente com o TTS worker ainda rodando.

**Restrições**:
- Claude Agent SDK usa anyio internamente - cancel scopes devem ser limpos na mesma task
- Textual TUI usa workers assíncronos que podem ser cancelados a qualquer momento
- TTS (Kokoro) usa sounddevice que não é thread-safe
- Manter compatibilidade com interface pública `stream_response()`

**Stakeholders**: Desenvolvedores mantendo código, usuários finais usando chat com TTS

## Goals / Non-Goals

**Goals:**
- Eliminar race conditions entre stream SDK e TTS worker
- Separar responsabilidades (UI vs business logic vs serviços)
- Permitir testabilidade de componentes isolados
- Facilitar adição de novos consumidores de eventos (log, métricas)

**Non-Goals:**
- Modificar interface pública de `ClaudeChatAdapter.stream_response()`
- Alterar comportamento TTS (mesma lógica de buffer/fala)
- Mudar experiência do usuário final

## Decisions

### 1. Event-Driven Architecture com EventBus

**Decisão**: Usar pub/sub assíncrono para comunicação entre componentes.

**Racional**: Desacopla completamente - chat não conhece TTS, apenas publica eventos. Alternativas consideradas:
- *Chamadas diretas*: Mantém acoplamento ❌
- *Callbacks*: Difícil de gerenciar múltiplos consumidores ❌
- *EventBus*: Loose coupling, extensível ✅

### 2. TTSService com Lifecycle Próprio

**Decisão**: `TTSService` gerencia próprio worker e fila, com métodos `start()/stop()`.

**Racional**: Isolamento completo - serviço pode ser testado sem UI. Alternativas:
- *Worker em MainScreen*: Mantém acoplamento ❌
- *Singleton global*: Difícil de testar ❌
- *Serviço com lifecycle*: Testável, controlável ✅

### 3. ChatOrchestrator como Coordenador

**Decisão**: `ChatOrchestrator.process_turn()` coordena chat + TTS, sem conhecer UI.

**Racional**: Orquestração isolada - fácil testar fluxo completo. Alternativas:
- *Coordenação em MainScreen*: Dificulta teste ❌
- *Coordenação em TTSService*: TTS não deveria conhecer chat ❌
- *Orquestrador dedicado*: Separação clara ✅

### 4. ChatContainer com DI

**Decisão**: `ChatContainer` cria todas dependências e gerencia lifecycle com `async with`.

**Racional**: Resource safety garantido - cleanup automático. Alternativas:
- *Manual start/stop*: Propenso a esquecer cleanup ❌
- *Context manager*: RAII-style, garantido ✅

### 5. In-Memory EventBus vs External

**Decisão**: `InMemoryEventBus` usando `asyncio.Queue`.

**Racional**: Zero dependências externas, suficiente para single-process. Alternativas:
- *Redis/RabbitMQ*: Overkill para single-process ❌
- *asyncio.Queue*: Simples, suficiente ✅

## Risks / Trade-offs

**[Risk] CancelledError ainda pode ocorrer** →
- **Mitigação**: Cada serviço captura CancelledError E faz cleanup específico (sd.stop(), queue.close())
- **Fallback**: Se CancelledError ocorrer fora do escopo conhecido, loga FULL traceback para análise

**[Risk] Complexidade inicial maior** →
- **Benefício**: Separação clara de responsabilidades: UI (MainScreen) vs Lógica (Orchestrator) vs Serviços (TTS)
- **Mitigação**: 45 tarefas pequenas com progresso rastreável
- **Evidência**: 3 dias de debugging de código "simples" > 1 dia de implementação arquitetural

**[Trade-off] Mais arquivos/componentes** →
- **Benefício**: Cada componente com responsabilidade única (SRP), testável isoladamente
- **Mitigação**: Documentação clara de dependências e lifecycle

**[Risk] Degradação de performance (events)** →
- **Mitigação**: EventBus com limite de 100 eventos + benchmark para medir overhead (<1ms esperado)
- **Fallback**: Se overhead for significativo, permitir modo "direct mode" (bypass EventBus)

**[Risk] Eventos perdidos se fila encher** →
- **Mitigação**: Buffer máximo de 100 eventos com monitoramento. Log warning quando approaching limit.
- **Ação**: Se atingir limite, descarta eventos mais antigos (FIFO) e continua operando

**[Risk] TTS worker pode ficar preso** →
- **Mitigação**: Timeout de 30s para síntese, 60s para falar. Se exceder, cancela operação e reinicia worker.

**[Risk] Migration pode introduzir regressões** →
- **Mitigação**: Fase 0: Testes FIRST antes de qualquer mudança. Branch separado com rollback rápido se necessário.

## Migration Plan

**Estratégia**: Feature branch com rollback rápido + Testes FIRST

0. **Fase 0** (Testes FIRST): Antes de qualquer mudança, escrever testes do comportamento atual
   - Testar fluxo completo de chat + TTS
   - Capturar baseline de performance
   - Documentar edge cases que funcionam hoje

1. **Fase 1** (Infraestrutura): Criar `EventBus`, eventos de domínio
   - Implementar sem modificar código existente
   - Testes unitários de cada componente

2. **Fase 2** (Serviços): Criar `TTSService`, `ChatOrchestrator`, `ChatContainer`
   - Implementar isoladamente, fora do código principal
   - Testes de integração de cada serviço

3. **Fase 3** (Migração Paralela): Novo e velho código coexistem
   - Criar flag/feature toggle para alternar entre old/new
   - `MainScreen` usa novos componentes SE flag ativado
   - Código legado mantido como fallback

4. **Fase 4** (Limpeza): Remover código legado após validação
   - Waveform para componente dedicado
   - Remover TTS worker de MainScreen
   - Apenas após Fase 3 estar estável em produção

5. **Fase 5** (Validação): Testes E2E, performance, estresse
   - Testes manuais completos
   - Monitoramento de performance
   - Teste de carga com múltiplos turnos simultâneos

**Rollback**: Branch `refactor-chat-event-driven` com merge rápido para `dev`. Se crítico, revert merge em < 1 hora. Código legado nunca é deletado, apenas desativado.

## Justification (Contra-argumentos às Críticas)

### "Por que não solução simples de 10 linhas?"

**Fato**: Após 3 dias de debugging, solução simples não foi encontrada.

**Evidência**: O erro `RuntimeError: Attempted to exit cancel scope in a different task` é estrutural - acontece quando anyio task groups são limpos em task diferente da criação. Isso não é corrigível com pequenos tweaks; requer reorganização de tasks.

**Custo-benefício**:
- 3 dias desperdados tentando hotfix
- 8-12 horas para arquitetura robusta = ROI positivo

### "EventBus é overengineering para 1 consumidor"

**Contra-argumento**:
- Você tem 1 consumidor HOJE, mas waveform UI, logging, métricas são próximos
- EventBus: adicionar consumidor = 3 linhas (`await events.subscribe(X)`)
- Sem EventBus: cada consumidor = mais código acoplado em MainScreen

**Histórico**: Todo sistema "provisório" que "só tem 1 caso de uso" acaba acumulando consumidores. EventBus é anti-fragilidade.

### "TTSService é worker com roupinha"

**Benefício real não é o "service", é o **isolamento**:
- Hoje: TTS worker precisa conhecer MainScreen (para waveform, logs)
- Com TTSService: Testa TTS sem subir Textual UI inteira
- Benefício: Testes unitários rápidos sem dependência de UI

### "Container é overengineering em Python"

**Problema real**: Resource safety em async Python

```python
# Sem Container:
tts.start()
chat.start()
# ... se der exceção aqui?
tts.stop()  # Pode nunca ser chamado
chat.stop()

# Com Container:
async with ChatContainer.create() as c:
    # ... exceção aqui é OK
# cleanup garantido na ordem reversa
```

**AsyncContextManager** é pattern Python standard (contextlib) - não é overengineering.

### "Por que não DI manual no __init__?"

**DI manual funciona**, mas não lida com:
- Lifecycle complexo (start/stop em ordem específica)
- Cleanup condicional (se falhou, não precisa parar o que não iniciou)
- Reutilização entre múltiplos turnos (container persistente)

**Container** encapsula essa complexidade.

1. **Timeout para TTS worker?** → **DEFINIDO**: 30 segundos por operação de síntese, 60s para falar. Se exceder, descarta e loga warning.
2. **Buffer máximo de eventos?** → **DEFINIDO**: Max 100 eventos na fila do EventBus. Se encher, descarta eventos mais antigos e loga warning.
3. **Persistência de eventos?** → Fora do escopo inicial (futuro: debugging)
4. **Ordem de shutdown?** → **DEFINIDO**: TTS → Chat → EventBus (ordem reversa do start)
5. **Fallback se EventBus falhar?** → **DEFINIDO**: Log erro e usa chamada direta (degradação graciosa)
