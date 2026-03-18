# Log Copier

Cópia de logs filtrados para clipboard.

## ADDED Requirements

### Requirement: LogCopier fornece botão para copiar logs

O sistema SHALL fornecer um widget `LogCopier` que é um botão para copiar logs.

#### Scenario: Clicar no botão copia logs para clipboard

- **GIVEN** um `LogCopier` renderizado
- **WHEN** o usuário clica no botão
- **THEN** as linhas de log visíveis são copiadas para o clipboard
- **AND** uma notificação de sucesso é exibida

---

### Requirement: Copiar respeita filtros ativos

O sistema SHALL copiar apenas as linhas que passam pelo filtro atual.

#### Scenario: Copiar com filtro ERROR copia apenas errors

- **GIVEN** um `ChatLog` com filtro `ERROR` ativo
- **AND** 10 mensagens ERROR, 50 mensagens INFO
- **WHEN** o botão copiar é clicado
- **THEN** apenas as 10 mensagens ERROR são copiadas
- **AND** as 50 mensagens INFO não são incluídas

#### Scenario: Copiar com filtro ALL copia tudo

- **GIVEN** um `ChatLog` com filtro `ALL` ativo
- **AND** múltiplas mensagens de vários níveis
- **WHEN** o botão copiar é clicado
- **THEN** todas as mensagens são copiadas

---

### Requirement: Copiar respeita busca ativa

O sistema SHALL copiar apenas as linhas que contêm o termo de busca, quando busca está ativa.

#### Scenario: Copiar com busca ativa copia apenas matches

- **GIVEN** um `ChatLog` com busca "error" ativa
- **AND** 7 mensagens contendo "error"
- **WHEN** o botão copiar é clicado
- **THEN** apenas as 7 mensagens com "error" são copiadas
- **AND** outras mensagens não são incluídas

---

### Requirement: Formato de cópia preserva timestamp e nível

O sistema SHALL formatar as linhas copiadas com timestamp e nível.

#### Scenario: Linhas copiadas mantém formato original

- **GIVEN** um `ChatLog` com linhas formatadas como `[14:23:45] [INFO] Message`
- **WHEN** as linhas são copiadas
- **THEN** o formato preserva timestamp e nível
- **AND** cada linha termina com newline

---

### Requirement: Notificação confirma quantidade copiada

O sistema SHALL exibir notificação com número de linhas copiadas.

#### Scenario: Copiar 50 linhas mostra notificação

- **GIVEN** um `LogCopier` que copiou 50 linhas
- **WHEN** a cópia é concluída
- **THEN** uma notificação é exibida: "50 linhas copiadas!"
- **AND** a notificação usa estilo `success`

#### Scenario: Copiar zero linhas mostra aviso

- **GIVEN** um `LogCopier` sem linhas para copiar
- **WHEN** o botão é clicado
- **THEN** uma notificação é exibida: "Nenhuma linha para copiar"
- **AND** a notificação usa estilo `warning`

---

### Requirement: Copiar falha graciosamente se clipboard não disponível

O sistema SHALL tratar erros de clipboard sem quebrar a UI.

#### Scenario: Clipboard indisponível mostra erro

- **GIVEN** um ambiente sem clipboard disponível
- **WHEN** o botão copiar é clicado
- **THEN** nenhuma exceção é lançada
- **AND** uma notificação de erro é exibida: "Clipboard não disponível"

---

### Requirement: Copiar usa pyperclip ou fallback nativo

O sistema SHALL tentar usar `pyperclip` primeiro, com fallback para clipboard nativo do Textual.

#### Scenario: pyperclip disponível é usado

- **GIVEN** `pyperclip` instalado e disponível
- **WHEN** o botão copiar é clicado
- **THEN** `pyperclip.copy()` é usado
- **AND** o conteúdo é copiado corretamente

#### Scenario: pyperclip não disponível usa fallback

- **GIVEN** `pyperclip` não instalado
- **WHEN** o botão copiar é clicado
- **THEN** o clipboard nativo do Textual é usado
- **AND** a cópia funciona normalmente

---

### Requirement: Histórico de cópia limitado a última operação

O sistema SHALL manter apenas o conteúdo da última cópia.

#### Scenario: Segunda cópia substitui a anterior

- **GIVEN** um `LogCopier` que copiou 50 linhas
- **WHEN** uma nova cópia de 30 linhas é feita
- **THEN** o clipboard contém apenas as 30 linhas
- **AND** as 50 linhas anteriores foram sobrescritas
