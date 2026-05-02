## Context

O projeto Skybridge já possui o bounded context `src/core/companion/` com:
- Interface abstrata `CompanionAdapter` (`_base.py`) com `connect()`, `get_context()`, `send_message()`, `execute_action()`, `disconnect()`
- Dataclass `GameContext` para snapshot do estado
- Classes `CompanionState`, `CompanionSession` no core game-agnostic
- Stubs de adapters para Minecraft e Planet Craft

O repositório `sky-tpc-mod/` (C#) já possui scaffold funcional:
- `Plugin.cs` — entry point BepInEx
- `GameHooks.cs` — acesso ao estado via `Managers.GetManager<WorldUnitsHandler>()` e `PlayersManager`
- `HttpServer.cs` — GET `/state`, GET `/events`, POST `/action` em `localhost:17234`
- `HarmonyPatches.cs` — patch em `WorldUnitsHandler.CreateUnits`
- **Já builda e funciona** — retorna dados reais de terraformação, posição e inventário

O Discord Channel MCP (`discord_channel_mcp.py`) é a referência de implementação: MCP server via stdio que pusha notificações para Claude Code.

## Goals / Non-Goals

**Goals:**
- Sky como companheira visível no jogo com modelo 3D e animações
- Comunicação bidirecional: jogador fala com Sky (`/skychat`) e Sky fala com jogador (balão de fala)
- Claude Code recebe eventos do jogo em tempo real via Channel MCP
- Claude Code pode enviar comandos ao jogo via MCP Tools
- Sessão de jogatina rastreável (eventos, notas, duração)

**Non-Goals:**
- Multiplayer (Sky Companion é single-player)
- Suporte a jogos além de Planet Crafter nesta iteração
- IA autônoma tomando decisões sem o jogador (Sky reage, não joga sozinha)
- Integração com TTS/STT nesta iteração (futuro)

## Decisions

### D1: HTTP REST como protocolo entre Mod e Channel MCP

**Escolha:** Mod expõe API REST em `localhost:17234` (porta configurável via BepInEx `ConfigEntry<int>`); Channel MCP consulta eventos filtrados.

**Alternativas consideradas:**
- WebSocket: mais eficiente mas adiciona complexidade ao mod C# e requer threading dedicado
- Named pipe: limitado ao Windows, não Portable
- File watching: latência alta, parsing pesado

**Rationale:** HTTP REST é simples, funciona em Unity sem dependências extras (`HttpListener` nativo). O channel faz polling leve (10s) apenas da fila de eventos significativos — não do estado completo.

### D2: Modelo 3D — borboleta que evolui com a terraformação

**Escolha:** Sky é uma borboleta que **evolui** com o estágio de terraformação do planeta:
1. **Antes do oxigênio (insetos):** **Lorpen** — borboleta comum (600% insect mass), selvagem no jogo. Simboliza o início da vida.
2. **Após oxigênio atingir estágio de insetos:** **Oesbe** — borboleta rara (1500% insect mass), obtida via Space Trading Rocket ou Planet Humble. Simboliza a maturação do ecossistema.

**Implementação em fases:**
- **Debug/desenvolvimento:** Tentar reusar prefab de borboleta do próprio jogo (Planet Crafter tem Lorpen e Oesbe nos assets). Se prefab não for acessível, montar borboleta com primitivas: dois quads coloridos como asas + corpo fino (capsule escalada), animação de bater asas via `transform.Rotate()`. Cor/textura diferenciam Lorpen (simples) de Oesbe (mais elaborada).
- **Produção:** AssetBundle `.asset` carregado em runtime, substituindo o modelo de debug quando disponível.

**Alternativas consideradas:**
- Capsule + cubo (cacto Crumpet): funcional mas sem personalidade
- Borboleta fixa (sem evolução): perde a conexão narrativa com a terraformação
- GLTF em runtime: requer biblioteca extra (UniGLTF)
- AssetBundle desde o início: bloqueia desenvolvimento enquanto modelo não existe

**Rationale:** A evolução Lorpen→Oesbe conecta a Sky ao progresso do jogador — ela cresce junto com o planeta. Reusar os prefabs de borboleta do jogo (Lorpen/Oesbe) é zero esforço e tematicamente perfeito. O fallback com primitivas é simples e funcional.

### D3: Chat via comando de console customizado

**Escolha:** Usar o sistema de input do jogo para capturar `/skychat <mensagem>`.

**Fluxo da resposta:** `/skychat` → mod enfileira evento → Channel MCP detecta e notifica Claude Code → Claude responde via `send_companion_message` tool → mod exibe balão sobre o modelo 3D. Direto, sem endpoint intermediário.

**Rationale:** O Planet Crafter não tem chat multiplayer, mas tem sistema de input. O mod registra um handler que captura o comando, enfileira como evento significativo. O akarnokd tem um mod `FeatCommandConsole` que demonstra como fazer isso.

### D3.1: Balão de fala world-space com escala controlada

**Escolha:** Balão de fala como `TextMeshPro` em world-space posicionado acima do modelo 3D.

**Constraint de distância:** O companion DEVE manter distância configurável do jogador (default ~3 unidades Unity). O font size do TextMeshPro escala com a distância para manter legibilidade — nem muito grande (ilegível colado) nem muito pequeno (ilegível longe). Essa escala é calibrada empiricamente durante desenvolvimento.

**Rationale:** World-space é mais imersivo que UI overlay. A constraint de distância garante que o texto sempre esteja na zona de leitura confortável.

### D4: Channel MCP + Tools no mesmo servidor

**Escolha:** Um único MCP server faz tanto o channel (push de notificações) quanto expõe tools (comandos).

**Rationale:** Simplifica configuração (uma entrada no `.mcp.json`). O `discord_channel_mcp.py` já segue esse padrão: mesmo server tem tools (`send_discord_message`) e channel capability.

### D5: DestinationStrategy para movimentação do companion

**Escolha:** `move_companion_to` recebe uma estratégia, não coordenadas cruas.

**Estratégias:**
- `follow_player` — segue o jogador mantendo distância
- `goto_coords(x, y, z)` — vai para coordenada específica do mapa
- `goto_named(name)` — vai para local nomeado (ex: "base", "último beacon")
- `stay` — fica parada no local atual

**Rationale:** O Claude Code decide a estratégia ("siga o jogador", "vá para a base"), não coordenadas numéricas. O mod C# traduz a estratégia em pathfinding/converção. Isso mantém o MCP tool simples e a inteligência de navegação no lado do jogo, onde tem acesso ao navmesh e collision.

### D7: Event-Driven com Filtro de Relevância (não polling burro)

**Escolha:** Mod filtra eventos significativos no lado C#; Channel MCP só pusha quando há eventos relevantes; Claude Code consulta estado sob demanda via tool.

**O problema do polling:** Enviar notificação a cada 3 segundos consome quota do Claude Code com informação irrelevante (posição mudou 0.1, O2 subiu 0.01). Isso é tóxico para o contexto e para a cota.

**A solução — 3 camadas:**

1. **Mod C# filtra o que importa** — mantém fila de `significant_events`:
   - ✅ Milestone de terraformação ("Primeira chuva!", "Insetos apareceram!")
   - ✅ Morte do jogador
   - ✅ Mensagem `/skychat` do jogador
   - ✅ Story event / narrativa
   - ✅ Construção concluída
   - ❌ Posição mudou
   - ❌ O2 subiu 0.1
   - ❌ Inventário +/- 1 item

2. **Channel MCP pusha apenas eventos filtrados** — polling leve de `GET /events` a cada 10s. Só envia `JSONRPCNotification` se a fila não estiver vazia. Intervalo mínimo de 30s entre notificações para não lotar o contexto.

3. **Tool `get_game_state()` para contexto sob demanda** — Quando Claude Code precisa de contexto (jogador pediu dica, `/skychat` disparou, ou quer saber "como tá o terraform"), chama a tool. Sem push, sem waste.

**Alternativas consideradas:**
- Polling de estado completo a cada 3s: desperdício de quota e contexto
- WebSocket push de todos os eventos: mesma waste, mais complexidade
- Sem channel, só tools: Claude Code não saberia quando reagir proativamente

**Rationale:** O filtro no lado do mod é barato (C# comparando thresholds). O channel vira um throttler inteligente. E o tool dá contexto sob demanda quando Claude precisa. O resultado é ~5-15 notificações por hora de jogatina (vs. 1200 com polling burro).

**Escolha:** O `CompanionAdapter` Python é um thin wrapper sobre `http://localhost:17234`.

**Rationale:** Toda lógica de jogo fica no mod C# (onde tem acesso direto às APIs Unity). O Python só traduz HTTP ↔ interface `CompanionAdapter`. Mantém o adapter simples e testável com mocks.

## Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│  The Planet Crafter (Unity)                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SkyTpcMod (BepInEx)                                  │  │
│  │                                                        │  │
│  │  │  GameHooks ──► lê estado via SpaceCraft API            │  │
│  │       │           (WorldUnitsHandler, PlayersManager)  │  │
│  │       ▼                                                │  │
│  │  EventFilter ──► filtra eventos significativos         │  │
│  │    ✅ milestones, mortes, story, /skychat              │  │
│  │    ❌ posição, O2+0.1, inventário-1                    │  │
│  │       │                                                │  │
│  │       ▼                                                │  │
│  │  HttpServer (porta config, default :17234)             │  │
│  │    GET /state     → JSON terraform+player+inventory    │  │
│  │    GET /events    → eventos recentes                   │  │
│  │    POST /action   → comandos no jogo                  │  │
│  │    POST /chat     → recebe msg do /skychat             │  │
│  │                                                        │  │
│  │  SkyModel3D ──► Lorpen (pré-O2) → Oesbe (pós-O2)       │  │
│  │    evolui com terraformação (prefab jogo ou primitivas)│  │
│  │    animações: idle (voando), thinking, speaking        │  │
│  │    balão world-space (TMP) com escala por distância    │  │
│  │    distância do jogador: configurável (~3 unidades)    │  │
│  │                                                        │  │
│  │  ChatHandler ──► captura /skychat                      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP (localhost, porta config)
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  planet-crafter-channel.py (MCP Server via stdio)            │
│                                                              │
│  Channel: polling GET /events a cada 10s (throttle 30s)     │
│    eventos filtrados → JSONRPCNotification → Claude Code     │
│                                                              │
│  Tools:                                                      │
│    send_companion_message(text) → POST /action               │
│    move_companion_to(strategy)  → POST /action               │
│      strategy: follow_player | goto_coords | goto_named | stay│
│    set_companion_animation(a)  → POST /action               │
│    get_game_state()            → GET /state                 │
│                                                              │
│  Configurado em .mcp.json com capabilities.experimental      │
│  = {"claude/channel": {}}                                    │
└──────────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Polling consome CPU | Intervalo de 10s com throttle de 30s é suficiente; Planet Crafter muda devagar |
| AssetBundle de modelo 3D pode falhar em versões diferentes do Unity | Fallback para primitive shape; testar com versão específica do jogo |
| `HttpListener` pode ter conflito de porta | Detectar porta em uso e logar erro claro |
| Chat `/skychat` pode conflitar com outros mods de comando | Verificar como akarnokd resolve em `FeatCommandConsole` |
| Modelo 3D da Sky ainda não existe | Borboleta de debug (prefab do jogo ou primitivas) permite desenvolvimento imediato; evolução Lorpen→Oesbe usa mesmos assets do jogo |
| Balão de fala pode ficar ilegível a certas distâncias | Distância do companion ao jogador é configurável; font size do TextMeshPro escala com distância |
| Mod pode crashar o jogo se patches Harmony mudarem com update | Versão do jogo verificada no load; log claro de erros |

## Open Questions

- **Modelo 3D de produção**: Quem cria o modelo final da Sky? Asset existente ou encomendado? (modelo de debug com primitives já definido)
- **Calibração do balão**: A escala exata do TextMeshPro e distância ideal do companion precisam ser calibradas empiricamente no jogo
