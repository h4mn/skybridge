## 1. Infraestrutura do Mod (C#)

- [x] 1.1 Configurar HttpServer com porta configurável via BepInEx ConfigEntry (default 17234)
- [x] 1.2 Implementar GET /state retornando JSON com terraform, posição do jogador, inventário
- [x] 1.3 Implementar GET /events retornando fila de eventos significativos (cursor-based)
- [x] 1.4 Implementar POST /action aceitando comandos (show_message, set_animation, move)
- [ ] 1.5 Escrever testes unitários para HttpServer (validação de rotas, JSON serialization)

## 2. EventFilter e Eventos Significativos

- [x] 2.1 Implementar EventFilter no mod C# que mantém fila de significant_events
- [x] 2.2 Adicionar detection de milestone de terraformação como evento significativo
- [ ] 2.3 Adicionar detection de morte do jogador → **MOVIDO PARA SPRINT FUTURA** (PlayerGaugeHealth API não encontrada)
- [ ] 2.4 Escrever testes para EventFilter → **MOVIDO PARA SPRINT FUTURA**

## 3. Modelo 3D — Borboleta Evolutiva

- [x] 3.1 Implementar CompanionController com modelo próximo ao jogador
- [x] 3.2 Implementar fallback com primitivas Unity (Unlit/Color, double-sided wings)
- [x] 3.3 Implementar animações: idle, thinking, speaking (batida de asas)
- [x] 3.4 Controle de animação via POST /action type "set_animation"
- [x] 3.5 Evolução Lorpen→Oesbe: detectar insects > 0 e trocar cor
- [x] 3.6 Em save avançado o modelo já nasce como Oesbe
- [x] 3.7 Busca automática de prefab de borboleta do jogo (Butterfly_LOD1)
- [x] 3.8 Fallback periódico: busca asset a cada 5s até encontrar
- [ ] 3.9 Diferenciar visualmente Lorpen vs Oesbe com assets distintos → **MOVIDO PARA SPRINT FUTURA**

## 4. Balão de Fala World-Space

- [x] 4.1 Implementar balão TextMeshPro em world-space acima do modelo 3D
- [x] 4.2 Implementar escala de font size por distância ao jogador
- [x] 4.3 Implementar fade-out do balão após 5 segundos
- [x] 4.4 Distância configurável do companion ao jogador (default ~3 unidades)
- [ ] 4.5 Fix shader do TextMeshPro em world-space → **MOVIDO PARA SPRINT FUTURA** (balão existe mas não renderiza visivelmente)

## 5. Chat Bidirecional

- [x] 5.1 Harmony prefix em UiWindowChat.OnSendText captura todas as mensagens (sem prefixo)
- [x] 5.2 Push imediato via POST para MCP server (localhost:17235/incoming)
- [x] 5.3 return true = chat vanilla funciona normalmente (mensagens aparecem no histórico do jogo)
- [x] 5.4 POST /action type "show_message" → overlay no topo da tela (flash 3x, 30s visível)
- [x] 5.5 Fix Harmony postfix → prefix: capturar texto ANTES de OnSendText limpar o _inputField
- [x] 5.6 Null recovery: GameHooks reconecta via CompanionController.Instance quando _companion é null

## 6. DestinationStrategy — Movimentação

- [x] 6.1 Implementar follow_player: seguir jogador mantendo distância configurável
- [x] 6.2 Implementar goto_coords(x, y, z): mover para coordenada
- [x] 6.3 Implementar goto_named(name): mover para local nomeado do registro
- [x] 6.4 Implementar stay: parar no local atual
- [x] 6.5 Conectar POST /action type "move" ao DestinationStrategy

## 7. Channel MCP (Python) — Push Direto

- [x] 7.1 Criar planet-crafter-channel.py com MCP Server via stdio
- [x] 7.2 Declarar capability experimental claude/channel na inicialização
- [x] 7.3 HTTP server aiohttp na porta 17235 recebendo POST /incoming do mod
- [x] 7.4 Push imediato: POST /incoming → JSONRPCNotification (sem polling, sem throttle)
- [x] 7.5 Tool send_companion_message(text) → POST /action no mod
- [x] 7.6 Tool move_companion_to(strategy, params) → POST /action
- [x] 7.7 Tool set_companion_animation(animation) → POST /action
- [x] 7.8 Tool get_game_state() → GET /state
- [x] 7.9 Tool add_session_note(text) e get_session_summary()
- [x] 7.10 Testes: 29 testes passando (unit + E2E com MockModServer)

## 8. Sessão de Jogatina

- [x] 8.1 Sessão criada no primeiro evento recebido
- [x] 8.2 Registro de eventos na sessão (milestone, skychat, note)
- [x] 8.3 Tool add_session_note(text)
- [x] 8.4 Tool get_session_summary()
- [x] 8.5 Testes para gerenciamento de sessão

## 9. Integração E2E

- [x] 9.1 Entrada do channel no .mcp.json do skybridge
- [x] 9.2 E2E validado: mod rodando → push direto → Claude Code recebe notificação via channel
- [x] 9.3 E2E validado: chat no jogo → push → notificação → resposta via tool → overlay no topo
- [ ] 9.4 Documentar setup: como instalar o mod, configurar o channel, usar no Claude Code

## Sprint Futura (pendências)

- [ ] F1 Detecção de morte do jogador (PlayerGaugeHealth API)
- [ ] F2 Testes unitários C# (HttpServer, EventFilter)
- [ ] F3 Diferenciar Lorpen vs Oesbe visualmente (assets distintos, texturas)
- [ ] F4 Fix shader TextMeshPro world-space (balão de fala 3D)
- [ ] F5 Documentação de setup e uso
