## 1. Configuração BepInEx

- [ ] 1.1 Adicionar ConfigEntries em MovementConfig: NametagText, NametagVisible, NametagOffsetY, NametagFontSize, NametagGradientSpeed, NametagMinScale, NametagMaxScale
- [ ] 1.2 Criar array de cores SKY_GRADIENT (6 cores: azul→índigo→violeta→roxo→lavanda→fúcsia)

## 2. Criação do Label

- [ ] 2.1 Criar método CreateNametag() em CompanionController — TextMeshPro world-space, child do companion
- [ ] 2.2 Configurar TMP: fontSize, alignment center, sem wrappint, color branco inicial
- [ ] 2.3 Posicionar label acima do modelo com offset configurável

## 3. Gradiente Animado

- [ ] 3.1 Implementar sweep temporal por caractere — offset = Time.time * speed, cor = Lerp(cores[i], cores[i+1], fração)
- [ ] 3.2 Aplicar cores via TMP textInfo.meshInfo.colors32 no Update (sem GC allocation)

## 4. Billboard e Escala

- [ ] 4.1 Billboard: rotacionar label LookAt câmera no Update
- [ ] 4.2 Escala por distância: scale = baseSize / Mathf.Clamp(dist, min, max)
- [ ] 4.3 Integrar lógica de escala no Update existente (junto com balloon scale)

## 5. Visibilidade e Evolução

- [ ] 5.1 Respeitar NametagVisible config — ocultar/mostrar label
- [ ] 5.2 Forçar visível quando speaking
- [ ] 5.3 Atualizar nome na evolução: "Sky" → "Sky Oesbe" (ou config + " Oesbe")

## 6. Validação

- [ ] 6.1 Validar in-game: label visível, gradiente animado, escala constante
- [ ] 6.2 Validar in-game: evolução muda nome, speaking força visível
