# Tasks: Sky Chat Streaming & Thinking UI

> **NOTA DO USUÁRIO**: ThinkingPanel deve ser sempre expandido por padrão. O usuário pode colapsá-lo manualmente se quiser, mas o comportamento padrão é expandido.

## 1. Setup e Infraestrutura

### 1.1 Claude Agent SDK Setup
- [x] 1.1.1 Verificar que `claude-agent-sdk` está instalado em requirements.txt
- [x] 1.1.2 Criar estrutura de options para streaming com `include_partial_messages=True`
- [x] 1.1.3 Configurar `allowed_tools=["Read", "Grep", "Glob"]` nas opções

### 1.2 Estrutura de Componentes
- [x] 1.2.1 Criar diretório `widgets/` se não existir (já deve existir)
- [ ] 1.2.2 Criar stub dos novos widgets (pensar depois sobre implementação)

---

## 2. Streaming de Resposta (Fase 1)

### 2.1 ClaudeWorker Modificações
- [x] 2.1.1 Adicionar import de `query` e `ClaudeAgentOptions` do Agent SDK
- [x] 2.1.2 Criar método `async def stream_response(self, user_message: str) -> AsyncIterator[str]`
- [x] 2.1.3 Implementar `include_partial_messages=True` nas options
- [x] 2.1.4 Implementar parser de `StreamEvent` para extrair `text_delta`
- [x] 2.1.5 Retornar `text_delta` chunks via `yield`
- [x] 2.1.6 Adicionar tratamento de erro `asyncio.CancelledError` para cancelamento
- [x] 2.1.7 Manter método `generate_response()` existente para compatibilidade

### 2.2 Turn Modificações
- [x] 2.2.1 Adicionar atributo `_sky_bubble: SkyBubble | None = None` em `__init__`
- [x] 2.2.2 Adicionar atributo `_thinking_panel: ThinkingPanel | None = None` em `__init__`
- [x] 2.2.3 Criar método `async def append_response(self, text: str) -> None`
- [x] 2.2.4 Implementar criação preguiçosa de `SkyBubble` no primeiro `append_response()`
- [x] 2.2.5 Atualizar `content` do SkyBubble incrementalmente
- [x] 2.2.6 Chamar `bubble.refresh()` para repint imediato
- [x] 2.2.7 Adicionar método `async def add_thinking_entry(self, entry: ThinkingEntry) -> None`

### 2.3 ChatScreen Modificações
- [x] 2.3.1 Modificar `_process_message()` para usar streaming
- [x] 2.3.2 Criar `Turn` antes do loop de streaming
- [x] 2.3.3 Chamar `Turn.start_thinking()` no início
- [x] 2.3.4 Entrar em loop `async for chunk in claude_worker.stream_response()`
- [x] 2.3.5 Passar cada chunk para `Turn.append_response(chunk)`
- [ ] 2.3.6 Capturar eventos especiais (tool_start, tool_result) se presentes
- [x] 2.3.7 Ao completar, chamar `Turn.finalize_thinking()`
- [x] 2.3.8 Atualizar métricas no header após stream completar

### 2.4 Latência e Performance
- [ ] 2.4.1 Medir latência do primeiro chunk (deve ser < 500ms)
- [ ] 2.4.2 Testar com resposta longa (100+ tokens)
- [x] 2.4.3 Verificar que `SkyBubble` não trava durante streaming (watch_content otimizado)

---

## 3. Thinking UI (Fase 2)

### 3.1 ThinkingPanel Widget
- [ ] 3.1.1 Criar arquivo `widgets/thinking_panel.py`
- [ ] 3.1.2 Implementar classe `ThinkingPanel(Widget)`
- [ ] 3.1.3 Adicionar `DEFAULT_CSS` com estilos para expandido/colapsado
- [ ] 3.1.4 Implementar método `compose()` retornando `Header` e `Content`
- [ ] 3.1.5 Implementar atributo `_collapsed: bool = False` (começa expandido)
- [ ] 3.1.6 Implementar método `toggle()` para alternar estado
- [ ] 3.1.7 Implementar método `add_entry(entry: ThinkingEntry) -> None`
- [ ] 3.1.8 Implementar auto-scroll para última entrada sempre visível
- [ ] 3.1.9 Adicionar botões de ação (collapse/expand, close) no Header

### 3.2 ThinkingEntryWidget
- [ ] 3.2.1 Criar arquivo `widgets/thinking_entry.py`
- [ ] 3.2.2 Criar dataclass `ThinkingEntry` com campos: type, timestamp, content, metadata
- [ ] 3.2.3 Implementar classe `ThinkingEntryWidget(Static)`
- [ ] 3.2.4 Adicionar `DEFAULT_CSS` com estilos por tipo (--thought, --tool, --result, --error)
- [ ] 3.2.5 Implementar prefixos baseados no tipo (💭, 🔧, ✓, ❌)
-  [ ] 3.2.6 Suportar texto multiline (altura auto)
- [ ] 3.2.7 Adicionar timestamp se disponível

### 3.3 Turn Integração com ThinkingPanel
- [ ] 3.3.1 Modificar `Turn.compose()` para incluir `ThinkingPanel`
- [ ] 3.3.2 Criar `ThinkingPanel` no mount (não no compose inicial)
- [ ] 3.3.3 Implementar `start_thinking()` que cria/ativa ThinkingPanel
- [ ] 3.3.4 Implementar `add_thinking_entry()` delegando para `ThinkingPanel.add_entry()`
- [ ] 3.3.5 Implementar `finalize_thinking()` que **mantém expandido** (NOTA DO USUÁRIO)
- [ ] 3.3.6 Adicionar botão de close/remove se usuário quiser limpar

### 3.4 Indicador de Processamento
- [ ] 3.4.1 `ThinkingIndicator` existente continua como fallback rápido
- [ ] 3.4.2 ThinkingPanel substitui `ThinkingIndicator` quando primeira entrada chega
- [ ] 3.4.3 Transição suave entre `ThinkingIndicator` e `ThinkingPanel`

---

## 4. Tool Feedback Visual (Fase 3)

### 4.1 Captura de Eventos de Ferramenta
- [ ] 4.1.1 Modificar `ClaudeWorker.stream_response()` para detectar `content_block_start`
- [ ] 4.1.2 Extrair `tool_use` name e input do evento
- [ ] 4.1.3 Yield marcador especial `[TOOL:name]` ou criar `ThinkingEntry` específico
- [ ] 4.1.4 Detectar `content_block_stop` após `tool_use`
- [ ] 4.1.5 Capturar resultado da ferramenta (primeiros 100 chars)
- [ ] 4.1.6 Yield marcador `[TOOL_COMPLETE]` ou criar `ThinkingEntry` de resultado

### 4.2 Exibição de Ferramentas no ThinkingPanel
- [ ] 4.2.1 `add_thinking_entry()` recebe tipo "tool_start" para ferramentas
- [ ] 4.2.2 Criar `ThinkingEntryWidget` com estilo --tool (ícone 🔧)
- [ ] 4.2.3 Exibir nome da ferramenta e input resumido
- [ ] 4.2.4 `add_thinking_entry()` recebe tipo "tool_result" para resultados
- [ ] 4.2.5 Criar `ThinkingEntryWidget` com estilo --result (ícone ✓)
- [ ] 4.2.6 Truncar resultado se > 100 caracteres

### 4.3 Status Visual de Ferramentas
- [ ] 4.3.1 Ferramenta em execução mostra spinner ou animação
- [ ] 4.3.2 Status muda para "✓ completo" quando ferramenta termina
- [ ] 4.3.3 Status "❌ erro" se ferramenta falhar
- [ ] 4.3.4 Cores seguem paleta Textual ($warning, $accent, $success, $error)

---

## 5. SkyBubble com Markdown (JÁ FEITO)

- [x] 5.1 SkyBubble usa widget `Markdown` do Textual (implementado anteriormente)
- [x] 5.2 `watch_content` atualiza incrementalmente (já suportado)
- [ ] 5.3 Verificar que Markdown renderiza corretamente durante streaming

---

## 6. Compatibilidade e Feature Flags

### 6.1 Modo Legado
- [ ] 6.1.1 `legacy_ui.py` permanece inalterado (usa `messages.create()`)
- [ ] 6.1.2 Feature flag `USE_TEXTUAL_UI=false` ativa modo legado
- [ ] 6.1.3 Verificar que não quebra comportamento existente

### 6.2 Feature Flag
- [ ] 6.2.1 Verificar que `USE_TEXTUAL_UI=true` ativa nova UI com streaming
- [ ] 6.2.2 Testar alternância entre modos
- [ ] 6.2.3 Documentar feature flag em `.env.example`

---

## 7. Polimento e Testes (Fase 4)

### 7.1 Animações e Interações
- [ ] 7.1.1 Botão de toggle [▼]/[▶] funciona corretamente
- [ ] 7.1.2 Botão close [✕] remove ThinkingPanel
- [ ] 7.1.3 Auto-scroll mantém última entrada visível
- [ ] 7.1.4 Transição suave entre colapsado/expandido

### 7.2 Cancelamento de Resposta
- [ ] 7.2.1 Implementar captura de Ctrl+C no ChatScreen
- [ ] 7.2.2 Cancelar generator do worker sem erros
- [ ] 7.2.3 Turn é marcado como estado CANCELLED
- [ ] 7.2.4 Mensagem "Resposta cancelada" aparece no lugar

### 7.3 Testes Unitários
- [ ] 7.3.1 Testar `ClaudeWorker.stream_response()` retorna async generator
- [ ] 7.3.2 Testar `Turn.append_response()` atualiza SkyBubble
- [ ] 7.3.3 Testar `ThinkingPanel.toggle()` alterna estado
- [ ] 7.3.4 Testar `add_thinking_entry()` adiciona entrada correta
- [ ] 7.3.5 Testar streaming com resposta longa (100+ chunks)

### 7.4 Testes E2E
- [ ] 7.4.1 Teste: Primeiro conteúdo aparece em < 500ms
- [ ] 7.4.2 Teste: Texto é atualizado incrementalmente
- [ ] 7.4.3 Teste: ThinkingPanel mostra entradas de pensamento
- [ ] 7.4.4 Teste: Ferramentas são exibidas com status correto
- [ ] 7.4.5 Teste: ThinkingPanel pode ser colapsado/expandido
- [ ] 7.4.6 Teste: Cancelamento funciona sem erros

### 7.5 Documentação
- [ ] 7.5.1 Atualizar `.env.example` com feature flag
- [ ] 7.5.2 Documentar novos métodos em docstrings
- [ ] 7.5.3 Atualizar CLAUDE.md ou docs relevantes se necessário
- [ ] 7.5.4 Adicionar exemplos de uso nos comentários

---

## 8. Rollback e Verificação

### 8.1 Rollback Strategy
- [ ] 8.1.1 Verificar que `legacy_ui.py` funciona se bugs forem encontrados
- [ ] 8.1.2 Feature permite desabilitar streaming via `USE_TEXTUAL_UI=false`
- [ ] 8.1.3 Commits são independentes e podem ser revertidos

### 8.2 Verificação Final
- [ ] 8.2.1 Testar latência < 500ms para primeira resposta
- [ ] 8.2.2 Testar streaming com múltiplas ferramentas
- [ ] 8.2.3 Testar cancelamento e retomada
- [ ] 8.2.4 Testar alternância entre modo legado e novo

---

> "A implementação é a arte de tornar design em realidade" – made by Sky 🚀
