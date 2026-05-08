# Companion — Sky como Companheira de Jogos

## Visão Geral

Bounded Context que transforma a Sky em companheira de jogos, recebendo estado do jogo em tempo real e enviando comandos.

## Arquitetura: Channel + MCP

```
  GAME STATE (in)                    COMMANDS (out)
┌─────────────────┐              ┌─────────────────┐
│  Channel MCP    │              │   MCP Tools     │
│  (notificações) │              │   (ações)       │
│                 │              │                 │
│  jogo publica ──┼──► Sky ────┼──► comando ────►│ jogo
│  estado         │    recebe   │    decide e     │ executa
│                 │    contexto │    envia        │
└─────────────────┘              └─────────────────┘
```

### Channel MCP (entrada — game state)
- O jogo/servidor publica mudanças de estado via Channel MCP
- Sky recebe notificações em tempo real: posição, vida, inventário, eventos
- Channels usam o protocolo de notificações do Claude Code (sem polling)

### MCP Tools (saída — comandos)
- Sky envia comandos ao jogo via MCP tools
- Ações: mover, craftar, construir, chat, seguir jogador
- Cada adapter define suas tools específicas

## Estrutura

```
src/core/companion/
├── docs/
│   ├── README.md              # este arquivo
│   └── mcp-jogavel/
│       └── proposta.md        # proposta original (Minecraft)
├── core/                      # lógica game-agnostic
│   ├── companion.py           # CompanionState, GameEvent
│   └── session.py             # ciclo de vida da sessão
├── adapters/                  # um adapter por jogo
│   ├── _base.py               # CompanionAdapter (interface abstrata)
│   ├── minecraft/             # Minecraft via Mineflayer
│   └── planet-craft/          # Planet Craft via Channel + MCP
└── __init__.py
```

## Adapters

| Adapter | State IN | Commands OUT | Status |
|---------|----------|-------------|--------|
| Minecraft | Channel MCP + Mineflayer | MCP Tools (Mineflayer) | Proposta |
| Planet Craft | Channel MCP | MCP Tools | Proposta |

## Interface do Adapter

Todo adapter implementa `CompanionAdapter`:

- `connect()` — conecta ao jogo
- `get_context()` — snapshot do estado atual (GameContext)
- `send_message(text)` — envia mensagem/chat
- `execute_action(action, **params)` — executa ação no jogo
- `disconnect()` — desconecta graciosamente

## Jogos Suportados

### Minecraft
- Plugin Skycraft (`B:/_repositorios/skycraft/`) no servidor PaperMC 1.21.1
- Integração via Mineflayer (Node.js) ou plugin direto
- Já tem chat handler, histórico e TTS

### Planet Craft
- Jogo mobile/PC tipo Minecraft
- Adapter via Channel MCP para receber estado
- MCP tools para enviar comandos

## Referências

- Proposta original: `docs/mcp-jogavel/proposta.md`
- Plugin Skycraft: `B:/_repositorios/skycraft/`
- Claude Code Channels: MCP servers com notificações em tempo real

> "Channel pra ouvir o jogo, MCP pra falar com ele" – made by Sky 🎮
