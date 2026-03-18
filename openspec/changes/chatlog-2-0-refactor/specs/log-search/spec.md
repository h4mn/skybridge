# Log Search

Busca reativa em logs com highlight em tempo real.

## ADDED Requirements

### Requirement: LogSearch fornece input de texto para busca

O sistema SHALL fornecer um widget `LogSearch` que é um input de texto para busca.

#### Scenario: Digitar no input atualiza termo de busca

- **GIVEN** um `LogSearch` renderizado
- **WHEN** o usuário digita "error"
- **THEN** o termo de busca é atualizado para "error"
- **AND** uma mensagem `SearchChanged` é emitida

---

### Requirement: Busca é reativa com debounce

O sistema SHALL aplicar debounce de 300ms antes de executar a busca.

#### Scenario: Digitação rápida não executa múltiplas buscas

- **GIVEN** um `LogSearch`
- **WHEN** o usuário digita "e", depois "r", depois "r" em 100ms
- **THEN** apenas uma busca é executada após 300ms de inatividade
- **AND** o termo de busca final é "err"

#### Scenario: Busca executa após pausa na digitação

- **GIVEN** um `LogSearch`
- **WHEN** o usuário digita "test" e para de digitar
- **THEN** após 300ms a busca é executada
- **AND** os resultados são destacados

---

### Requirement: Resultados de busca são destacados

O sistema SHALL destacar todas as ocorrências do termo de busca nos logs.

#### Scenario: Busca por "error" highlights matching text

- **GIVEN** logs contendo "Connection error" e "Success"
- **WHEN** o usuário busca por "error"
- **THEN** "error" em "Connection error" fica destacado
- **AND** "Success" não é destacado

#### Scenario: Highlight usa style inverse do Textual

- **GIVEN** resultados de busca encontrados
- **WHEN** os logs são renderizados
- **THEN** o texto correspondente usa `style="inverse"`
- **AND** o contraste torna os matches fáceis de ver

---

### Requirement: Busca é case-insensitive

O sistema SHALL ignorar maiúsculas/minúsculas ao buscar.

#### Scenario: Busca por "erro" encontra "Error"

- **GIVEN** logs contendo "Connection Error"
- **WHEN** o usuário busca por "erro" (minúsculo)
- **THEN** "Connection Error" é encontrado
- **AND** "Error" é destacado

---

### Requirement: Indicador mostra número de matches

O sistema SHALL exibir um contador de quantas ocorrências foram encontradas.

#### Scenario: Contador atualiza com cada busca

- **GIVEN** um `ChatLog` com 50 mensagens
- **WHEN** uma busca encontra 7 matches
- **THEN** o contador mostra "7 matches"
- **AND** o contador fica visível próximo ao input

#### Scenario: Busca sem resultados mostra indicador

- **GIVEN** um `ChatLog` com mensagens
- **WHEN** uma busca não encontra nenhum match
- **THEN** o contador mostra "0 matches"
- **AND** um ícone de alerta é exibido

---

### Requirement: Busca pode ser limpa

O sistema SHALL permitir limpar o termo de busca.

#### Scenario: Limpar busca remove highlights

- **GIVEN** uma busca ativa com highlights
- **WHEN** o usuário clica no botão de limpar (X)
- **THEN** o termo de busca é limpo
- **AND** todos os highlights são removidos
- **AND** `SearchChanged` é emitido com string vazia

---

### Requirement: Busca suporta regex simples

O sistema SHALL suportar curingas `*` e `?` na busca.

#### Scenario: Busca com curinga encontra múltiplos patterns

- **GIVEN** logs contendo "error1", "error2", "warning"
- **WHEN** o usuário busca por "error*"
- **THEN** "error1" e "error2" são encontrados
- **AND** "warning" não é encontrado

---

### Requirement: Navegação entre matches

O sistema SHALL permitir navegar entre as ocorrências encontradas.

#### Scenario: Botões Next/Previous navegam entre matches

- **GIVEN** uma busca com 5 matches
- **WHEN** o usuário clica em "Next"
- **THEN** o scroll vai para o próximo match
- **AND** o match atual é destacado com estilo diferente
- **AND** clicando "Previous" volta ao match anterior

#### Scenario: Wrap-around ao navegar

- **GIVEN** uma busca com matches
- **WHEN** o usuário está no último match e clica "Next"
- **THEN** a navegação volta para o primeiro match
