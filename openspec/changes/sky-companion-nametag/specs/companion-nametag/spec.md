## ADDED Requirements

### Requirement: Name tag persistente via OnGUI/IMGUI
O sistema SHALL exibir um label com o nome do companion usando OnGUI/IMGUI (mesmo frame da mensagem de tela), posicionado via WorldToScreenPoint acima do companion.

#### Scenario: Name tag visível por padrão
- **WHEN** o companion é inicializado e greeting completo
- **THEN** SHALL exibir label com texto configurável (default: "Sky") acima do companion na tela

#### Scenario: Name tag oculto por configuração
- **WHEN** `NametagVisible` config é false
- **THEN** SHALL não desenhar o label

#### Scenario: Name tag sempre visível quando speaking
- **WHEN** o companion está no estado Speaking
- **THEN** SHALL desenhar o name tag independente da configuração NametagVisible

#### Scenario: Name tag oculto quando atrás da câmera
- **WHEN** o companion está atrás da câmera (WorldToScreenPoint.z <= 0)
- **THEN** SHALL não desenhar o label

### Requirement: Gradiente de cores animado por sweep
O label SHALL exibir gradiente de cores animado (azul → índigo → violeta → roxo → lavanda → fúcsia) com sweep temporal por caractere.

#### Scenario: Cores fluem por caractere
- **WHEN** o label está visível
- **THEN** cada caractere SHALL ter cor interpolada do gradiente, com offset avançando com o tempo

#### Scenario: Velocidade do sweep configurável
- **WHEN** `NametagGradientSpeed` é alterado
- **THEN** SHALL ajustar a velocidade de rotação das cores (default: 1.0)

### Requirement: Posição acompanha companion
A posição do label SHALL seguir a posição 3D do companion convertida para coordenadas de tela.

#### Scenario: Label acompanha companion
- **WHEN** o companion se move no mundo
- **THEN** o label SHALL se mover na tela proporcionalmente

#### Scenario: Offset Y configurável
- **WHEN** `NametagOffsetY` > 0 (default: 1.2)
- **THEN** label SHALL aparecer acima do companion no mundo

### Requirement: Parâmetros configuráveis via BepInEx
Todos os parâmetros do name tag SHALL ser configuráveis via BepInEx ConfigEntry.

#### Scenario: ConfigEntries registrados
- **WHEN** o mod carrega
- **THEN** SHALL registrar: NametagText, NametagVisible, NametagOffsetY, NametagFontSize, NametagGradientSpeed

## REMOVED Requirements

### ~~Requirement: TextMeshPro world-space~~
Removido — TMP world-space não apareceu. Renderer.isVisible instável, sem renderer no modelo primitivo, transição de evolução quebra referência. Substituído por OnGUI/IMGUI.

### ~~Requirement: Escala por distância~~
Removido — IMGUI é screen-space, tamanho fixo.

### ~~Requirement: Nome muda com evolução~~
Removido — funcionalidade de evolução será tratada em change separada.

### ~~Requirement: Billboard — sempre olha para câmera~~
Removido — IMGUI é screen-space, não precisa de billboard.

### ~~Requirement: Visibilidade condicional por frustum da câmera~~
Removido — Renderer.isVisible instável. Substituído por screenPos.z > 0 (atrás da câmera).
