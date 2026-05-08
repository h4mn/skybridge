## Why

O `GET /state` do mod retorna apenas dados do mundo (terraform, player, inventário, eventos). O companion não tem visibilidade própria — não sabemos onde está, qual estado de movimentação, nem o que existe ao redor dele. Isso limita a capacidade do MCP de dar respostas contextuais baseadas no ambiente do companion.

## What Changes

- Adicionar campo **Companion** no `GET /state`: dados internos do companion (posição, estado de movimentação, velocidade, visibilidade, distância ao jogador) + percepção ambiental (NearbyBuilds, NearbyResources, NearbyCreatures, ScanRadius, Altitude, Biome, NearestLandmark)
- Estender `FullGameState` com o campo `Companion` na resposta do `GET /state`
- Criar models em `GameState.cs`
- Estender `GameHooks.GetState()` para popular o novo campo

## Capabilities

### New Capabilities
- `Companion`: Objeto com dados internos (Position, State, Distance, IsVisible, Speed) + aroundness (NearbyBuilds, NearbyResources, NearbyCreatures, ScanRadius, Altitude, Biome, NearestLandmark)

### Modified Capabilities

## Impact

- **C# (sky-tpc-mod)**: `GameState.cs` (models), `GameHooks.cs` (extensão do GetState), `CompanionController.cs` (expor dados internos)
- **API**: `GET /state` response cresce com 1 nova seção — **não-breaking** (campo novo)
- **MCP (skybridge)**: `planet_crafter_companion.py` consome os dados para respostas mais contextuais
- **Performance**: Scan periódico com cache de 3s controla o custo do OverlapSphere
