## Why

O companion atual tem movimentação básica — `follow_player` faz Lerp direto sem personalidade. A borboleta fica de costas para o jogador, gira sem critério e não reage ao contexto. Uma borboleta real tem voo errático, orbital e expressivo. O modelo 3D já funciona (prefab Butterfly_LOD1), mas a movimentação não faz jus à identidade visual.

## What Changes

- Substituir `DestinationStrategy` simples por uma **state machine de movimentação** com 12 estados contextuais
- Cada estado define: posição, lookAt, velocidade, animação de asas, e transições automáticas
- Novos movimentos: **orbit** (padrão), **lead** (Superman), **speaking** (avatar do overlay), **perch** (pousa no ombro), **celebrate** (espiral em milestone), **greeting** (spawn), **explore** (vagueia), **flee** (perigo)
- Movimentos existentes (`goto_coords`, `goto_named`, `stay`) continuam funcionando como comandos MCP
- Detecção automática de velocidade do jogador para transição **orbit** ↔ **lead**
- Detecção de parada para transição **orbit** → **perch**

## Capabilities

### New Capabilities

- `movement-state-machine`: State machine com 12 estados de movimentação, transições automáticas por prioridade, parâmetros configuráveis via BepInEx ConfigEntry
- `contextual-flight-behaviors`: Comportamentos reativos: lead (velocidade jogador), speaking (viewport position), celebrate (milestone), greeting (spawn), listening (chat input)

### Modified Capabilities

## Impact

- **Mod C#**: `DestinationStrategy.cs` substituído por `MovementStateMachine.cs` + estados individuais
- **Mod C#**: `CompanionController.cs` — Update loop usa state machine ao invés de strategy direta
- **Mod C#**: `GameHooks.cs` — novos eventos: `player_speed_changed`, `player_stopped`
- **MCP Tool**: `move_companion_to` continua compatível (mapeia estratégias para estados)
- **Docs**: `src/core/companion/docs/movement-strategies.md` já existe como referência
