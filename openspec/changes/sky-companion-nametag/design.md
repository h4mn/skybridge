## Context

O companion já possui modelo 3D (borboleta), state machine de movimentação com 13 estados, e frame de mensagem via OnGUI (IMGUI) que funciona perfeitamente. Falta um identificador visual persistente — um name tag que mostra o nome da borboleta com a identidade visual da Sky.

Referência de identidade visual:
- **Statusline** (`statusline.py`): gradiente SKY_GRADIENT com 6 cores animadas por offset temporal (azul #3B82F6 → índigo #6366F1 → violeta #8B5CF6 → roxo #A855F7 → lavanda #C084FC → fúcsia #D946EF)

## Goals / Non-Goals

**Goals:**
- Label persistente com nome do companion usando o mesmo frame OnGUI/IMGUI das mensagens (`_screenMessage`)
- Posição rastreia companion via `WorldToScreenPoint`
- Gradiente de cores animado (azul→violeta→fúcsia) por sweep temporal por caractere
- Visibilidade: só desenha se companion está na frente da câmera (screenPos.z > 0)
- Visibilidade configurável via BepInEx
- Nome configurável via BepInEx (default: "Sky")

**Non-Goals:**
- Billboard (IMGUI é screen-space, não precisa)
- Escala por distância (IMGUI é screen-space, tamanho fixo)
- Frustum culling via Renderer.isVisible (instável)
- Mudança automática de nome na evolução (será change separada)
- TextMeshPro world-space (não funcionou — Renderer.isVisible instável)

## Decisions

### D1: OnGUI/IMGUI em vez de TextMeshPro world-space

**Escolha:** Usar `OnGUI()` com `GUI.Label` e `Camera.main.WorldToScreenPoint()` para posicionar o nametag na tela. Mesmo frame já usado para `_screenMessage`.

**Alternativas:**
- TextMeshPro world-space: não apareceu — Renderer.isVisible instável, sem renderer no modelo primitivo, transição de evolução quebra
- Canvas Screen Space: mais complexo, não necessário
- Canvas World Space: mais pesado, mesmo problema de visibilidade

**Rationale:** O frame de mensagem (OnGUI) funciona perfeitamente. IMGUI é screen-space, não depende de renderer, e WorldToScreenPoint converte posição do mundo pra tela de forma confiável.

### D2: Gradiente por sweep temporal (caractere por caractere via GUI.Label)

**Escolha:** Desenhar cada caractere como GUI.Label separado com cor do gradiente. Sweep: `cor = Lerp(cores[idx], cores[idx+1], frac)` onde offset avança com `Time.time * speed`.

**Rationale:** IMGUI não suporta per-character colors em Label único. Desenhar caractere a caractere com GUI.Label individual dá o mesmo efeito visual do sweep.

### D3: Visibilidade por screenPos.z > 0

**Escolha:** Se `WorldToScreenPoint` retorna z <= 0, companion está atrás da câmera → não desenha.

**Rationale:** Simples e confiável. Não depende de Renderer.isVisible.

### D4: ConfigEntry para parâmetros essenciais

**Escolha:** BepInEx ConfigEntry para: NametagText, NametagVisible, NametagOffsetY, NametagFontSize, NametagGradientSpeed.

**Rationale:** Hot-reload pelo config do BepInEx sem rebuild. NametagMinScale/NametagMaxScale removidos (IMGUI é screen-space).

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| GUI.Label por caractere pode ser lento com nomes longos | Nomes curtos (3-10 chars), custo desprezível |
| WorldToScreenPoint pode jitter em transições de câmera | Aceitável para label |
| IMGUI roda após OnPostRender → pode piscar | Aceitável para label flutuante |
