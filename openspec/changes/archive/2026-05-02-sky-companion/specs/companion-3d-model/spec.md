## ADDED Requirements

### Requirement: Modelo 3D da Sky aparece no mundo e evolui com a terraformação

O mod SHALL instanciar um modelo 3D da Sky (borboleta) no mundo do jogo logo após o load. O modelo DEVE evoluir conforme o estágio de terraformação: **Lorpen** antes do oxigênio atingir estágio de insetos, **Oesbe** após.

#### Scenario: Modelo carregado como Lorpen (pré-oxigênio) usando prefab do jogo

- **WHEN** o mod é carregado e o terraform estágio de insetos AINDA NÃO foi atingido e o prefab de Lorpen está acessível via API
- **THEN** o mod instancia o prefab de Lorpen no mundo, posicionado próximo ao jogador

#### Scenario: Modelo carregado como Lorpen usando primitivas como fallback

- **WHEN** o prefab de Lorpen do jogo não está acessível e o estágio de insetos AINDA NÃO foi atingido
- **THEN** o mod cria modelo com primitivas Unity: dois quads planos coloridos como asas + capsule fina como corpo, posicionado próximo ao jogador

#### Scenario: Evolução para Oesbe quando oxigênio atinge estágio de insetos

- **WHEN** o WorldUnitsHandler detecta que o oxigênio atingiu o threshold de insetos (insect spawn habilitado)
- **THEN** o modelo 3D é substituído de Lorpen para Oesbe (prefab do jogo ou primitivas mais elaboradas), com transição visual suave

#### Scenario: Modelo já nasce como Oesbe em save avançado

- **WHEN** o mod é carregado em um save onde o estágio de insetos JÁ foi atingido
- **THEN** o modelo é instanciado diretamente como Oesbe, sem passar por Lorpen

### Requirement: Modelo executa animações controláveis externamente

O modelo 3D SHALL suportar animações de idle (voando/batem asas), thinking (asas mais lentas, leve flutuação) e speaking (asas batem, balão ativo). As animações DEVEM ser ativáveis via comando externo (`POST /action`).

#### Scenario: Animação idle ao spawnar

- **WHEN** o modelo 3D é instanciado no mundo
- **THEN** ele inicia com animação idle (asas batendo suavemente, leve flutuação)

#### Scenario: Mudança de animação via comando

- **WHEN** o comando `POST /action` com `{type: "set_animation", animation: "thinking"}` é recebido
- **THEN** o modelo muda para animação thinking (asas mais lentas, flutuação diferente)

#### Scenario: Animação speaking com balão

- **WHEN** o comando `POST /action` com `{type: "set_animation", animation: "speaking"}` é recebido
- **THEN** o modelo muda para animação speaking e ativa o componente de balão de fala

### Requirement: Modelo mantém distância configurável do jogador

O modelo 3D SHALL manter uma distância configurável do jogador (default ~3 unidades Unity). Quando em modo follow, o modelo se move suavemente para manter essa distância.

#### Scenario: Distância padrão mantida

- **WHEN** o modelo está em modo follow_player e o jogador se move
- **THEN** o modelo se move suavemente mantendo ~3 unidades de distância do jogador

#### Scenario: Distância customizada via config

- **WHEN** o usuário define distância customizada no arquivo de config do BepInEx
- **THEN** o modelo mantém a distância especificada em vez de 3 unidades

### Requirement: Balão de fala world-space com escala por distância

O modelo SHALL exibir balão de fala como TextMeshPro em world-space acima do modelo. O font size DEVE escalar com a distância ao jogador para manter legibilidade — nem muito grande quando perto, nem muito pequeno quando longe.

#### Scenario: Balão aparece ao receber mensagem

- **WHEN** o comando `POST /action` com `{type: "show_message", text: "..."}` é recebido
- **THEN** um balão de fala aparece acima do modelo com o texto especificado

#### Scenario: Balão escala com distância

- **WHEN** o modelo está a diferentes distâncias do jogador (2, 3, 5 unidades)
- **THEN** o font size do TextMeshPro ajusta para manter texto legível em todas as distâncias

#### Scenario: Balão desaparece após timeout

- **WHEN** um balão de fala é exibido e passam 5 segundos sem nova mensagem
- **THEN** o balão desaparece com fade suave
