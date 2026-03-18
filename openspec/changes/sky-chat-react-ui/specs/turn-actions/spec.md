# Turn Actions

Ações pós-resposta (Copy, Retry) para melhorar experiência do usuário.

## ADDED Requirements

### Requirement: ActionBar com botões Copy e Retry
O sistema SHALL exibir um `ActionBar` abaixo do `SkyBubble` com botões Copy (copiar resposta) e Retry (reenviar mensagem do usuário).

#### Scenario: ActionBar visível após resposta completa
- **WHEN** turno chega ao estado DONE
- **THEN** ActionBar é exibido abaixo do SkyBubble com botões [Copy] [Retry]

### Requirement: Botão Copy copia conteúdo do SkyBubble
O sistema SHALL copiar o conteúdo markdown do `SkyBubble` para a área de transferência quando o botão Copy é acionado.

#### Scenario: Copiar resposta com sucesso
- **WHEN** usuário clica no botão [Copy]
- **THEN** conteúdo do SkyBubble é copiado para clipboard
- **AND** feedback visual "✓ Copiado!" aparece por 2 segundos

#### Scenario: Tratamento de erro ao copiar
- **WHEN** clipboard não está disponível ou operação falha
- **THEN** feedback visual "Erro ao copiar" aparece
- **AND** nenhum crash ou exceção é propagado

### Requirement: Botão Retry reemite última mensagem do usuário
O sistema SHALL re-enviar a última mensagem do usuário quando o botão Retry é acionado, criando um novo turno com o mesmo conteúdo.

#### Scenario: Retry com sucesso
- **WHEN** usuário clica no botão [Retry]
- **THEN** novo Turn é criado com a mesma mensagem do usuário
- **AND** mensagem anterior permanece visível no histórico
- **AND** foco move para o novo turno

#### Scenario: Retry sem mensagem anterior
- **WHEN** usuário clica [Retry] mas não há mensagem anterior (edge case)
- **THEN** botão é desabilitado
- **AND** tooltip indica "Nada para repetir"

### Requirement: ActionBar sempre visível em terminal
O sistema SHALL manter ActionBar sempre visível em interface terminal (não depende de hover, que não funciona em TUI).

#### Scenario: ActionBar visível em terminal
- **WHEN** SkyChat está rodando em terminal Textual
- **THEN** ActionBar é sempre visível após resposta completa
- **AND** não depende de mouse hover

### Requirement: Copy preserva formatação markdown
O sistema SHALL copiar o conteúdo preservando formatação markdown (negrito, código, listas).

#### Scenario: Copy com formatação preservada
- **WHEN** SkyBubble contém markdown com negrito, código, listas
- **THEN** clipboard contém o markdown original com formatação
- **AND** não é texto plano sem formatação

---

> "Ações que potencilizam o usuário" – made by Sky ⚡
