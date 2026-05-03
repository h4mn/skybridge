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
- **Fase 1 (ATUAL):** Reusa prefab de borboleta do próprio jogo. Busca assets com `Resources.FindObjectsOfTypeAll<GameObject>()` por nomes como `Butterfly`, `WorldFlockButterfly`. Se o asset ainda não carregou, busca periodicamente (a cada 5s) e troca automaticamente. Fallback com primitivas (capsule + quads) usando shader `Unlit/Color` e asas double-sided.
- **Fase 2 (FUTURO):** Diferenciar Lorpen e Oesbe por cor/textura. Mapear assets `WorldFlockButterfly` vs `WorldFlockButterflyBlack` para as duas formas.

**Alternativas consideradas:**
- Capsule + cubo (cacto Crumpet): funcional mas sem personalidade
- Borboleta fixa (sem evolução): perde a conexão narrativa com a terraformação
- GLTF em runtime: requer biblioteca extra (UniGLTF)
- AssetBundle desde o início: bloqueia desenvolvimento enquanto modelo não existe

**Rationale:** A evolução Lorpen→Oesbe conecta a Sky ao progresso do jogador — ela cresce junto com o planeta. Reusar os prefabs de borboleta do jogo (Lorpen/Oesbe) é zero esforço e tematicamente perfeito. O fallback com primitivas é simples e funcional.

### D3: Chat via Harmony prefix no UiWindowChat.OnSendText

**Escolha:** Usar Harmony prefix patch em `UiWindowChat.OnSendText` para capturar TODAS as mensagens do chat (sem prefixo). O mod captura a mensagem E deixa o chat vanilla funcionar normalmente.

**Fluxo da resposta:** jogador digita no chat → Harmony prefix captura texto de `_inputField` (TMP_InputField) → push imediato via POST para MCP server → retorna `true` (chat vanilla continua) → Channel MCP envia notificação → Claude responde via `send_companion_message` tool → mod exibe overlay no topo da tela.

**Implementação:** `SkyChatHandler` usa reflection para acessar `_inputField` na instância de `UiWindowChat`. O prefix retorna `true` para todas as mensagens (deixa o chat vanilla processar). O texto é capturado ANTES do método original e enviado ao MCP via fire-and-forget HTTP POST.

**Rationale:** Postfix não funciona — `OnSendText` já limpou o `_inputField` quando o postfix roda. Prefix captura o texto intacto. Removemos o prefixo `/skychat` porque UX real mostrou que digitar direto é melhor — o chat do jogo já tem histórico próprio.

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

### D7: Push Direto — Mod POSTa evento para MCP Server (sem polling)

**Escolha:** O mod C# faz POST direto para o MCP server Python (`localhost:17235/incoming`) sempre que um evento significativo acontece. O MCP server envia `JSONRPCNotification` imediatamente. Sem polling, sem throttle, sem cursor.

**O problema do polling original:** O design anterior usava polling (`GET /events` a cada 2-10s) com throttling diferenciado. Isso adicionava latência (até 10s), complexidade (cursor, throttle por tipo) e bugs (drain pattern, cursor timing).

**A solução — push imediato:**
1. **Mod C# POSTa eventos** — `HttpClient` fire-and-forget para `localhost:17235/incoming`
2. **MCP server recebe e notifica** — `aiohttp` handler envia `JSONRPCNotification` instantaneamente
3. **Tool `get_game_state()` para contexto sob demanda** — Quando Claude Code precisa de contexto detalhado

**Arquitetura:**
```
Jogador digita → Harmony patch captura → POST /incoming → JSONRPCNotification → Claude Code
Milestone → GameHooks detecta → POST /incoming → JSONRPCNotification → Claude Code
```

**Alternativas consideradas:**
- Polling de eventos: latência + complexidade (design original, eliminado)
- WebSocket: mais eficiente mas complexo no C# sem deps extras
- Sem channel, só tools: Claude Code não saberia quando reagir

**Rationale:** Push direto é instantâneo (< 1s), zero complexidade no MCP server, e o mod C# já tem HttpClient disponível. O EventFilter e GET /events ainda existem no mod para debug, mas não são mais o canal principal.

**Escolha:** O `CompanionAdapter` Python é um thin wrapper sobre `http://localhost:17234`.

**Rationale:** Toda lógica de jogo fica no mod C# (onde tem acesso direto às APIs Unity). O Python só traduz HTTP ↔ interface `CompanionAdapter`. Mantém o adapter simples e testável com mocks.

## Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│  The Planet Crafter (Unity)                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SkyTpcMod (BepInEx)                                  │  │
│  │                                                        │  │
│  │  GameHooks ──► lê estado via SpaceCraft API            │  │
│  │       │           (WorldUnitsHandler, PlayersManager)  │  │
│  │       ▼                                                │  │
│  │  EventFilter ──► filtra eventos significativos         │  │
│  │    ✅ milestones, story, chat                          │  │
│  │       │                                                │  │
│  │       ▼                                                │  │
│  │  HttpServer (porta 17234)                              │  │
│  │    GET /state           → JSON terraform+player        │  │
│  │    GET /events?since=N  → eventos desde cursor         │  │
│  │    POST /action         → comandos no jogo             │  │
│  │       │                                                │  │
│  │  SkyChatHandler ──► Harmony prefix em OnSendText       │  │
│  │    captura TUDO (sem prefixo) → return true            │  │
│  │    PushToMcp() ──► POST http://localhost:17235/incoming│  │
│  │                                                        │  │
│  │  CompanionController (mono)                            │  │
│  │    Modelo: prefab Butterfly_LOD1 do jogo               │  │
│  │    Fallback: primitivas (Unlit/Color)                  │  │
│  │    Evolução: Lorpen → Oesbe (quando insects > 0)       │  │
│  │    Overlay: OnGUI flash no topo (30s, pisca 3x)        │  │
│  │    Instância estática: CompanionController.Instance     │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP (localhost)
                       │ 17234 (mod → tools)
                       │ 17235 (mod → push incoming)
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  planet-crafter-channel.py (MCP Server via stdio)            │
│                                                              │
│  HTTP Server (aiohttp, porta 17235):                         │
│    POST /incoming → JSONRPCNotification instantâneo          │
│                                                              │
│  Tools (POST localhost:17234/action):                        │
│    send_companion_message(text) → show_message               │
│    move_companion_to(strategy)  → move                       │
│    set_companion_animation(a)  → set_animation              │
│    get_game_state()            → GET /state                 │
│    add_session_note(text)                                    │
│    get_session_summary()                                     │
│                                                              │
│  Capability: experimental = {"claude/channel": {}}           │
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
