## Context

O mod sky-tpc-mod já expõe `GET /state` via HttpServer.cs retornando `FullGameState` com Terraform, Player, Inventory e RecentEvents. O CompanionController mantém dados internos (posição, estado da state machine, velocidade) que não são expostos. Não existe nenhum mecanismo de scan ambiental.

## Goals / Non-Goals

**Goals:**
- Expor dados internos do companion como campo `Companion` no `GET /state`
- Criar mecanismo de scan ambiental completo (NearbyBuilds, NearbyResources, NearbyCreatures, Biome, Altitude, NearestLandmark, ScanRadius) dentro do objeto `Companion`
- Manter compatibilidade (não-breaking) com clientes existentes

**Non-Goals:**
- Não modificar o MCP server Python (apenas consumir os novos dados no futuro)
- Não criar nova rota HTTP — os campos são adicionais no `GET /state` existente
- Não implementar persistência dos state-types

## Decisions

### 1. Companion como campo único do FullGameState

**Escolha:** Adicionar `Companion` como propriedade de `FullGameState`, contendo tanto state quanto aroundness.

**Alternativas:**
- Rota separada `GET /companion-state` → rejeitado: mais complexidade HTTP, mais roundtrips
- Array genérico de state-types → rejeitado: perde tipagem forte, mais parsing no MCP
- Dois campos separados (CompanionState + CompanionAroundness) → rejeitado na implementação: dados ficaram num único objeto

**Razão:** FullGameState já é o contrato consolidado. Objeto único é mais simples e já está implementado.

### 2. Scan ambiental via Physics.OverlapSphere com cache

**Escolha:** `CompanionAroundness` faz scan via `Physics.OverlapSphere` a cada 3 segundos com cache interno. Retorna dados do cache no `GetState()`.

**Alternativas:**
- Scan síncrono a cada GET /state → rejeitado: custo alto se poll for frequente
- Raycast em múltiplas direções → rejeitado: não detecta objetos atrás/ao lado
- Hook em eventos do jogo → rejeitado: Planet Crafter não tem API de eventos de spawn/despawn de objetos

**Razão:** OverlapSphere com cache é simples, cobre 360°, e o custo é controlado pelo intervalo.

### 3. Classificação de objetos por inventório e tags

**Escolha:** Classificar objetos detectados pelo scan:
- **NearbyBuilds**: WorldObjects com inventório vinculado (linkedInventoryId > 0)
- **NearbyResources**: WorldObjects sem inventório vinculado (recursos naturais: minérios, plantas)
- **NearbyCreatures**: GameObjects sem WorldObjectAssociated mas com tag Creature/Insect/Animal

**Razão:** Planet Crafter não expõe GroupType diretamente. Inventório vinculado é o melhor discriminante entre builds e resources. Criaturas são entidades separadas do sistema WorldObject.

### 4. CompanionState populado do CompanionController

**Escolha:** CompanionController expõe método `GetCompanionState()` que retorna dados internos. GameHooks chama no `GetState()`.

**Razão:** Encapsulamento — CompanionController é dono dos dados. GameHooks apenas orquestra.

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| OverlapSphere custo por frame | Cache de 3s, scan em thread background |
| Tags/layers do Planet Crafter podem mudar com updates | Logging claro, fallback para "unknown" |
| FullGameState response cresce | Campos nullable — se companion não existe, retorna null |
| Dados do CompanionController podem não estar disponíveis no momento do GetState | Null checks, retorna estado parcial |

> "Dois state-types, um response, zero breaking changes" – made by Sky 🔧
