## Why

O companion não tem identificação visual — o jogador não sabe o nome da borboleta. Um name tag persistente com a identidade visual da Sky (gradiente azul→violeta→fúcsia animado) reforça a presença do companion e dá personalidade ao mod.

## What Changes

- Adicionar label TextMeshPro 3D acima/abaixo do modelo do companion
- Gradiente de cores dinâmico (azul → índigo → violeta → roxo → lavanda → fúcsia) animado por sweep temporal
- Escala por distância para manter tamanho aparente constante (billboard)
- Posição configurável (acima/abaixo do modelo)
- Visibilidade configurável via BepInEx (sempre visível se flag=true)
- Nome configurável via BepInEx (default: "Sky")
- Nome muda automaticamente para "Sky Oesbe" quando evolui

## Capabilities

### New Capabilities
- `companion-nametag`: Name tag 3D com gradiente animado, billboard, escala por distância, e configurações BepInEx

### Modified Capabilities

## Impact

- **Arquivos C#**: `CompanionController.cs` (criação do label, Update para billboard/gradiente), `MovementConfig.cs` (novos ConfigEntries)
- **Dependências**: TextMeshPro (já presente no projeto)
- **Referência visual**: `statusline.py` (gradiente SKY_GRADIENT), `welcome.py` (paletas _PALETAS com sweep animado)
