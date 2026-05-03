## Context

O companion já possui modelo 3D (borboleta), state machine de movimentação com 13 estados, e balão de mensagens com TextMeshPro. Falta um identificador visual persistente — um name tag que flutua acima do modelo com o nome da borboleta e a identidade visual da Sky.

Referência de identidade visual:
- **Statusline** (`statusline.py`): gradiente SKY_GRADIENT com 6 cores animadas por offset temporal (azul #3B82F6 → índigo #6366F1 → violeta #8B5CF6 → roxo #A855F7 → lavanda #C084FC → fúcsia #D946EF)
- **Welcome logo** (`welcome.py`): paletas por emoção com sweep animado e interpolação entre estados

## Goals / Non-Goals

**Goals:**
- Label 3D com nome do companion usando TextMeshPro
- Gradiente de cores animado (azul→violeta→fúcsia) por sweep temporal
- Billboard: sempre olha para a câmera
- Escala por distância: tamanho aparente constante independente da distância
- Posição configurável: acima ou abaixo do modelo
- Visibilidade configurável via BepInEx
- Nome configurável via BepInEx (default: "Sky")
- Nome muda automaticamente na evolução ("Sky" → "Sky Oesbe")

**Non-Goals:**
- Sombras ou efeitos de iluminação no label
- Outline/borda no texto
- Interatividade (clique no nome)
- Fonte customizada (usa default do TextMeshPro)

## Decisions

### D1: TextMeshPro world-space com billboard manual

**Escolha:** Criar TextMeshPro em world-space como child do companion. No Update, rotacionar para olhar a câmera (`transform.LookAt(camera)`) e inverter escala com distância.

**Alternativas:**
- Canvas Screen Space: ficaria fixo na tela, não world-space
- Canvas World Space: mais flexível mas mais pesado que TMP direto
- Overlay IMGUI: já existe pra mensagens, não serve pra label 3D

**Rationale:** TMP world-space com billboard manual é leve, já usamos TMP no projeto, e funciona em 1a/3a pessoa.

### D2: Gradiente por sweep temporal (offset + Lerp entre cores)

**Escolha:** Array de 6 cores (SKY_GRADIENT). Offset avança com `Time.time * velocidade`. Cada caractere recebe cor = Lerp(cores[offset % 6], cores[(offset+1) % 6], fração). No Update, aplicar cor por caractere via `textMesh.textInfo.meshInfo`.

**Alternativas:**
- Vertex gradient do TMP: só 2 cantos, não dá sweep por caractere
- Material property: não controla por caractere
- Color tag rich text: `[color]` inline, simples mas sem animação smooth

**Rationale:** Sweep por caractere com Lerp dá o mesmo efeito do statusline — cada letra tem uma cor diferente que flui. O meshInfo do TMP permite alterar cores sem recriar o texto.

### D3: Escala por distância (1/distance)

**Escolha:** `scale = baseSize / Mathf.Clamp(distance, minDist, maxDist)`. Distance = distância câmera→label. Base size configurável.

**Rationale:** Inversamente proporcional à distância mantém tamanho aparente constante. Clamp evita escala infinita (muito perto) ou invisível (muito longe).

### D4: ConfigEntry para todos os parâmetros

**Escolha:** BepInEx ConfigEntry para: NametagText, NametagVisible, NametagOffsetY (positivo=acima, negativo=abaixo), NametagFontSize, NametagGradientSpeed, NametagMinScale, NametagMaxScale.

**Rationale:** Hot-reload pelo config do BepInEx sem rebuild.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Sweep por caractere pode causar GC allocation | Usar `meshInfo.colors32` direto, não recriar arrays |
| Escala por distância pode conflitar com FOV | Clamp de escala mínima/máxima |
| Gradiente animado chama Update todo frame | Custo baixo (6-20 caracteres), batch com Update existente |
| TMP font pode não renderizar em distância longa | Configurar `fontSizeMin`/`fontSizeMax` no TMP |
