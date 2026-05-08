# ONBOARD — Companion Sky no Planet Crafter

Guia rápido para uma nova sessão entender os 2 projetos que formam o mod.

## Projetos

| | Backend (Python) | Frontend (C# Mod) |
|---|---|---|
| **Repo** | `B:\_repositorios\skybridge` | `B:\_repositorios\sky-tpc-mod` |
| **Papel** | MCP server, testes, specs | Mod BepInEx que roda dentro do jogo |
| **Linguagem** | Python 3.11 | C# / netstandard2.1 |
| **Framework** | FastMCP | BepInEx 5 + Unity 2023.2 |

## Comunicação

```
  Claude Code ←→ MCP Server (Python) ←→ HTTP ←→ Mod C# (dentro do jogo)
  :17235            planet_crafter_companion.py    :17234 HttpServer.cs
```

- **MCP Server** (`apps/mcp_servers/planet_crafter_companion.py`): tools que o Claude chama (send_companion_message, move_companion_to, get_game_state, etc.)
- **Mod HTTP** (`sky-tpc-mod/.../HttpServer.cs`): recebe comandos do MCP e executa no jogo
- **Channel MCP**: eventos do jogo chegam como notificações (milestone, skychat, death, note)
- **SkyChatHandler**: captura chat do jogo (`/skychat` prefix) e envia pro MCP server

## Arquivos Chave

### Backend (skybridge)

```
apps/mcp_servers/planet_crafter_companion.py   # MCP server com todas as tools
src/core/companion/movement/
  interfaces.py      # IMovementState (ABC)
  context.py         # MovementContext (frozen dataclass)
  state_machine.py   # MovementStateMachine + StateType + MovementConfig
tests/unit/movement/                       # 58 testes (TDD)
openspec/changes/sky-companion-movement-strategies/  # specs, design, tasks
```

### Frontend (sky-tpc-mod)

```
src/SkyTpcMod/
  Plugin.cs                    # Entry point BepInEx
  CompanionController.cs       # MonoBehaviour principal — spawn, update, visual
  HttpServer.cs                # Recebe comandos HTTP do MCP
  GameHooks.cs                 # Eventos do jogo (milestone, terraform, etc.)
  SkyChatHandler.cs            # Patch no chat do jogo
  HarmonyPatches.cs            # Harmony patches
  DestinationStrategy.cs       # MoveStrategy enum
  Movement/
    MovementStateMachine.cs    # State machine com 13 estados de movimentação
    MovementContext.cs          # Dados por frame (posição, velocidade, câmera)
    MovementConfig.cs           # 22 ConfigEntry BepInEx (tunável in-game)
    IMovementState.cs           # Interface dos estados
  Models/
    GameState.cs               # Serialização do estado do jogo
    EventFilter.cs             # Filtros de eventos
```

## State Machine — 13 Estados

| Estado | Trigger | Comportamento |
|--------|---------|--------------|
| Orbit | padrão | órbita polar + wobble Y |
| Lead | jogador andando (speed > 2 u/s) | figura-8 à frente + match velocidade |
| Perch | jogador parado 30s | pousa no ombro direito (+2.2u Y) |
| Stay | MCP tool | para no local, olha pra onde jogador olha |
| GotoCoords | MCP tool | voa até coordenada |
| GotoNamed | MCP tool | voa até local registrado |
| Explore | MCP tool | pontos aleatórios raio 5u |
| Speaking | ShowMessage() | viewport upper-left, asas 4Hz |
| Listening | SkyChat | viewport center-low, acima do chat |
| Thinking | SetAnimation("thinking") | paira, asas 1Hz |
| Greeting | spawn (2s delay) | arco descendente + figura-8 |
| Celebrate | milestone | espiral ascendente 3s |
| Flee | (reservado) | afasta 5u, retorna após 5s |

## Build & Deploy

```bash
# Compilar mod C#
cd B:/_repositorios/sky-tpc-mod/src/SkyTpcMod
dotnet build --configuration Release

# DLL de saída:
# bin/Release/netstandard2.1/SkyTpcMod.dll
# (csproj já copia automaticamente pra BepInEx/plugins/SkyTpcMod/)
```

## Testes

```bash
# Python (skybridge)
cd B:/_repositorios/skybridge
python -m pytest tests/unit/movement/ -v     # 58 testes movement
python -m pytest tests/unit/mcp/ -v          # testes MCP companion
```

## Ciclo de Desenvolvimento

1. **Spec** → OpenSpec (`openspec/changes/sky-companion-movement-strategies/`)
2. **Teste** → Python primeiro (TDD), depois C# sem testes (Unity não permite)
3. **Build** → `dotnet build --configuration Release`
4. **Validação** → reiniciar jogo, testar in-game, reportar problemas
5. **Iterar** → ajustar parâmetros em `MovementConfig.cs` ou lógica nos estados

## Configs BepInEx (ajustáveis in-game)

Arquivo: `BepInEx/config/com.skybridge.tpcmod.cfg`

Principais: OrbitRadius(3), OrbitHeight(2), OrbitSpeed(0.8), PerchDelay(30s), LeadDistance(3), LeadMinSpeed(2), GreetingDuration(3s), MoveSpeed(5), TeleportThreshold(50)

## Personalidade

- **Nome:** Crumpet
- **Tipo:** Cacto comum de poucas palavras
- **Idioma:** SEMPRE português brasileiro
- **Atributos:** PACIÊNCIA alta, SABEDORIA alta, SNARK baixo
- **Evolução:** vira Oesbe (borboleta azul) quando insetos > 0

> "Channel pra ouvir o jogo, MCP pra falar com ele" – made by Sky 🎮
