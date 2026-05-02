## 1. Infraestrutura do Mod (C#)

- [ ] 1.1 Configurar HttpServer com porta configurável via BepInEx ConfigEntry (default 17234) — ref: spec `game-state-provider`, design D1
- [ ] 1.2 Implementar GET /state retornando JSON com terraform, posição do jogador, inventário — ref: spec `game-state-provider` req 1
- [ ] 1.3 Implementar GET /events retornando fila de eventos significativos — ref: spec `game-state-provider` req 2
- [ ] 1.4 Implementar POST /action aceitando comandos (show_message, set_animation, move) — ref: spec `game-state-provider` req 3
- [ ] 1.5 Escrever testes unitários para HttpServer (validação de rotas, JSON serialization, porta configurável)

## 2. EventFilter e Eventos Significativos

- [ ] 2.1 Implementar EventFilter no mod C# que mantém fila de significant_events — ref: design D7
- [ ] 2.2 Adicionar detection de milestone de terraformação como evento significativo — ref: spec `game-state-provider` req 2
- [ ] 2.3 Adicionar detection de morte do jogador como evento significativo
- [ ] 2.4 Escrever testes para EventFilter (thresholds, tipos de evento, fila FIFO)

## 3. Modelo 3D — Borboleta Evolutiva

- [ ] 3.1 Implementar SkyModel3D que instancia modelo próximo ao jogador — ref: spec `companion-3d-model` req 1
- [ ] 3.2 Implementar fallback com primitivas Unity (2 quads como asas + capsule como corpo) — ref: spec `companion-3d-model` req 1
- [ ] 3.3 Implementar animações: idle (asas batendo suavemente), thinking (asas lentas), speaking (asas ativas + balão) — ref: spec `companion-3d-model` req 2
- [ ] 3.4 Implementar controle de animação via POST /action com type "set_animation" — ref: spec `companion-tools` req 3
- [ ] 3.5 Implementar evolução Lorpen→Oesbe: detectar estágio de oxigênio/insetos e trocar modelo — ref: spec `companion-3d-model` req 1, design D2
- [ ] 3.6 Garantir que em save avançado o modelo já nasce como Oesbe — ref: spec `companion-3d-model` req 1

## 4. Balão de Fala World-Space

- [ ] 4.1 Implementar balão TextMeshPro em world-space acima do modelo 3D — ref: spec `companion-3d-model` req 4, design D3.1
- [ ] 4.2 Implementar escala de font size por distância ao jogador (legibilidade) — ref: spec `companion-3d-model` req 4
- [ ] 4.3 Implementar fade-out do balão após 5 segundos sem nova mensagem — ref: spec `companion-3d-model` req 4
- [ ] 4.4 Garantir distância configurável do companion ao jogador (default ~3 unidades) — ref: spec `companion-3d-model` req 3

## 5. Chat /skychat

- [ ] 5.1 Implementar handler de input que captura /skychat <mensagem> — ref: spec `companion-chat` req 1
- [ ] 5.2 Enfileirar mensagem como evento tipo "skychat" no EventFilter — ref: spec `companion-chat` req 1
- [ ] 5.3 Exibir confirmação visual no jogo ao capturar comando
- [ ] 5.4 Validar comando vazio (exibir "Uso: /skychat <mensagem>") — ref: spec `companion-chat` req 1
- [ ] 5.5 Conectar POST /action type "show_message" ao balão de fala — ref: spec `companion-chat` req 2

## 6. DestinationStrategy — Movimentação

- [ ] 6.1 Implementar follow_player: seguir jogador mantendo distância configurável — ref: spec `companion-tools` req 2
- [ ] 6.2 Implementar goto_coords(x, y, z): mover para coordenada — ref: spec `companion-tools` req 2
- [ ] 6.3 Implementar goto_named(name): mover para local nomeado do registro — ref: spec `companion-tools` req 2
- [ ] 6.4 Implementar stay: parar no local atual — ref: spec `companion-tools` req 2
- [ ] 6.5 Conectar POST /action type "move" ao DestinationStrategy — ref: design D5

## 7. Channel MCP (Python)

- [ ] 7.1 Criar planet-crafter-channel.py com MCP Server via stdio — ref: design D4, spec `channel-mcp-companion`
- [ ] 7.2 Declarar capability experimental claude/channel na inicialização — ref: spec `channel-mcp-companion` req 3
- [ ] 7.3 Implementar polling de GET /events a cada 10s com JSONRPCNotification — ref: spec `channel-mcp-companion` req 1
- [ ] 7.4 Implementar throttling de 30s entre notificações (agrupar eventos) — ref: spec `channel-mcp-companion` req 2
- [ ] 7.5 Implementar reconexão automática ao mod (log + retry) — ref: spec `channel-mcp-companion` req 4
- [ ] 7.6 Implementar tool send_companion_message(text) → POST /action — ref: spec `companion-tools` req 1
- [ ] 7.7 Implementar tool move_companion_to(strategy, params) → POST /action — ref: spec `companion-tools` req 2
- [ ] 7.8 Implementar tool set_companion_animation(animation) → POST /action — ref: spec `companion-tools` req 3
- [ ] 7.9 Implementar tool get_game_state() → GET /state — ref: spec `companion-tools` req 4
- [ ] 7.10 Escrever testes para o Channel MCP (mock HTTP, throttling, capability declaration)

## 8. Sessão de Jogatina

- [ ] 8.1 Implementar criação de sessão ao primeiro polling bem-sucedido — ref: spec `companion-session` req 1
- [ ] 8.2 Implementar registro de eventos na sessão (milestone, skychat, note) — ref: spec `companion-session` req 2
- [ ] 8.3 Implementar tool add_session_note(text) — ref: spec `companion-session` req 3
- [ ] 8.4 Implementar encerramento de sessão após 60s de indisponibilidade — ref: spec `companion-session` req 4
- [ ] 8.5 Implementar tool get_session_summary() — ref: spec `companion-session` req 5
- [ ] 8.6 Escrever testes para gerenciamento de sessão

## 9. Configuração e Integração

- [ ] 9.1 Adicionar entrada do channel no .mcp.json do skybridge
- [ ] 9.2 Validar integração E2E: mod rodando → channel conectado → Claude Code recebe notificações
- [ ] 9.3 Validar integração E2E: /skychat → notificação → resposta via tool → balão no jogo
- [ ] 9.4 Documentar setup: como instalar o mod, configurar o channel, usar no Claude Code
