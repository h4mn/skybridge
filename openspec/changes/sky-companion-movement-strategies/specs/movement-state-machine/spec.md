## ADDED Requirements

### Requirement: State machine gerencia transições de movimento
O sistema SHALL manter uma state machine que controla o estado de movimento atual do companion. Apenas UM estado SHALL estar ativo por vez.

#### Scenario: Transição automática por prioridade
- **WHEN** múltiplas transições são possíveis simultaneamente
- **THEN** a state machine SHALL selecionar a transição de maior prioridade (speaking > celebrate > listening > lead > flee > goto/stay > perch > explore > orbit)

#### Scenario: Cooldown entre transições
- **WHEN** uma transição ocorre
- **THEN** nenhuma outra transição automática SHALL ocorrer por 0.3 segundos (cooldown configurável)

### Requirement: MovementContext fornecido a cada frame
O sistema SHALL construir um `MovementContext` imutável a cada frame contendo: playerPosition, playerForward, playerVelocity, cameraViewport, isPlayerMoving, timeSincePlayerStopped, isSpeaking, currentMessage.

#### Scenario: Context reflete estado atual do jogo
- **WHEN** o Update roda
- **THEN** MovementContext SHALL conter dados frescos do frame atual (posição, velocidade, câmera)

#### Scenario: Velocidade suavizada
- **WHEN** a velocidade do jogador é calculada
- **THEN** SHALL usar média móvel dos últimos 5 frames para evitar jitter

### Requirement: Interface IMovementState
Cada estado de movimento SHALL implementar a interface `IMovementState` com métodos: `GetTargetPosition(context)`, `GetLookAt(context)`, `GetWingSpeed(context)`, `ShouldTransition(context)`.

#### Scenario: Novo estado adicionado
- **WHEN** um novo estado implementa IMovementState
- **THEN** SHALL ser integrável sem modificar estados existentes

### Requirement: Orbit como estado padrão
O estado **orbit** SHALL ser o estado padrão (idle). A borboleta SHALL circular horizontalmente ao redor do jogador com ondulação vertical senoidal.

#### Scenario: Orbit ativo quando jogador está parado
- **WHEN** jogador está parado e sem eventos
- **THEN** companion SHALL orbitar com raio 3u, altura 2u, ondulação Y ±0.5u

#### Scenario: LookAt tangente ao círculo
- **WHEN** em orbit
- **THEN** companion SHALL olhar na direção do voo (tangente ao círculo), NÃO diretamente para o jogador

### Requirement: Stay para no local atual
O estado **stay** SHALL parar o companion no local atual com oscilação Y sutil.

#### Scenario: Stay via MCP tool
- **WHEN** `move_companion_to(strategy="stay")` é chamado
- **THEN** companion SHALL parar no local atual mantendo oscilação Y ±0.1u

### Requirement: Goto_coords voa para coordenada
O estado **goto_coords** SHALL mover o companion para coordenada (x, y, z) específica.

#### Scenario: Teleporte quando distância > 50u
- **WHEN** distância até o destino > teleport_threshold
- **THEN** companion SHALL teleportar instantaneamente

#### Scenario: Voo suave quando distância < 50u
- **WHEN** distância até o destino ≤ teleport_threshold
- **THEN** companion SHALL voar suavemente em direção ao destino

### Requirement: Goto_named voa para local nomeado
O estado **goto_named** SHALL buscar o local no registro de nomes e voar até ele.

#### Scenario: Nome encontrado no registro
- **WHEN** `move_companion_to(strategy="goto_named", name="base")` é chamado e "base" existe no registro
- **THEN** companion SHALL voar para as coordenadas registradas

#### Scenario: Nome não encontrado
- **WHEN** o nome não existe no registro
- **THEN** companion SHALL permanecer no estado atual e registrar warning no log

### Requirement: Perch pousa no ombro do jogador
O estado **perch** SHALL pousar o companion no ombro direito do jogador quando parado por mais de 30s.

#### Scenario: Transição orbit → perch
- **WHEN** jogador está parado por mais de `perch_delay` segundos (default 30s)
- **THEN** companion SHALL mover suavemente para o ombro direito do jogador

#### Scenario: Transição perch → orbit
- **WHEN** jogador se move enquanto companion está perched
- **THEN** companion SHALL retornar ao estado orbit

#### Scenario: Asas dobradas no perch
- **WHEN** em perch
- **THEN** asas SHALL estar paradas (wing speed 0)

### Requirement: Thinking paira no local
O estado **thinking** SHALL manter o companion pairando no local atual com oscilação Y sutil e asas lentas.

#### Scenario: Thinking via MCP tool
- **WHEN** `set_companion_animation("thinking")` é chamado
- **THEN** companion SHALL parar no local atual com asas a 1Hz e oscilação Y ±0.1u

### Requirement: Flee afasta de perigo
O estado **flee** SHALL afastar o companion rapidamente do ponto de perigo.

#### Scenario: Flee ao detectar perigo (futuro)
- **WHEN** evento de perigo detectado (morte do jogador)
- **THEN** companion SHALL voar 5u na direção oposta ao perigo com asas a 4Hz

#### Scenario: Retorno após flee
- **WHEN** 5 segundos após evento de perigo
- **THEN** companion SHALL retornar ao estado orbit

### Requirement: Parâmetros configuráveis via BepInEx
Todos os parâmetros de movimentação SHALL ser configuráveis via BepInEx ConfigEntry.

#### Scenario: Parâmetros acessíveis no config
- **WHEN** o mod carrega
- **THEN** SHALL registrar ConfigEntries para: orbit_radius, orbit_height, orbit_speed, orbit_wobble, perch_delay, speaking_duration, lead_distance, lead_min_speed, teleport_threshold

### Requirement: Retrocompatibilidade com MCP tool move_companion_to
O MCP tool `move_companion_to` SHALL continuar funcionando com as estratégias existentes (follow_player, goto_coords, goto_named, stay).

#### Scenario: follow_player mapeia para orbit
- **WHEN** `move_companion_to(strategy="follow_player")` é chamado
- **THEN** SHALL transicionar para estado orbit (não lead — follow é seguir, lead é ir na frente)

#### Scenario: goto_coords mapeia para estado goto_coords
- **WHEN** `move_companion_to(strategy="goto_coords", x, y, z)` é chamado
- **THEN** SHALL transicionar para estado goto_coords com as coordenadas fornecidas
