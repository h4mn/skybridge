## ADDED Requirements

### Requirement: Tool send_companion_message exibe mensagem no jogo

O MCP Tool `send_companion_message(text)` SHALL enviar `POST /action` ao mod com `{type: "show_message", text: <text>}` para exibir a mensagem como balão de fala sobre o modelo 3D.

#### Scenario: Mensagem enviada com sucesso

- **WHEN** Claude Code chama `send_companion_message` com text = "Olá! Vi que você atingiu o primeiro milestone!"
- **THEN** o tool envia POST ao mod e retorna confirmação de sucesso

#### Scenario: Mod indisponível

- **WHEN** Claude Code chama `send_companion_message` mas o mod não está respondendo
- **THEN** o tool retorna erro informativo: "Companion não está disponível — verifique se o jogo está aberto com o mod carregado"

### Requirement: Tool move_companion_to executa estratégia de movimentação

O MCP Tool `move_companion_to(strategy, params)` SHALL enviar `POST /action` ao mod com a estratégia especificada. As estratégias são: `follow_player`, `goto_coords(x, y, z)`, `goto_named(name)`, `stay`.

#### Scenario: Estratégia follow_player

- **WHEN** Claude Code chama `move_companion_to` com strategy = "follow_player"
- **THEN** o mod inicia o modo de seguir o jogador mantendo distância configurável

#### Scenario: Estratégia goto_coords

- **WHEN** Claude Code chama `move_companion_to` com strategy = "goto_coords" e params = {"x": 100, "y": 50, "z": 200}
- **THEN** o mod move o modelo para as coordenadas (100, 50, 200)

#### Scenario: Estratégia goto_named

- **WHEN** Claude Code chama `move_companion_to` com strategy = "goto_named" e params = {"name": "base"}
- **THEN** o mod move o modelo para o local nomeado "base" se existir no registro

#### Scenario: Estratégia stay

- **WHEN** Claude Code chama `move_companion_to` com strategy = "stay"
- **THEN** o modelo para de seguir o jogador e fica no local atual

### Requirement: Tool set_companion_animation muda animação do modelo

O MCP Tool `set_companion_animation(animation)` SHALL enviar `POST /action` ao mod com `{type: "set_animation", animation: <animation>}`. Animações válidas: `idle`, `thinking`, `speaking`.

#### Scenario: Animação alterada com sucesso

- **WHEN** Claude Code chama `set_companion_animation` com animation = "thinking"
- **THEN** o mod muda a animação do modelo para thinking e retorna confirmação

#### Scenario: Animação inválida

- **WHEN** Claude Code chama `set_companion_animation` com animation = "dancing"
- **THEN** o tool retorna erro informando animações válidas: idle, thinking, speaking

### Requirement: Tool get_game_state retorna estado atual do jogo

O MCP Tool `get_game_state()` SHALL consultar `GET /state` no mod e retornar o estado completo (terraform, jogador, inventário) para Claude Code tomar decisões.

#### Scenario: Estado retornado com jogo ativo

- **WHEN** Claude Code chama `get_game_state` e o mod está respondendo
- **THEN** o tool retorna JSON com terraform, posição do jogador, inventário e eventos recentes

#### Scenario: Estado retornado sem jogo

- **WHEN** Claude Code chama `get_game_state` mas o mod não está respondendo
- **THEN** o tool retorna erro informativo: "Jogo não está disponível"
