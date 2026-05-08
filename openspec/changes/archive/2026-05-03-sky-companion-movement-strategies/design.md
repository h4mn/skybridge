## Context

O mod SkyTpcMod para Planet Crafter já possui um companion funcional com modelo 3D (borboleta), chat bidirecional, e 6 MCP tools. A movimentação atual usa `DestinationStrategy` — uma classe simples com 4 estratégias fixas (`follow_player`, `goto_coords`, `goto_named`, `stay`) que fazem Lerp direto sem contexto.

O `CompanionController.Update()` chama `_strategy.GetTargetPosition()` e aplica `Vector3.Lerp` + `transform.LookAt(_playerTransform)`. Não há state machine, transições automáticas, ou reação a eventos do jogo.

Referência de design: `src/core/companion/docs/movement-strategies.md` — tabela com 12 estados, prioridades e parâmetros.

## Goals / Non-Goals

**Goals:**
- State machine de movimentação com 13 estados contextuais
- Transições automáticas por prioridade (speaking > celebrate > lead > orbit > perch)
- Movimento **lead** ("punho do Superman") — borboleta voa na frente quando jogador se move
- Movimento **speaking** — borboleta voa para o canto superior esquerdo do viewport
- Movimento **orbit** — padrão com ondulação vertical, face tangente ao círculo
- Movimento **perch** — pousa no ombro quando jogador para > 30s
- Movimentos **celebrate**, **greeting**, **listening**, **explore**, **flee**, **thinking**
- Parâmetros configuráveis via BepInEx ConfigEntry
- Compatibilidade retroativa com MCP tool `move_companion_to`

**Non-Goals:**
- Pathfinding ou navmesh (borboleta voa, não anda)
- Colisão com terreno ou obstáculos
- Animações de modelo 3D além de rotação de asas
- Detecção de construção/interação do jogador (futuro)

## Decisions

### D1: State Machine Pattern com classes por estado

**Escolha:** Cada estado de movimento é uma classe que implementa `IMovementState` com métodos `GetTargetPosition()`, `GetLookAt()`, `GetWingSpeed()`, `ShouldTransition(context)`. `MovementStateMachine` gerencia o estado atual e transições.

**Alternativas consideradas:**
- Enum + switch: rápido mas gera switch monolítico difícil de estender
- ScriptableObject: flexível mas overkill pra Unity sem editor tooling
- Behavior Tree: poderoso mas complexo demais pra 12 estados

**Rationale:** Uma interface por estado é extensível (novo estado = nova classe), testável (mock context), e mantém a responsabilidade isolada. A state machine centraliza prioridade e transição.

### D2: Context compartilhado (MovementContext)

**Escolha:** `MovementContext` struct imutável por frame com: `playerPosition`, `playerForward`, `playerVelocity`, `cameraViewport`, `isPlayerMoving`, `timeSincePlayerStopped`, `isSpeaking`, `currentMessage`, `lastMilestone`.

**Rationale:** Context por frame evita estado mutável compartilhado. Cada estado recebe o contexto e decide se deve transicionar. O `CompanionController.Update()` monta o context uma vez e passa pra state machine.

### D3: Posição speaking via ViewportToWorldPoint

**Escolha:** `Camera.main.ViewportToWorldPoint(new Vector3(0.15f, 0.85f, distância))` para posicionar a borboleta no canto superior esquerdo da tela durante `ShowMessage()`.

**Alternativas consideradas:**
- ScreenToWorldPoint: mesma coisa mas coordenadas em pixels
- Posição fixa world-space: não funciona com rotação de câmera
- Overlay UI: já temos o overlay, a borboleta é world-space

**Rationale:** ViewportToWorldPoint funciona independentemente de resolução e rotação de câmera. O offset (0.15, 0.85) posiciona no canto superior esquerdo sem cobrir o texto.

### D4: Detecção de velocidade do jogador para lead

**Escolha:** Calcular velocidade do jogador como `Vector3.Distance(posAtual, posAnterior) / Time.deltaTime`. Se > `lead_min_speed` (default 2 u/s) por mais de 0.5s, transicionar para lead.

**Rationale:** Sem access direto ao CharacterController do jogador (API não exposta), medimos velocidade por diferença de posição. O delay de 0.5s evita flickering ao andar devagar.

### D5: Orbit com coordenadas polares + lookAt câmera

**Escolha:** Posição orbit calculada como `center + polar(angle + time * speed) * radius + Vector3.up * (height + sin(time * wobbleFreq) * wobble)`. O ângulo avança com `time * orbit_speed`. LookAt aponta para a câmera do jogador (compatível com 1a/3a pessoa). Ao retornar de outro estado, o ângulo da órbita é sincronizado com a posição atual do companion (SyncOrbitAngle) para evitar jump visual.

**Rationale:** Coordenadas polares são naturais para órbita. O seno no Y dá ondulação. LookAt para câmera garante que a borboleta sempre enfrente o jogador, independente da perspectiva (1a/3a pessoa). SyncOrbitAngle elimina teleportes visuais ao transicionar de volta para orbit.

## Arquitetura

```
CompanionController.Update()
    │
    ▼
MovementContext.Build(player, camera, gameState)
    │
    ▼
MovementStateMachine.Update(context)
    │
    ├── currentState.ShouldTransition(context)?
    │       │ YES → TransitionTo(highestPriority)
    │       │ NO  → stay
    │
    ▼
currentState.GetTargetPosition(context) → Vector3?
    │
    ▼
Apply movement (Lerp / Teleport)
Apply LookAt
Apply WingSpeed
```

## Prioridade de Transição

```
speaking > celebrate > listening > lead > flee > goto/stay > perch > explore > orbit > thinking
```

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| ViewportToWorldPoint varia com FOV/resolução | Offset configurável, calibrar empiricamente |
| Cálculo de velocidade por posição pode ter jitter | Suavizar com média móvel de 5 frames |
| Transições rápidas podem causar flickering | Cooldown mínimo de 0.3s entre transições |
| 12 estados pode parecer over-engineering | Estados são classes simples (~30 linhas cada) — são 13 estados |
| Lead pode conflitar com jetpack vertical | Lead só ativa no eixo horizontal, ignora Y |
| Performance: 12 classes de estado por frame | Sem alocação, context é struct, lookup por enum |

## Open Questions

- **Calibração do orbit**: Raio, velocidade e wobble precisam ser calibrados no jogo
- **Perch offset**: Posição exata no ombro depende do modelo do jogador (não controlamos)
- **Explore trigger**: O que define "jogador construindo/interagindo"? Por ora, explore só ativa via MCP tool
