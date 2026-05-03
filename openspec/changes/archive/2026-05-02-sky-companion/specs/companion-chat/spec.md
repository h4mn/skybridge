## ADDED Requirements

### Requirement: Comando /skychat permite jogador conversar com a Sky

O mod SHALL registrar um handler de input que captura o comando `/skychat <mensagem>` digitado no console/input do jogo e enfileira a mensagem como evento significativo.

#### Scenario: Mensagem capturada e enfileirada

- **WHEN** o jogador digita `/skychat onde tem mais ferro?` no input do jogo
- **THEN** o mod captura a mensagem "onde tem mais ferro?", enfileira como evento tipo `skychat` com descrição da mensagem, e exibe confirmação visual no jogo

#### Scenario: Comando sem mensagem

- **WHEN** o jogador digita apenas `/skychat` sem texto adicional
- **THEN** o mod exibe mensagem de uso: "Uso: /skychat <mensagem>" e NÃO enfileira evento

#### Scenario: Múltiplas mensagens em sequência

- **WHEN** o jogador envia 3 mensagens `/skychat` em sequência rápida
- **THEN** as 3 mensagens são enfileiradas como eventos separados, cada uma com seu timestamp

### Requirement: Resposta da Sky aparece como balão sobre o modelo

Quando o Claude Code responde via `send_companion_message`, o mod SHALL exibir a resposta como balão de fala world-space sobre o modelo 3D da Sky.

#### Scenario: Resposta exibida como balão

- **WHEN** o comando `POST /action` com `{type: "show_message", text: "Tem ferro perto da caverna ao norte!"}` é recebido
- **THEN** o balão de fala aparece sobre o modelo 3D com o texto "Tem ferro perto da caverna ao norte!"

#### Scenario: Animação speaking durante resposta

- **WHEN** uma resposta é exibida no balão
- **THEN** o modelo muda para animação speaking automaticamente e retorna para idle após o balão desaparecer
