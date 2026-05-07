## 1. Models (GameState.cs)

- [x] 1.1 Criar model `CompanionState` com campos: Position[3], State (string), Distance (float), IsVisible (bool), Speed (float)
- [x] 1.2 Criar model `CompanionAroundness` com campos: NearbyResources (string[]), NearbyCreatures (string[]), NearbyBuilds ([]), Biome (string), Altitude (float), NearestLandmark (string), ScanRadius (float)
- [x] 1.3 Adicionar `CompanionState` e `CompanionAroundness` como propriedades nullable em `FullGameState`

## 2. CompanionController — exposição de dados

- [x] 2.1 Adicionar método `GetCompanionState()` no CompanionController que retorna CompanionState populado (Position, State, Distance, IsVisible, Speed)
- [x] 2.2 Adicionar método `GetAroundnessData()` no CompanionController com cache de 3s usando Physics.OverlapSphere
- [x] 2.3 Implementar classificação de objetos: NearbyResources, NearbyCreatures, NearbyBuilds

## 3. GameHooks — integração no GetState

- [x] 3.1 Estender `GameHooks.GetState()` para chamar `_companion.GetCompanionState()` e atribuir ao FullGameState
- [x] 3.2 Estender `GameHooks.GetState()` para chamar `_companion.GetAroundnessData()` e atribuir ao FullGameState
- [x] 3.3 Adicionar null checks para quando companion não existe (retorna null nos campos)

## 4. Build e Validação

- [x] 4.1 Buildar mod com `dotnet build --configuration Release`
- [x] 4.2 Validar GET /state retorna CompanionState e CompanionAroundness no JSON
- [x] 4.3 Validar null quando companion não está spawnado

## 5. Aroundness Completa (NearbyResources, NearbyCreatures, Biome, Altitude, NearestLandmark)

- [x] 5.1 Adicionar campos NearbyResources, NearbyCreatures, Altitude, Biome, NearestLandmark ao model CompanionState
- [x] 5.2 Criar ScanAndClassify() que separa builds (com inventório) de resources (sem inventório) e creatures (por tag)
- [x] 5.3 Implementar DetectBiome() com heurística de altitude + presença de vida
- [x] 5.4 Implementar DetectNearestLandmark() com detecção de spawn e high ground
- [x] 5.5 Atualizar GetCompanionState() para popular todos os campos novos
- [x] 5.6 Buildar mod com `dotnet build --configuration Release` — 0 erros, 0 avisos
- [ ] 5.7 Validar E2E no jogo: GET /state retorna todos os campos com dados reais
