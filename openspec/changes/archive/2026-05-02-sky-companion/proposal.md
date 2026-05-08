## Why

A Sky atualmente é uma assistente de desenvolvimento que vive no terminal. O Sky Companion traz a Sky para dentro dos jogos como uma **companheira interativa** — com modelo 3D, animações, chat in-game e capacidade de reagir ao estado do mundo em tempo real. O primeiro jogo suportado é The Planet Crafter, via BepInEx mod.

Isso resolve: (a) a desconexão entre jogar e ter assistência IA, (b) a necessidade de alt-tab pra consultar informações, e (c) a falta de uma presença afetiva da Sky durante a jogatina.

## What Changes

- **BepInEx Mod (C#)** — `sky-tpc-mod/`
  - Expõe estado do jogo via API REST (`localhost:17234`): terraform, inventário, posição, eventos
  - Adiciona modelo 3D da Sky no mundo do jogo com animações (idle, thinking, speaking)
  - Permite que o modelo 3D seja controlado por comandos externos via HTTP
  - Adiciona comando in-game `/skychat` para o jogador conversar com a Sky e receber resposta em tempo real

- **MCP Channel (Python)** — `src/core/companion/adapters/planet-craft/channel.py`
  - Faz polling do estado do jogo e envia notificações em tempo real para o Claude Code via `notifications/claude/channel`
  - Detecta mudanças de estado (terraform level up, evento, construção) e empurra como eventos

- **MCP Tools (Python)** — expostas no mesmo servidor MCP
  - `send_companion_message(text)` — exibe mensagem falada pela Sky no jogo
  - `move_companion_to(DestinationStrategy)` — move a Sky segundo uma estratégia: seguir jogador, ir para coordenada, ir para local nomeado, ou ficar parada
  - `set_companion_animation(animation)` — muda animação (idle, thinking, speaking)
  - `get_game_state()` — retorna estado atual do jogo para Claude Code tomar decisões

- **Adapter Python** — `src/core/companion/adapters/planet-craft/`
  - Implementa `CompanionAdapter` (interface já definida em `_base.py`)
  - Conecta ao mod via HTTP para ler estado e enviar comandos

## Capabilities

### New Capabilities
- `game-state-provider`: Coleta e exposição de estado do jogo via API REST (terraform, posição, inventário, eventos)
- `companion-3d-model`: Modelo 3D da Sky no mundo do jogo com animações controláveis externamente
- `companion-chat`: Comando `/skychat` in-game para conversação direta com a Sky
- `channel-mcp-companion`: Channel MCP que empurra eventos do jogo para Claude Code em tempo real
- `companion-tools`: MCP Tools para Claude Code enviar comandos ao jogo (mensagem, movimento, animação)
- `companion-session`: Gerenciamento de sessão de jogatina (eventos, notas, duração, resumo)

### Modified Capabilities
<!-- Nenhuma spec existente precisa ser modificada -->

## Impact

- **Novos repositórios**: `sky-tpc-mod/` (C# BepInEx plugin) — já criado com scaffold inicial
- **Novo bounded context**: `src/core/companion/` — já criado com estrutura de adapters
- **Dependências**: BepInEx 5, HarmonyX, Newtonsoft.Json (já no jogo), mcp Python SDK
- **Games suportados**: The Planet Crafter (inicial), Minecraft (futuro via Skycraft)
- **Configuração**: Nova entrada em `.mcp.json` para o channel + tools do companion
- **Assets**: Modelo 3D da Sky (formato Unity AssetBundle ou prefab) — precisa ser criado ou adaptado
