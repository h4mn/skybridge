# Tasks: Sky Chat Textual UI Fix

## 1. Setup e Infraestrutura

- [x] 1.1 Criar estrutura de diretórios para novos widgets (`src/core/sky/chat/textual_ui/widgets/`)
- [x] 1.2 Criar arquivo `widgets/animated_verb.py` vazio com imports necessários
- [x] 1.3 Criar arquivo `widgets/chat_text_area.py` vazio com imports necessários
- [x] 1.4 Criar arquivo `widgets/chat_log.py` vazio com imports necessários
- [x] 1.5 Criar arquivo `widgets/chat_scroll.py` vazio com imports necessários

## 2. AnimatedVerb + EstadoLLM (Maior Complexidade)

### 2.1. EstadoLLM Dataclass
- [x] 2.1.1 Criar dataclass `EstadoLLM` com campos: verbo, certeza, esforco, emocao, direcao
- [x] 2.1.2 Definir valores padrão: "iniciando", 0.8, 0.5, "neutro", 1
- [x] 2.1.3 Adicionar docstring explicando cada dimensão de estado

### 2.2. Sistema de Paletas
- [x] 2.2.1 Criar dataclass `_TemplateCores` com campos `de` e `ate` (hex)
- [x] 2.2.2 Definir dicionário `_PALETAS` com 9 emoções (urgente, debugando, empolgado, em_duvida, pensando, cuidadoso, concluindo, neutro, curioso)
- [x] 2.2.3 Implementar função `_hex_para_rgb(hex_str)` → (r, g, b)
- [x] 2.2.4 Implementar função `_rgb_para_hex(r, g, b)` → hex_str
- [x] 2.2.5 Implementar função `_lerp_cor(cor_a, cor_b, t)` → cor interpolada

### 2.3. Widget AnimatedVerb
- [x] 2.3.1 Criar classe `AnimatedVerb(Static)` com atributos reativos: _offset, _pulso, _estado
- [x] 2.3.2 Implementar `on_mount()` para iniciar timers de sweep e oscilação
- [x] 2.3.3 Implementar `_intervalo_sweep()` que calcula intervalo baseado em certeza/esforco
- [x] 2.3.4 Implementar `_tick_sweep()` para incrementar _offset
- [x] 2.3.5 Implementar `_tick_oscila()` para incrementar _pulso
- [x] 2.3.6 Implementar `render()` que aplica cores letra-por-letra
- [x] 2.3.7 Implementar `update_verbo(novo_verbo)` para atualizar texto sem reiniciar
- [x] 2.3.8 Implementar `update_estado(estado)` para atualizar todas as dimensões
- [x] 2.3.9 Adicionar handler `on_click()` para postar mensagem `Inspecionado`

### 2.4. Tooltip e Modal
- [x] 2.4.1 Implementar `_tooltip_estado(estado)` → string formatada
- [x] 2.4.2 Implementar `watch__estado()` para atualizar tooltip automaticamente
- [x] 2.4.3 Criar classe `EstadoModal(ModalScreen)` para exibir estado completo
- [x] 2.4.4 Implementar `compose()` do EstadoModal com barras de progresso
- [x] 2.4.5 Adicionar botão para fechar modal (ESC também fecha)

## 3. ChatTextArea Customizado

### 3.1. Widget Base
- [x] 3.1.1 Criar classe `ChatTextArea(TextArea)`
- [x] 3.1.2 Definir inner class `Submitted(Message)` com atributo `value: str`
- [x] 3.1.3 Implementar `on_key(event)` para detectar Enter, Shift+Enter, Escape

### 3.2. Comportamento de Chat
- [x] 3.2.1 Implementar Enter: previne default, stop, post Submitted, clear()
- [x] 3.2.2 Implementar Shift+Enter: comportamento padrão (nova linha)
- [x] 3.2.3 Implementar Escape: limpa texto (self.text = "")

### 3.3. Foco Automático
- [x] 3.3.1 Adicionar método para focar o widget (será chamado pela Screen)
- [x] 3.3.2 Implementar lógica de recuperação de foco após fechar modal

### 3.4. Histórico (Opcional)
- [ ] 3.4.1 Adicionar atributo `_historico: list[str]`
- [ ] 3.4.2 Adicionar atributo `_historico_idx: int`
- [ ] 3.4.3 Implementar SetaCima: recupera mensagem anterior
- [ ] 3.4.4 Implementar SetaBaixo: avança para próxima mensagem
- [ ] 3.4.5 Implementar limpeza de histórico ao iniciar nova sessão

## 4. AnimatedTitle Refatorado

### 4.1. De render() para compose()
- [x] 4.1.1 Remover método `render()` do AnimatedTitle
- [x] 4.1.2 Implementar `compose()` que retorna 3 widgets: Static(sujeito), AnimatedVerb, Static(predicado)
- [x] 4.1.3 Adicionar `DEFAULT_CSS` com `layout: horizontal`, `height: 1`, `width: auto`

### 4.2. Métodos de Atualização
- [x] 4.2.1 Implementar `update_title(verbo, predicado)` usando query_one()
- [x] 4.2.2 Implementar `update_estado(estado, predicado)` usando query_one()
- [x] 4.2.3 Garantir que nenhum widget é recriado (apenas atualizado)

## 5. ChatHeader Corrigido

### 5.1. Remover mount() Quebrado
- [x] 5.1.1 Remover método `_update_title()` que usa `mount()`
- [x] 5.1.2 Remover container com `id="title-container"` do compose()

### 5.2. Usar query_one() Corretamente
- [x] 5.2.1 Implementar `update_title(verbo, predicado)` usando `query_one(AnimatedTitle).update_title()`
- [x] 5.2.2 Implementar `update_estado(estado, predicado)` usando `query_one(AnimatedTitle).update_estado()`
- [x] 5.2.3 Implementar `update_context(usage)` para atualizar barra de contexto
- [x] 5.2.4 Implementar `update_metrics(...)` para atualizar métricas do header

## 6. ChatLog e ChatScroll

### 6.1. ChatLog
- [x] 6.1.1 Criar classe `ChatLog(RichLog)` com `markup = True`
- [x] 6.1.2 Implementar `debug(message)` → write com [yellow]
- [x] 6.1.3 Implementar `info(message)` → write com [blue]
- [x] 6.1.4 Implementar `error(message)` → write com [red]
- [x] 6.1.5 Implementar `evento(nome, dados)` → write com [green]

### 6.2. ChatScroll
- [x] 6.2.1 Criar classe `ChatScroll(VerticalScroll)`
- [x] 6.2.2 Implementar `adicionar_mensagem(texto)` → mount + scroll_end
- [x] 6.2.3 Implementar `limpar()` → remove_children

## 7. CSS Completo

### 7.1. Arquivo assets/sky_chat.css
- [x] 7.1.1 Criar ou atualizar `assets/sky_chat.css`
- [x] 7.1.2 Adicionar estilos para SkyBubble e UserBubble
- [x] 7.1.3 Adicionar estilos para AnimatedTitle (layout: horizontal)
- [x] 7.1.4 Adicionar estilos para ChatHeader (dock: top)
- [x] 7.1.5 Adicionar estilos para ChatScroll (height: 1fr)
- [x] 7.1.6 Adicionar estilos para ChatTextArea (min-height: 3, border: thick $accent ao focar)
- [x] 7.1.7 Adicionar estilos para ChatLog (toggleável com display: none/block)
- [x] 7.1.8 Remover `@keyframes color-sweep` se existir (animação agora é Python)

## 8. ChatScreen Refatorada

### 8.1. Layout Correto
- [x] 8.1.1 Substituir `Input` por `ChatTextArea` no compose()
- [x] 8.1.2 Substituir `ScrollView` por `ChatScroll`
- [x] 8.1.3 Adicionar `ChatLog` antes do Footer
- [x] 8.1.4 Remover handler `on_input_submitted()`

### 8.2. Handlers Novos
- [x] 8.2.1 Implementar `on_chat_text_area_submitted(event)`
- [x] 8.2.2 Implementar `on_animated_verb_inspecionado(event)` → push_screen(EstadoModal)
- [x] 8.2.3 Implementar `action_toggle_log()` para mostrar/ocultar ChatLog

### 8.3. Foco Automático
- [x] 8.3.1 Implementar `on_mount()` para focar ChatTextArea
- [x] 8.3.2 Garantir que foco retorna após enviar mensagem

## 9. WelcomeScreen com ASCII Art

### 9.1. Banner ASCII Art
- [x] 9.1.1 Criar Static com banner ASCII art "SkyBridge" (estilo box drawing)
- [x] 9.1.2 Adicionar linha separadora com "═"
- [x] 9.1.3 Adicionar texto "Chat Interface by Sky 🚀"
- [x] 9.1.4 Adicionar texto "Bem-vindo ao SkyBridge!"

### 9.2. ChatTextArea na Welcome
- [x] 9.2.1 Substituir `Input` por `ChatTextArea` no compose()
- [x] 9.2.2 Remover handler `on_input_submitted()`
- [x] 9.2.3 Implementar `on_chat_text_area_submitted(event)` → push_screen(ChatScreen)

### 9.3. CSS da Welcome
- [x] 9.3.1 Adicionar CSS para `#welcome-container` (align: center middle)
- [x] 9.3.2 Adicionar CSS para `.splash-banner` (text-align: center, font-family: monospace)
- [x] 9.3.3 Adicionar CSS para `#first-input` (width: 60)

## 10. Testes TDD (Red → Green → Refactor)

### 10.1. Testes de AnimatedVerb
- [ ] 10.1.1 RED: Testar que AnimatedVerb exibe texto inicial
- [ ] 10.1.2 GREEN: Implementar render básico
- [ ] 10.1.3 RED: Testar que animação de sweep é iniciada no on_mount
- [ ] 10.1.4 GREEN: Implementar set_interval
- [ ] 10.1.5 RED: Testar que cores são aplicadas letra-por-letra
- [ ] 10.1.6 GREEN: Implementar lógica de interpolação
- [ ] 10.1.7 RED: Testar update_verbo() não reinicia animação
- [ ] 10.1.8 GREEN: Implementar update_verbo
- [ ] 10.1.9 RED: Testar update_estado() muda cores/velocidade
- [ ] 10.1.10 GREEN: Implementar update_estado

### 10.2. Testes de ChatTextArea
- [ ] 10.2.1 RED: Testar que Enter posta Submitted e limpa texto
- [ ] 10.2.2 GREEN: Implementar on_key para Enter
- [ ] 10.2.3 RED: Testar que Shift+Enter insere newline
- [ ] 10.2.4 GREEN: Implementar on_key para Shift+Enter
- [ ] 10.2.5 RED: Testar que Escape limpa texto
- [ ] 10.2.6 GREEN: Implementar on_key para Escape

### 10.3. Testes de AnimatedTitle
- [ ] 10.3.1 RED: Testar que compose() retorna 3 widgets
- [ ] 10.3.2 GREEN: Implementar compose
- [ ] 10.3.3 RED: Testar que update_title() atualiza sem recriar
- [ ] 10.3.4 GREEN: Implementar update_title com query_one

### 10.4. Testes de ChatHeader
- [ ] 10.4.1 RED: Testar que update_title() não acumula widgets
- [ ] 10.4.2 GREEN: Implementar update_title com query_one
- [ ] 10.4.3 RED: Testar que update_estado() propaga para AnimatedTitle
- [ ] 10.4.4 GREEN: Implementar update_estado

### 10.5. Testes de Integração ChatScreen
- [ ] 10.5.1 RED: Testar fluxo completo: mensagem → Submitted → UserBubble
- [ ] 10.5.2 GREEN: Implementar handler completo
- [ ] 10.5.3 RED: Testar que clique no verbo exibe modal
- [ ] 10.5.4 GREEN: Implementar on_animated_verb_inspecionado
- [ ] 10.5.5 RED: Testar que Ctrl+L toggle ChatLog
- [ ] 10.5.6 GREEN: Implementar action_toggle_log

### 10.6. Testes de WelcomeScreen
- [ ] 10.6.1 RED: Testar que banner ASCII art é exibido
- [ ] 10.6.2 GREEN: Implementar compose com banner
- [ ] 10.6.3 RED: Testar que primeira mensagem transita para ChatScreen
- [ ] 10.6.4 GREEN: Implementar on_chat_text_area_submitted

## 11. Validação Final

- [ ] 11.1 Executar testes completos e garantir que todos passam
- [ ] 11.2 Executar aplicação e validar que WelcomeScreen exibe banner ASCII art corretamente
- [ ] 11.3 Enviar mensagem primeira e validar transição para ChatScreen
- [ ] 11.4 Validar que verbo está animando com color sweep
- [ ] 11.5 Clicar no verbo e validar que EstadoModal é exibido
- [ ] 11.6 Pressionar Ctrl+L e validar que ChatLog aparece
- [ ] 11.7 Enviar múltiplas mensagens e validar que título é atualizado
- [ ] 11.8 Validar que Shift+Enter insere nova linha e Enter envia
- [ ] 11.9 Validar que Escape limpa o texto
- [ ] 11.10 Verificar que não há widgets acumulando (memória estável)

---

> "Todo teste é uma especificação viva, todo checkbox é um passo em direção à qualidade" – made by Sky 🚀
