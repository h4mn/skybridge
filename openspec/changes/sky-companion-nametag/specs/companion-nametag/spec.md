## ADDED Requirements

### Requirement: Name tag persistente acima do modelo
O sistema SHALL exibir um label TextMeshPro 3D com o nome do companion posicionado acima ou abaixo do modelo, visível em world-space.

#### Scenario: Name tag visível por padrão
- **WHEN** o companion é inicializado
- **THEN** SHALL exibir label com texto configurável (default: "Sky") acima do modelo

#### Scenario: Name tag oculto por configuração
- **WHEN** `NametagVisible` config é false
- **THEN** SHALL ocultar o label completamente

#### Scenario: Name tag sempre visível quando speaking
- **WHEN** o companion está no estado Speaking
- **THEN** SHALL exibir o name tag independente da configuração NametagVisible

### Requirement: Gradiente de cores animado por sweep
O label SHALL exibir gradiente de cores animado (azul → índigo → violeta → roxo → lavanda → fúcsia) com sweep temporal por caractere.

#### Scenario: Cores fluem por caractere
- **WHEN** o label está visível
- **THEN** cada caractere SHALL ter cor interpolada do gradiente, com offset avançando com o tempo

#### Scenario: Velocidade do sweep configurável
- **WHEN** `NametagGradientSpeed` é alterado
- **THEN** SHALL ajustar a velocidade de rotação das cores (default: 1.0)

### Requirement: Billboard — sempre olha para câmera
O label SHALL sempre mirar para a câmera ativa (compatível com 1a e 3a pessoa).

#### Scenario: Rotação acompanha câmera
- **WHEN** a câmera rotaciona
- **THEN** o label SHALL rotacionar para permanecer legível de qualquer ângulo

### Requirement: Escala por distância
O label SHALL escalar inversamente proporcional à distância da câmera para manter tamanho aparente constante.

#### Scenario: Tamanho constante a qualquer distância
- **WHEN** a câmera se aproxima ou se afasta
- **THEN** o label SHALL manter tamanho visual aproximadamente constante (clamp entre min e max)

### Requirement: Posição configurável acima/abaixo
A posição do label SHALL ser configurável via `NametagOffsetY` (positivo = acima, negativo = abaixo).

#### Scenario: Offset positivo posiciona acima
- **WHEN** `NametagOffsetY` > 0 (default: 0.8)
- **THEN** label SHALL aparecer acima do modelo

#### Scenario: Offset negativo posiciona abaixo
- **WHEN** `NametagOffsetY` < 0
- **THEN** label SHALL aparecer abaixo do modelo

### Requirement: Nome muda com evolução
O nome exibido SHALL mudar automaticamente quando o companion evolui para Oesbe.

#### Scenario: Evolução muda nome
- **WHEN** insects > 0 e companion evolui
- **THEN** nome SHALL mudar de "Sky" para "Sky Oesbe"

#### Scenario: Nome customizado mantém evolução
- **WHEN** nome configurado como "Buddy" e companion evolui
- **THEN** nome SHALL mudar para "Buddy Oesbe"

### Requirement: Parâmetros configuráveis via BepInEx
Todos os parâmetros do name tag SHALL ser configuráveis via BepInEx ConfigEntry.

#### Scenario: ConfigEntries registrados
- **WHEN** o mod carrega
- **THEN** SHALL registrar: NametagText, NametagVisible, NametagOffsetY, NametagFontSize, NametagGradientSpeed, NametagMinScale, NametagMaxScale
