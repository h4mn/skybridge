# Post-Mortem: sky-companion-nametag

**Data:** 2026-05-03
**Resultado:** Falha — não foi possível implementar um name tag funcional

## O que tentamos

Uma label com o nome "Sky" acima da borboleta companion, com gradiente animado.

## Tentativas e por que falharam

### 1. TextMeshPro world-space (child do companion)
- Criou `_nametagGO` com `AddComponent<TextMeshPro>()`
- Billboard manual com `LookAt(camera)`, escala por distância
- **Resultado:** nunca apareceu na tela. Motivo incerto — possivelmente renderer do TMP não renderiza sem canvas/material correto, ou posição/escala estavam errados para o contexto do jogo.

### 2. TextMeshPro world-space simplificado (sem billboard, sem escala)
- Removeu LookAt e escala dinâmica
- **Resultado:** ainda não apareceu.

### 3. Frustum culling via Renderer.isVisible
- Adicionou visibilidade condicional baseada no renderer do modelo
- **Resultado:** introduziu bug — `Renderer.isVisible` retorna false em vários cenários (modelo primitivo sem renderer, modelo desativado antes do greeting, transição durante evolução).

### 4. OnGUI/IMGUI com WorldToScreenPoint
- Abordagem totalmente diferente: desenhar na tela via `GUI.Label`
- Posição via `Camera.main.WorldToScreenPoint()`
- Gradiente caractere por caractere com GUI.Label individual
- **Bug:** `GUIStyle` criado fora do `OnGUI` crasha silenciosamente (`GUI.skin` é null)
- **Fix:** lazy init dentro do `OnGUI`
- **Resultado:** continuou não aparecendo. Motivo incerto.

## Causas raiz prováveis

1. **Falta de feedback visual in-game** — não dá pra debugar TextMeshPro ou IMGUI sem ver o jogo. Cada tentativa exige reiniciar o jogo, o que torna iteração extremamente lenta.
2. **Complexidade do Unity/BepInEx** — TMP world-space tem requisitos ocultos (canvas, material, shader, sorting layer) que não são óbvios sem documentação específica do contexto Planet Crafter.
3. **Planejamento insuficiente** — fomos direto pra implementação sem validar a abordagem básica (um label simples sem gradiente) primeiro.
4. **Escopo crescente** — cada iteração mudava a estratégia inteira em vez de isolar o problema.

## Lições

- **Validar o mínimo antes de iterar** — se um "Sky" branco sem gradiente não aparece, gradiente não vai salvar.
- **Uma estratégia por vez** — TMP world-space, depois IMGUI. Não pular entre elas sem entender por que a anterior falhou.
- **Debug logging é essencial** — cada abordagem deveria ter logado posição, visibilidade, e screenPos pra diagnosticar.
- **Não acumular frustração** — várias tentativas falhando quebra a UX mental do jogador/desenvolvedor.

## Estado atual

- Código C# revertido ao commit `2e1d7da` (pre-nametag)
- Specs e design atualizados no openspec (documentam as decisões e remoções)
- TODO-001 (mensagens no chat do jogo) criado como alternativa

> "Falhar rápido é melhor que falhar devagar" – made by Sky 🦋
