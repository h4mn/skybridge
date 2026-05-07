## ADDED Requirements

### Requirement: aroundness dentro de Companion no GET /state
O `GET /state` SHALL retornar campos de percepção ambiental dentro do objeto `Companion`. Se o companion não existir, o campo `Companion` SHALL ser null (sem aroundness separado).

#### Scenario: Companion ativo retorna aroundness
- **WHEN** `GET /state` é chamado e o companion está spawnado
- **THEN** response inclui `Companion` com campos de aroundness: NearbyBuilds, NearbyResources, NearbyCreatures, ScanRadius, Altitude, Biome, NearestLandmark

#### Scenario: Companion não existe retorna null
- **WHEN** `GET /state` é chamado e o companion não foi spawnado
- **THEN** `Companion` é null

### Requirement: CompanionAroundness model (campos dentro de Companion)
O objeto `Companion` SHALL conter campos de aroundness:
- `NearbyBuilds`: array — construções do jogador dentro do ScanRadius (cada item com id, name, position, relatedItems)
- `NearbyResources`: string[] — nomes dos recursos naturais dentro do ScanRadius
- `NearbyCreatures`: string[] — nomes das criaturas dentro do ScanRadius
- `ScanRadius`: float — raio do scan em unidades Unity (default: 20.0)
- `Altitude`: float — altura Y do companion
- `Biome`: string — bioma inferido (altitude + presença de vida)
- `NearestLandmark`: string — landmark mais próximo (ou "None")

#### Scenario: Dados populados corretamente
- **WHEN** companion está próximo a construções e recursos, altitude 35.0, com insetos ativos
- **THEN** Companion.NearbyBuilds = [{Id: "...", Name: "Armário de Armazenamento", ...}], Companion.NearbyResources = ["Semente de Shanga"], Companion.NearbyCreatures = [], Companion.Altitude = 35.0, Companion.Biome = "Valley", Companion.NearestLandmark = "None", Companion.ScanRadius = 20.0

### Requirement: Scan ambiental via OverlapSphere com cache
O scan ambiental SHALL usar `Physics.OverlapSphere` a cada 3 segundos com cache interno. O `GetState()` retorna dados do cache.

#### Scenario: Cache evita scan a cada request
- **WHEN** `GET /state` é chamado 2 vezes em 1 segundo
- **THEN** apenas 1 OverlapSphere é executado, segunda request usa cache

#### Scenario: Cache expira após 3 segundos
- **WHEN** se passam 3+ segundos desde último scan
- **THEN** próximo `GetState()` dispara novo OverlapSphere

### Requirement: Classificação de objetos por tipo
Objetos detectados pelo scan SHALL ser classificados em:
- **NearbyResources**: WorldObjects com grupo de tipo recurso
- **NearbyCreatures**: GameObjects com tag/layer de criatura
- **NearbyBuilds**: GameObjects com tag/layer de construção do jogador

#### Scenario: Objeto desconhecido é ignorado
- **WHEN** OverlapSphere detecta objeto que não é recurso, criatura nem construção
- **THEN** objeto não aparece em nenhuma lista
