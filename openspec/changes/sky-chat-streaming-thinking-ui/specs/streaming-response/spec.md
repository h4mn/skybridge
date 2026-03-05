# Spec: Streaming Response (Delta)

## ADDED Requirements

### Requirement: Streaming de texto em tempo real

O sistema SHALL implementar streaming de resposta da Sky usando Claude Agent SDK com `include_partial_messages=True`, permitindo que o texto apareça incrementalmente na interface.

#### Scenario: Primeiro conteúdo aparece em menos de 500ms
- **QUANDO** usuário envia uma mensagem
- **ENTÃO** primeiro chunk de texto da resposta aparece em menos de 500ms na UI
- **E** texto é atualizado incrementalmente conforme chunks chegam

#### Scenario: Texto é atualizado no SkyBubble
- **QUANDO** chunk de texto chega do stream
- **ENTÃO** conteúdo do SkyBubble é atualizado com o texto acumulado
- **E** SkyBubble é repintado para mostrar o novo conteúdo

#### Scenario: Streaming continua até resposta completa
- **QUANDO** stream de resposta está em andamento
- **ENTÃO** sistema continua processando chunks até mensagem completa
- **E** sky_bubble final contém o texto completo da resposta

---

### Requirement: Worker suporta streaming via async generator

O sistema SHALL fornecer método `ClaudeWorker.stream_response()` que retorna async generator de chunks de texto.

#### Scenario: stream_response retorna async generator
- **QUANDO** `ClaudeWorker.stream_response(message)` é chamado
- **ENTÃO** retorna async generator que yield chunks de texto
- **E** cada chunk contém parte incremental da resposta

#### Scenario: Generator pode ser cancelado
- **QUANDO** usuário interrompe a resposta (Ctrl+C ou botão Stop)
- **ENTÃO** generator é cancelado e recursos são liberados
- **E** nenhum erro é lançado na UI

---

### Requirement: Turn suporta atualização incremental

O sistema SHALL fornecer método `Turn.append_response(text)` para adicionar conteúdo incrementalmente ao SkyBubble.

#### Scenario: append_response atualiza SkyBubble
- **QUANDO** `Turn.append_response(chunk)` é chamado durante streaming
- **ENTÃO** chunk é adicionado ao conteúdo existente do SkyBubble
- **E** SkyBubble é atualizado visualmente

#### Scenario: SkyBubble final é criado ao completar streaming
- **QUANDO** streaming de resposta é completado
- **ENTÃO** Turn contém SkyBubble com o texto completo
- **E** ThinkingIndicator é removido do Turn

---

### Requirement: ChatScreen usa loop de streaming

O sistema SHALL modificar `ChatScreen` para usar loop de streaming ao invés de `await respond()` completo.

#### Scenario: Loop processa chunks conforme chegam
- **QUANDO** resposta da Sky começa a ser gerada
- **ENTÃO** ChatScreen entra em loop processando chunks
- **E** cada chunk é passado para `Turn.append_response()`

#### Scenario: Loop termina quando stream completa
- **QUANDO** generator de streaming é esgotado
- **ENTÃO** loop de streaming termina
- **E** métricas (tokens, latência) são coletadas e exibidas

---

### Requirement: Compatibilidade com modo legado

O sistema SHALL manter compatibilidade com UI legada (`legacy_ui.py`) que usa resposta completa.

#### Scenario: Modo legado continua funcionando
- **QUANDO** `USE_TEXTUAL_UI=false` ou não definido
- **ENTÃO** sistema usa `legacy_ui.py` com resposta completa
- **E** nenhuma mudança de comportamento ocorre

#### Scenario: Feature flag controla streaming
- **QUANDO** `USE_TEXTUAL_UI=true`
- **ENTÃO** nova UI com streaming é ativada
- **E** resposta é exibida em tempo real

---

> "A rapidez da resposta é tão importante quanto a própria resposta" – made by Sky 🚀
