## 1. Configuração BepInEx

- [x] 1.1 Adicionar ConfigEntries em MovementConfig: NametagText, NametagVisible, NametagOffsetY, NametagFontSize, NametagGradientSpeed
- [x] 1.2 Remover NametagMinScale e NametagMaxScale do MovementConfig

## 2. Nametag IMGUI (substitui TMP world-space)

- [x] 2.1 Remover CreateNametag() com TextMeshPro
- [x] 2.2 Criar CreateNametag() com GUIStyle para IMGUI
- [x] 2.3 Implementar DrawNametagIMGUI() no OnGUI: WorldToScreenPoint + GUI.Label por caractere com gradiente
- [x] 2.4 Visibilidade: screenPos.z > 0 (atrás da câmera), NametagVisible || speaking
- [x] 2.5 Gradiente sweep por caractere com GUI.Label individual + Lerp de cores

## 3. Limpeza

- [x] 3.1 Remover UpdateNametag() e ApplyNametagGradient() (TMP)
- [x] 3.2 Remover _nametagGO e _nametagText (TMP objects)
- [x] 3.3 Remover UpdateNametagName() e lógica de evolução no nametag

## 4. Validação

- [ ] 4.1 Validar in-game: label visível com gradiente animado acima do companion
- [ ] 4.2 Validar in-game: label some quando companion está atrás da câmera
- [ ] 4.3 Validar in-game: speaking força visível mesmo com config off
