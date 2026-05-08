## ADDED Requirements

### Requirement: Speaking voa para canto superior esquerdo do viewport
O estado **speaking** SHALL mover o companion para o canto superior esquerdo da tela do jogador quando `ShowMessage()` é chamado, atuando como "avatar" visual da mensagem.

#### Scenario: Posicionamento via ViewportToWorldPoint
- **WHEN** `ShowMessage()` é chamado
- **THEN** companion SHALL voar para `Camera.ViewportToWorldPoint(0.15, 0.85, offset)` com offset configurável (default 1.5u)

#### Scenario: LookAt câmera
- **WHEN** em speaking
- **THEN** companion SHALL olhar para a câmera (de frente para o jogador)

#### Scenario: Retorno após mensagem expirar
- **WHEN** a mensagem expira (30s) ou fade-out completa
- **THEN** companion SHALL retornar ao estado anterior ao speaking

#### Scenario: Asas aceleradas
- **WHEN** em speaking
- **THEN** asas SHALL bater a 4Hz (velocidade speaking)

### Requirement: Lead voa na frente do jogador em movimento
O estado **lead** SHALL posicionar o companion à frente do jogador na direção do movimento, como "punho do Superman", quando o jogador está andando ou usando jetpack.

#### Scenario: Ativação por velocidade
- **WHEN** velocidade horizontal do jogador > `lead_min_speed` (default 2 u/s) por mais de 0.5s consecutivos
- **THEN** companion SHALL transicionar para lead

#### Scenario: Posicionamento à frente
- **WHEN** em lead
- **THEN** companion SHALL se posicionar em `player.position + player.forward * lead_distance + Vector3.up * lead_height`

#### Scenario: Match velocidade do jogador
- **WHEN** em lead
- **THEN** companion SHALL manter velocidade igual à do jogador + 10% (lead_speed_bonus)

#### Scenario: Retorno ao orbit
- **WHEN** jogador para (velocidade < threshold) por mais de `lead_stop_delay` segundos (default 1s)
- **THEN** companion SHALL retornar ao estado orbit

#### Scenario: Lead ignora eixo Y
- **WHEN** jogador voa verticalmente com jetpack
- **THEN** cálculo de velocidade para lead SHALL considerar apenas eixos X e Z (horizontal)

### Requirement: Celebrate faz espiral ascendente em milestones
O estado **celebrate** SHALL fazer o companion executar uma espiral ascendente quando um milestone de terraformação é detectado.

#### Scenario: Ativação por milestone
- **WHEN** milestone de terraformação é detectado
- **THEN** companion SHALL transicionar para celebrate

#### Scenario: Espiral ascendente
- **WHEN** em celebrate
- **THEN** companion SHALL subir em espiral (1.5 voltas, sobe 5u, dura 3s, velocidade 4 u/s)

#### Scenario: LookAt para cima
- **WHEN** em celebrate
- **THEN** companion SHALL olhar para cima (sky)

#### Scenario: Retorno automático
- **WHEN** celebrate termina (3s)
- **THEN** companion SHALL retornar ao estado orbit

### Requirement: Greeting aparece em arco ao carregar save
O estado **greeting** SHALL fazer o companion aparecer em um arco descendente seguido de figura-8 na frente do jogador quando o save carrega.

#### Scenario: Delay antes do greeting
- **WHEN** o companion é inicializado (spawn/save load)
- **THEN** SHALL aguardar 1 segundo (carregamento do save e spawn do jogador) antes de iniciar o greeting

#### Scenario: Fase 1 — arco descendente
- **WHEN** o greeting inicia
- **THEN** SHALL executar arco descendente de cima para frente do jogador (2s de duração)

#### Scenario: Fase 2 — figura-8
- **WHEN** a fase 1 do greeting termina
- **THEN** SHALL executar figura-8 na frente do jogador (1s de duração)

#### Scenario: Transição pós-greeting
- **WHEN** greeting termina (3s total: 2s arco + 1s figura-8)
- **THEN** companion SHALL transicionar para orbit

### Requirement: Listening aproxima quando jogador digita
O estado **listening** SHALL fazer o companion se aproximar do jogador quando uma mensagem de chat é detectada, posicionando-se acima da UI do chatbox.

#### Scenario: Aproximação ao jogador
- **WHEN** jogador envia mensagem no chat
- **THEN** companion SHALL voar para posição acima do chatbox via ViewportToWorldPoint(0.5, 0.4, 2.0)

#### Scenario: LookAt rosto do jogador
- **WHEN** em listening
- **THEN** companion SHALL olhar para o rosto do jogador (playerPosition + up * 1.7)

#### Scenario: Timeout de listening
- **WHEN** 3s se passam sem nova mensagem no chat
- **THEN** companion SHALL transicionar para estado thinking (aguardando resposta do companion)

#### Scenario: Fluxo listening → thinking → speaking
- **WHEN** o jogador envia mensagem e o companion responde
- **THEN** o fluxo SHALL ser: listening (3s) → thinking (aguarda resposta) → speaking (resposta enviada)

#### Scenario: Asas aceleradas no listening
- **WHEN** em listening
- **THEN** asas SHALL bater a 3Hz (acelerado mas não speaking)

### Requirement: Explore vagueia pela área do jogador
O estado **explore** SHALL fazer o companion vaguear por pontos aleatórios ao redor do jogador.

#### Scenario: Pontos aleatórios
- **WHEN** em explore
- **THEN** companion SHALL escolher pontos aleatórios num raio de 5u do jogador

#### Scenario: Limite de distância
- **WHEN** companion está a mais de 8u do jogador
- **THEN** SHALL voltar em direção ao jogador antes de continuar explorando

#### Scenario: Explore via MCP tool (por ora)
- **WHEN** `move_companion_to(strategy="explore")` é chamado
- **THEN** companion SHALL transicionar para explore
