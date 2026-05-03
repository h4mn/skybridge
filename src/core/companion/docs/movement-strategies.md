# Movement Strategies — Companion 3D

Tabela de referência para os comportamentos de movimentação do modelo 3D do companion.

## Estados de Movimento

| Nome | Descrição | Gatilho | Posição | LookAt | Velocidade | Asas | Raio/Params |
|------|-----------|---------|---------|--------|------------|------|-------------|
| **orbit** | Circular suave ao redor do jogador | Default (idle) | Órbita horizontal + ondulação senoidal Y | Tangente ao círculo (direção do voo) | Lenta (~1.5 u/s) | Idle (2Hz) | Raio 3u, altura 2u acima, variação Y ±0.5u |
| **speaking** | Voa pro canto sup. esquerdo como "avatar" da mensagem | `ShowMessage()` | `Camera.ViewportToWorldPoint(0.15, 0.85, dist)` | Câmera (de frente pro jogador) | Média (transição rápida) | Speaking (4Hz) | Offset 1.5u da câmera, 30s ou até mensagem expirar |
| **listening** | Aproxima do jogador, fica atenta | Jogador digita no chat | Frente do jogador, ~1.5u, nível dos olhos | Rosto do jogador | Média | Idle acelerado (3Hz) | Volta pra orbit após 10s sem input |
| **thinking** | Paira no lugar, processando | `set_animation("thinking")` | Onde está (parado no ar) | Mantém último LookAt | Zero (paira) | Lenta (1Hz) | Oscilação sutil Y ±0.1u |
| **perch** | Pousa no ombro do jogador | Jogador parado > 30s | Ombro direito do jogador (offset do transform) | Direção que o jogador olha | Muito lenta na aproximação | Parada (dobradas) | Verifica se jogador parou, desce suavemente |
| **celebrate** | Espirala ascendente com animação acelerada | Milestone de terraformação | Centro da órbita, subindo em espiral | Cima (sky) | Rápida (4 u/s) | Speaking (4Hz) | 1.5 voltas, sobe 5u, dura 3s, volta pra orbit |
| **greeting** | Aparece voando em arco na frente do jogador | Carregamento do save / spawn | Arco descendente de cima para frente do jogador | Jogador | Média | Speaking (4Hz) | 1 arco, 2s de duração |
| **goto_coords** | Voa para coordenada específica | `move_companion_to(goto_coords)` | Coordenada (x, y, z) | Direção do voo → destino | Média (~3 u/s) | Idle (2Hz) | Teleporta se dist > 50u |
| **goto_named** | Voa para local nomeado | `move_companion_to(goto_named)` | Lookup no registro de nomes | Direção do voo → destino | Média (~3 u/s) | Idle (2Hz) | Fallback: orbit se nome não existe |
| **stay** | Para no local atual | `move_companion_to(stay)` | Onde está | Último LookAt | Zero | Idle (2Hz) | Oscilação Y sutil (paira no lugar) |
| **flee** | Afasta rapidamente do perigo | Morte do jogador (futuro) | Oposto ao ponto de morte, +5u | Longe do perigo | Rápida (6 u/s) | Speaking (4Hz) | Volta pra orbit após 5s |
| **lead** | Voa na frente do jogador como "punho do Superman" | Jogador andando ou jetpack (velocidade > threshold) | `player.position + player.forward * lead_distance + Vector3.up * 1.5u` | Direção do voo (frente) | Match velocidade do jogador + 10% | Speaking (4Hz) | lead_distance: 3u, velocidade mínima: 2 u/s |
| **explore** | Vagueia pela área ao redor do jogador | Jogador construindo/interagindo | Pontos aleatórios num raio de 5u do jogador | Direção do voo | Lenta (~1 u/s) | Idle (2Hz) | Não se afasta > 8u do jogador |

## Prioridade de Transição

```
speaking > celebrate > listening > lead > flee > goto/stay > perch > explore > orbit
```

## Transições Automáticas

| De | Para | Condição |
|----|------|----------|
| Qualquer | **speaking** | `ShowMessage()` chamado |
| Qualquer | **celebrate** | Milestone de terraformação detectado |
| **speaking** | Estado anterior | Mensagem expira (30s) |
| **listening** | **orbit** | 10s sem input no chat |
| **orbit** | **perch** | Jogador parado > 30s |
| **perch** | **orbit** | Jogador se move |
| **orbit** / **perch** / **explore** | **lead** | Jogador se move (vel > threshold) |
| **lead** | **orbit** | Jogador para (vel < threshold por 2s) |
| **celebrate** | **orbit** | Animação termina (3s) |
| **greeting** | **orbit** | Animação termina (2s) |
| **flee** | **orbit** | 5s após evento |

## Parâmetros Configuráveis

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| orbit_radius | 3.0 u | Raio da órbita ao redor do jogador |
| orbit_height | 2.0 u | Altura acima do jogador |
| orbit_speed | 1.5 u/s | Velocidade da órbita |
| orbit_wobble | 0.5 u | Variação vertical (senoide) |
| perch_delay | 30 s | Tempo parado para pousar |
| speaking_duration | 30 s | Duração da mensagem no overlay |
| listening_timeout | 10 s | Tempo sem input pra voltar ao orbit |
| flee_distance | 5.0 u | Distância de fuga |
| explore_radius | 5.0 u | Raio máximo de exploração |
| explore_max_distance | 8.0 u | Distância máxima do jogador |
| teleport_threshold | 50.0 u | Distância para teleportar ao invés de voar |
| lead_distance | 3.0 u | Distância à frente do jogador no modo lead |
| lead_height | 1.5 u | Altura acima do jogador no modo lead |
| lead_speed_bonus | 10% | Quanto mais rápido que o jogador a borboleta voa |
| lead_min_speed | 2.0 u/s | Velocidade mínima do jogador pra ativar lead |
| lead_stop_delay | 2.0 s | Tempo parado antes de sair do lead |

> "Borboletas não voam em linha reta — e nem a Sky" – made by Sky 🦋
