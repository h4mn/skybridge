## ADDED Requirements

### Requirement: Mod expõe estado completo do jogo via HTTP GET /state

O mod BepInEx SHALL expor endpoint `GET /state` retornando JSON com terraform (Terraformation, Heat, Oxygen, Pressure, Plants, Insects, Animals, Biomass), posição do jogador (x, y, z), inventário (lista de itens com id e nome) e eventos recentes.

#### Scenario: Estado completo retornado com jogo em execução

- **WHEN** o jogo está rodando com o mod carregado e uma requisição `GET /state` é enviada para `localhost:{porta}`
- **THEN** o mod retorna JSON com todos os campos de terraform preenchidos com valores float, posição do jogador como array [x, y, z], inventário como array de objetos {id, name}, e eventos recentes como array

#### Scenario: Estado retornado sem WorldUnitsHandler capturado

- **WHEN** o Harmony patch de `WorldUnitsHandler.CreateUnits` ainda não disparou e uma requisição `GET /state` é enviada
- **THEN** o mod retorna JSON com campos de terraform em 0.0 e posição do jogador em [0, 0, 0] como fallback

### Requirement: Mod expõe eventos filtrados via HTTP GET /events

O mod SHALL manter uma fila interna de eventos significativos (milestones de terraformação, morte do jogador, mensagens `/skychat`, story events, construções concluídas) e expô-los via `GET /events`.

#### Scenario: Eventos significativos enfileirados

- **WHEN** o jogador atinge um milestone de terraformação (ex: primeira chuva, insetos aparecem)
- **THEN** o mod adiciona evento na fila interna com tipo, descrição e timestamp Unix

#### Scenario: Eventos insignificantes descartados

- **WHEN** o jogador se move ou O2 sobe 0.1
- **THEN** o mod NÃO adiciona evento na fila interna

#### Scenario: Consulta de eventos retorna lista

- **WHEN** uma requisição `GET /events` é enviada
- **THEN** o mod retorna array de eventos enfileirados desde a última consulta, cada um com {type, description, timestamp}

#### Scenario: Fila tem limite de tamanho

- **WHEN** a fila de eventos excede 50 entradas
- **THEN** o mod remove o evento mais antigo (FIFO)

### Requirement: Mod executa ações via HTTP POST /action

O mod SHALL aceitar comandos via `POST /action` com JSON body especificando a ação e seus parâmetros.

#### Scenario: Ação recebida e registrada

- **WHEN** uma requisição `POST /action` com JSON válido é enviada
- **THEN** o mod registra a ação no log e executa a lógica correspondente ao tipo de ação

#### Scenario: Ação não implementada

- **WHEN** uma requisição `POST /action` com tipo de ação desconhecido é enviada
- **THEN** o mod retorna `{status: "not_implemented"}`

### Requirement: Porta HTTP configurável via BepInEx config

A porta do servidor HTTP SHALL ser configurável via arquivo de configuração BepInEx, com default `17234`.

#### Scenario: Porta padrão usada sem configuração

- **WHEN** o mod é carregado sem configuração customizada
- **THEN** o servidor HTTP inicia na porta 17234

#### Scenario: Porta customizada via config

- **WHEN** o usuário define a porta no arquivo de config do BepInEx
- **THEN** o servidor HTTP inicia na porta especificada
