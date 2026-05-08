## ADDED Requirements

### Requirement: Companion no GET /state
O `GET /state` SHALL retornar um campo `Companion` com dados internos do companion. Se o companion não existir, o campo SHALL ser null.

#### Scenario: Companion ativo retorna state completo
- **WHEN** `GET /state` é chamado e o companion está spawnado
- **THEN** response inclui `Companion` com Position[3], State (string do enum), Distance (float), IsVisible (bool), Speed (float)

#### Scenario: Companion não existe retorna null
- **WHEN** `GET /state` é chamado e o companion não foi spawnado
- **THEN** `CompanionState` é null

### Requirement: CompanionState model
O model `CompanionState` SHALL conter:
- `Position`: float[3] — posição world do companion
- `State`: string — nome do estado atual da MovementStateMachine (ex: "Orbit", "Lead", "Perch")
- `Distance`: float — distância ao jogador em unidades Unity
- `IsVisible`: bool — se o modelo 3D está visível
- `Speed`: float — velocidade atual do companion em u/s

#### Scenario: Campos populados corretamente
- **WHEN** companion está em estado "Lead" a 3.5u do jogador, velocidade 2.0u/s, modelo visível
- **THEN** Companion = { Position: [x,y,z], State: "Lead", Distance: 3.5, IsVisible: true, Speed: 2.0 }

### Requirement: CompanionController expõe GetCompanionState
O `CompanionController` SHALL fornecer método `GetCompanionState()` que retorna `CompanionState` populado com dados internos atuais.

#### Scenario: GetCompanionState chamado pelo GameHooks
- **WHEN** `GameHooks.GetState()` é chamado
- **THEN** invoca `_companion.GetCompanionState()` e atribui ao `FullGameState.Companion`
