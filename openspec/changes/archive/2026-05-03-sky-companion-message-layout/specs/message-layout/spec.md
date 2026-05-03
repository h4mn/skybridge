# Spec: Sky Message Layout (OnGUI Overlay)

## Objetivo

Definir o layout do frame de mensagem do companion (sky-message) renderizado via OnGUI no Planet Crafter.

## Layout

```
┌──────────────────────────────────────────────────────┐
│  0..20%        │  20..90%                            │  90..100%  │
│                │                                      │            │
│  [borboleta    │  ┌─────────────────────────────┐   │            │
│   modelo 3D    │  │  sky-message frame           │   │            │
│   speaking]    │  │  altura: 45% da tela         │   │            │
│                │  │  largura: 70% da tela        │   │            │
│                │  │  fundo: azul-violeta escuro   │   │            │
│                │  │  texto: branco 20px bold      │   │            │
│                │  └─────────────────────────────┘   │            │
│                │                                      │            │
│                │  ...restante da tela do jogo...      │            │
│                │                                      │            │
│                │  ┌─ chatbox ────────────────────┐   │            │
│                │  └──────────────────────────────┘   │            │
└──────────────────────────────────────────────────────┘
```

## Dimensões

| Propriedade | Valor | Descrição |
|---|---|---|
| Altura | `Screen.height * 0.45f` | 45% da altura da tela |
| Largura | `Screen.width * 0.7f` | 70% da largura da tela |
| Posição X | `Screen.width * 0.2f` | 20% à esquerda (reservado para borboleta) |
| Posição Y | `Screen.height * 0.05f` | 5% do topo |

## Estilo Visual

| Propriedade | Valor |
|---|---|
| Fundo (Box) | `Color(0.15f, 0.08f, 0.3f, 0.8f)` — azul-violeta escuro, 80% opacidade |
| Sombra texto | `Color(0, 0, 0, 0.8f)` — preto 80%, offset 2px |
| Texto | Branco, 20px bold, center-aligned, word-wrap |
| Flash inicial | 3x ao aparecer |
| Duração | 30 segundos |

## GameObject

| Campo | Valor |
|---|---|
| Nome | `"sky-message"` |
| Tipo | GameObject com TextMeshPro (balloon 3D) |
| Parent | CompanionController transform |
| Posição local | (0, 0.4, 0) |
| Ativo | Apenas durante speaking |

## Comportamento

- **WHEN** `ShowMessage(text)` é chamado
- **THEN** frame aparece no topo com flash 3x
- **AND** texto permanece visível por 30 segundos
- **AND** após expirar, frame desaparece

## Zonas de Layout

| Zona | % Tela | Propósito |
|---|---|---|
| Esquerda | 0-20% | Espaço reservado para modelo 3D da borboleta quando speaking |
| Mensagem | 20-90% | Frame de texto da mensagem |
| Direita | 90-100% | Margem livre |

> "Layout que respira entre borboleta e texto" – made by Sky 🎨
