## Why

O companion não tem identificação visual — o jogador não sabe o nome da borboleta. Um name tag persistente com a identidade visual da Sky (gradiente azul→violeta→fúcsia animado) reforça a presença do companion e dá personalidade ao mod.

## What Changes

- Name tag usando mesmo frame TextMeshPro do balão de mensagem (padrão já funcional)
- Gradiente de cores dinâmico (azul → índigo → violeta → roxo → lavanda → fúcsia) animado por sweep temporal
- Label acompanha posição do modelo 3D como child — sem billboard manual
- Visibilidade condicional: só renderiza quando modelo 3D está no frustum da câmera
- Visibilidade configurável via BepInEx (sempre visível se flag=true)
- Nome configurável via BepInEx (default: "Sky")

## Capabilities

### New Capabilities
- `companion-nametag`: Name tag com gradiente animado, visibilidade por frustum, e configurações BepInEx

### Modified Capabilities
- `companion-nametag` (revisão): Remove escala por distância, remove billboard manual, remove mudança de nome na evolução

## Impact

- **Arquivos C#**: `CompanionController.cs` (simplificar UpdateNametag — remover LookAt/scale), `MovementConfig.cs` (remover NametagMinScale/NametagMaxScale)
- **Dependências**: TextMeshPro (já presente no projeto)
- **Referência visual**: `statusline.py` (gradiente SKY_GRADIENT), balão de mensagem existente (padrão TMP)
