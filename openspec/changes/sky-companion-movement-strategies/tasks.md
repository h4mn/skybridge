## 1. Infraestrutura da State Machine

- [ ] 1.1 Criar interface `IMovementState` com GetTargetPosition, GetLookAt, GetWingSpeed, ShouldTransition
- [ ] 1.2 Criar struct `MovementContext` com dados por frame (playerPosition, playerForward, playerVelocity, camera, isPlayerMoving, timeSincePlayerStopped, isSpeaking)
- [ ] 1.3 Criar `MovementStateMachine` com estado atual, cooldown de transição, e métodos Update/TransitionTo
- [ ] 1.4 Registrar parâmetros configuráveis via BepInEx ConfigEntry (orbit_radius, orbit_height, orbit_speed, perch_delay, lead_distance, lead_min_speed, teleport_threshold)

## 2. Estados Básicos (ref: spec movement-state-machine)

- [ ] 2.1 Implementar estado `OrbitState` — coordenadas polares + ondulação Y senoidal, LookAt tangente
- [ ] 2.2 Implementar estado `StayState` — para no local com oscilação Y sutil
- [ ] 2.3 Implementar estado `GotoCoordsState` — voo suave + teleporte se dist > threshold
- [ ] 2.4 Implementar estado `GotoNamedState` — lookup no registro + fallback log warning
- [ ] 2.5 Implementar estado `ThinkingState` — paira no local com asas lentas (1Hz)
- [ ] 2.6 Implementar estado `PerchState` — pousa no ombro, asas dobradas, transição orbit↔perch por tempo parado
- [ ] 2.7 Implementar estado `FleeState` — afasta 5u na direção oposta, retorna após 5s

## 3. Estados Contextuais (ref: spec contextual-flight-behaviors)

- [ ] 3.1 Implementar estado `SpeakingState` — ViewportToWorldPoint(0.15, 0.85), LookAt câmera, asas 4Hz, retorno ao estado anterior
- [ ] 3.2 Implementar estado `LeadState` — posição à frente do jogador, match velocidade + 10%, detecção horizontal only
- [ ] 3.3 Implementar estado `CelebrateState` — espiral ascendente (1.5 voltas, 5u, 3s), LookAt sky, retorno orbit
- [ ] 3.4 Implementar estado `GreetingState` — arco descendente na frente do jogador (2s), transição → orbit
- [ ] 3.5 Implementar estado `ListeningState` — aproxima do jogador (~1.5u), LookAt rosto, timeout 10s
- [ ] 3.6 Implementar estado `ExploreState` — pontos aleatórios raio 5u, limite 8u do jogador

## 4. Integração no CompanionController

- [ ] 4.1 Substituir `DestinationStrategy` por `MovementStateMachine` no CompanionController
- [ ] 4.2 Construir `MovementContext` no Update com dados do frame atual + média móvel de velocidade (5 frames)
- [ ] 4.3 Conectar `ShowMessage()` → transição speaking (salvar estado anterior para retorno)
- [ ] 4.4 Conectar detecção de milestone → transição celebrate
- [ ] 4.5 Conectar SkyChatHandler.OnSendText → transição listening
- [ ] 4.6 Conectar spawn/inicialização → transição greeting

## 5. Retrocompatibilidade MCP

- [ ] 5.1 Mapear `move_companion_to(follow_player)` → estado orbit
- [ ] 5.2 Mapear `move_companion_to(goto_coords)` → estado goto_coords
- [ ] 5.3 Mapear `move_companion_to(goto_named)` → estado goto_named
- [ ] 5.4 Mapear `move_companion_to(stay)` → estado stay
- [ ] 5.5 Adicionar `move_companion_to(explore)` → estado explore

## 6. Testes e Validação

- [ ] 6.1 Testes unitários para MovementStateMachine (transições, prioridade, cooldown)
- [ ] 6.2 Testes unitários para cada estado (posição, lookAt, wingSpeed, shouldTransition)
- [ ] 6.3 Testes unitários para MovementContext (média móvel de velocidade)
- [ ] 6.4 Validação in-game: orbit, lead, speaking, perch
- [ ] 6.5 Validação in-game: celebrate em milestone, greeting no spawn
