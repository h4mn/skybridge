# Edge Cases Documentados - Chat + TTS (Implementação Atual)

**Data:** 2026-03-17
**Contexto:** Fase 0 - Testes FIRST (Pré-Refatoração)
**Objetivo:** Documentar edge cases que funcionam hoje para garantir regressão zero

---

## 1. Transições de Evento TTS

### Caso: TOOL_RESULT → THOUGHT (Novo ciclo de pensamento)

**Comportamento atual:**
- Buffer acumulado é falado antes do novo ciclo
- Reação de início ("hum...") é adicionada
- Transição é detectada em `MainScreen._tts_worker()` linha 677

**Teste:** Cenário 3 do test_chat_tts_e2e.py

**Código de referência:** `main.py:677-685`
```python
if last_event_type == "TOOL_RESULT" and event_type == "THOUGHT":
    if buffer.strip():
        await _speak_and_wait(buffer)
        buffer = ""
    reaction = get_reaction("post_tool", "positive", 0.5)
    if reaction:
        buffer = f"{reaction} "
```

### Caso: TOOL_RESULT → TEXT (Texto final)

**Comportamento atual:**
- Buffer do último pensamento é falado
- Buffer é limpo para começar texto final
- Transição detectada em `main.py:689-692`

**Teste:** Cenário 3 do test_chat_tts_e2e.py

**Código de referência:** `main.py:689-692`

### Caso: TOOL_START / TOOL_RESULT / ERROR (Interrupções)

**Comportamento atual:**
- Buffer acumulado é falado imediatamente
- Buffer é limpo após fala
- Eventos não são enfileirados para TTS, apenas disparam fala do buffer

**Teste:** Cenário 3 do test_chat_tts_e2e.py

**Código de referência:** `main.py:706-710`

---

## 2. Buffer de Fala

### Caso: Acumulação até pontuação final

**Comportamento atual:**
- Buffer acumula texto até 50+ caracteres
- Somente fala quando termina em pontuação (.!?)
- Verificação em `main.py:717-719`

**Teste:** Cenário 4 do test_chat_tts_e2e.py

**Código de referência:** `main.py:717-719`
```python
stripped = buffer.rstrip()
if len(stripped) >= 50 and stripped[-1] in ".!?":
    await _speak_and_wait(buffer)
    buffer = ""
```

### Caso: EOF com buffer restante

**Comportamento atual:**
- Quando EOF (None) é recebido, buffer restante é falado
- Worker termina após falar buffer
- Implementado em `main.py:662-669`

**Teste:** Cenário 2 do test_chat_tts_e2e.py

**Código de referência:** `main.py:662-669`
```python
if event is None:
    log.evento("TTS EOF", "Recebido sinal de fim")
    if buffer.strip():
        log.evento("TTS FINAL", f"Falando buffer restante: {len(buffer)} chars")
        await _speak_and_wait(buffer)
    log.evento("TTS EOF", "Worker terminando")
    break
```

### Caso: THOUGHT com buffer vazio

**Comportamento atual:**
- Se buffer está vazio, adiciona reação de início ("hum...")
- Se buffer tem conteúdo, apenas concatena
- Implementado em `main.py:700-704`

**Teste:** Cenário 3 do test_chat_tts_e2e.py

---

## 3. Lifecycle do Worker TTS

### Caso: Inicialização lazy

**Comportamento atual:**
- Worker é criado com `asyncio.create_task()` no início de `_processar_mensagem()`
- Fila `self._tts_queue` é criada se não existir
- Worker roda em background, não bloqueia stream

**Código de referência:** `main.py:592-601`
```python
if not self._tts_queue:
    self._tts_queue = asyncio.Queue()
if not self._tts_task or self._tts_task.done():
    self._tts_task = asyncio.create_task(self._tts_worker())
```

### Caso: Shutdown no EOF

**Comportamento atual:**
- `None` é enviado para fila ao final do stream
- Worker recebe `None`, fala buffer restante e termina
- **IMPORTANTE:** Worker NÃO é aguardado no finally (causa bug)

**Código de referência:** `main.py:462-467`
```python
if self._tts_queue:
    await self._tts_queue.put(None)  # Sinal de fim
    # FIX: NÃO aguarda worker terminar aqui
    # O await causa race condition com o cleanup do generator SDK
```

### Caso: Cleanup no on_unmount

**Comportamento atual:**
- Worker é cancelado se ainda estiver rodando
- Cleanup é feito em `MainScreen.on_unmount()`
- Garante que worker não vira "zombie task"

**Código de referência:** `main.py:540-544`
```python
if self._tts_task and not self._tts_task.done():
    try:
        self._tts_task.cancel()
    except Exception:
        pass
```

---

## 4. Waveform (UI)

### Caso: start_waveform durante fala

**Comportamento atual:**
- Waveform é iniciado antes de chamar `tts.speak()`
- Widget SkyBubble é atualizado com estado "speaking"
- Implementado em `_speak_and_wait()` dentro do worker

**Código de referência:** `main.py:652`
```python
self._start_waveform(turno, "speaking")
```

### Caso: stop_waveform após fala

**Comportamento atual:**
- Waveform é parado no finally block após fala
- Garante que waveform para mesmo se fala falhar
- Implementado em `_speak_and_wait()` dentro do worker

**Código de referência:** `main.py:653-656`
```python
try:
    await tts.speak(clean_text, mode=VoiceMode.NORMAL)
finally:
    self._stop_waveform(turno)
```

---

## 5. Bug Conhecido: Cancel Scope Error

### Caso: Stream SDK termina com TTS worker ativo

**Comportamento atual (BUG):**
- Quando `async for stream_response()` termina, generator SDK é fechado
- Finally block do SDK chama `query.close()` em task diferente
- TTS worker ainda está rodando, tentando falar buffer
- Resultado: `RuntimeError: Attempted to exit cancel scope in a different task`

**Stack trace:**
```
File "claude_agent_sdk/_internal/client.py", line 124, in process_query
    await query.close()
File "claude_agent_sdk/_internal/query.py", line 609, in close
    await self._tg.__aexit__(None, None, None)
File "anyio/_backends/_asyncio.py", line 794, in __aexit__
RuntimeError: Attempted to exit cancel scope in a different task
```

**Workaround atual:**
- NÃO aguardar `self._tts_task` no finally block (linha 464 comentada)
- Worker termina em background, limpo no `on_unmount()`

**Solução na refatoração:**
- TTSService com lifecycle próprio isolado
- Comunicação via EventBus (non-blocking)
- Worker não compartilha task scope com stream SDK

---

## 6. Performance Baseline

### Métricas capturadas (com TTS mock)

| Cenário | Duração esperada | Observação |
|---------|------------------|------------|
| Resposta simples (sem TTS) | < 200ms | Apenas chat SDK |
| Worker TTS (mock, 50ms) | < 100ms | Simulação de síntese |
| Chat + TTS real | +200-500ms | Depende da síntese Kokoro |

### Sobrecarga documentada

- Worker startup: ~10ms
- Enfileiramento de evento: < 1ms (asyncio.Queue)
- Buffer management: < 1ms

**NOTA:** Valores com TTS real (Kokoro) serão significativamente maiores devido a:
- Síntese de áudio: 50-200ms por frase
- Reprodução com sounddevice: tempo da frase

---

## 7. Integração com AgenticLoop (PRD-REACT-001)

### Caso: Tool use com TTS

**Comportamento atual:**
- Eventos TOOL_START e TOOL_RESULT são enfileirados para TTS
- Buffer é falado antes de cada tool start/result
- Reações visuais/sonoras indicam progresso

**Fluxo:**
1. THOUGHT → buffer acumula
2. TOOL_START → buffer é falado, waveform para
3. TOOL_RESULT → reação sonora ("hum...")
4. Próximo THOUGHT → novo ciclo começa

**Teste:** Cenário 3 do test_chat_tts_e2e.py

---

## Checklist de Regressão

Após implementação da arquitetura event-driven, validar:

- [ ] Buffer acumula corretamente (50+ chars + pontuação)
- [ ] Transições TOOL_RESULT→THOUGHT e TOOL_RESULT→TEXT funcionam
- [ ] Buffer restante é falado no EOF
- [ ] Waveform inicia/para corretamente
- [ ] Worker termina graciosamente
- [ ] **CANCEL SCOPE ERROR NÃO ACONTECE MAIS** 🎯
- [ ] Performance dentro de 5% do baseline

---

> "Testes são a especificação que não mente" – made by Sky 🚀
