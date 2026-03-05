# Spec: Tool Feedback Visual (Delta)

## ADDED Requirements

### Requirement: Feedback visual de ferramentas sendo executadas

O sistema SHALL exibir feedback visual claro quando ferramentas (Read, Grep, Bash, etc.) estão sendo executadas pela Sky.

#### Scenario: Ferramenta iniciada mostra nome e input
- **QUANDO** Sky inicia chamada de ferramenta
- **ENTÃO** nome da ferramenta é exibido (ex: "🔧 [Read] src/main.py")
- **E** input da ferramenta é mostrado de forma resumida
- **E** status "executando..." é indicado

#### Scenario: Status da ferramenta muda durante execução
- **QUANDO** ferramenta está em execução
- **ENTÃO** indicador visual mostra progresso (spinner ou dots)
- **QUANDO** ferramenta completa
- **ENTÃO** status muda para "✓ completo" com cor success

#### Scenario: Ferramenta com erro mostra status de erro
- **QUANDO** execução de ferramenta falha
- **ENTÃO** status mostra "❌ erro" em cor error
- **E** mensagem de erro é exibida

---

### Requirement: Widget ToolFeedback exibe chamadas de ferramenta

O sistema SHALL fornecer widget `ToolFeedback` que lista todas as ferramentas usadas na resposta atual.

#### Scenario: ToolFeedback lista ferramentas em ordem de execução
- **QUANDO** múltiplas ferramentas são usadas em uma resposta
- **ENTÃO** ToolFeedback mostra cada ferramenta em ordem de execução
- **E** ferramenta em execução é destacada das demais

#### Scenario: ToolFeedback mostra resultado abreviado
- **QUANDO** resultado de ferramenta é muito longo
- **ENTÃO** apenas primeiros 100 caracteres são exibidos
- **E** "..." é adicionado ao final indicando truncamento
- **E** botão "ver mais" permite expansão (se implementado)

---

### Requirement: Integração com ThinkingPanel

O sistema SHALL integrar feedback de ferramentas no ThinkingPanel como entradas especiais.

#### Scenario: Entrada de tool_start no ThinkingPanel
- **QUANDO** ferramenta é iniciada durante streaming
- **ENTÃO** entrada `tool_start` é adicionada ao ThinkingPanel
- **E** entrada mostra ícone 🔧, nome da ferramenta e input

#### Scenario: Entrada de tool_result no ThinkingPanel
- **QUANDO** resultado de ferramenta chega
- **ENTÃO** entrada `tool_result` é adicionada ao ThinkingPanel
- **E** entrada mostra ícone ✓ e resultado da ferramenta

#### Scenario: Multiplas ferramentas são listadas sequencialmente
- **QUANDO** Sky usa Read, depois Grep, depois Bash
- **ENTÃO** ThinkingPanel mostra 3 entradas sequenciais
- **E** ordem de execução é preservada

---

### Requirement: Contador de ferramentas usadas na sessão

O sistema SHALL exibir contador de quantas ferramentas foram usadas na resposta atual.

#### Scenario: Header mostra contagem de ferramentas
- **QUANDO** ferramentas são usadas na resposta
- **ENTÃO** header exibe "3 tools" ou similar
- **E** contagem é atualizada em tempo real

#### Scenario: Contagem é resetada a cada novo Turn
- **QUANDO** novo Turn começa
- **ENTÃO** contagem de ferramentas começa de zero
- **E** apenas ferramentas do Turn atual são contadas

---

### Requirement: Botões de ação em ToolFeedback

O sistema SHALL fornecer botões para interagir com entradas de ferramenta no ThinkingPanel.

#### Scenario: Botão collapse/expand
- **QUANDO** ThinkingPanel está expandido
- **ENTÃO** botão [▼] permite colapsar
- **QUANDO** ThinkingPanel está colapsado
- **ENTÃO** botão [▶] permite expandir

#### Scenario: Botão close remove ThinkingPanel
- **QUANDO** botão [✕] é clicado
- **ENTÃO** ThinkingPanel é removido do Turn
- **E** resposta da Sky permanece visível

---

### Requirement: Animação de status durante execução de ferramenta

O sistema SHALL mostrar animação visual enquanto ferramenta está sendo executada.

#### Scenario: Spinner durante execução
- **QUANDO** ferramenta está rodando
- **ENTÃO** spinner ou dots animados são exibidos
- **E** animação para quando ferramenta completa

#### Scenario: Barra de progresso para ferramentas longas
- **QUANDO** ferramenta demora mais de 3 segundos
- **ENTÃO** barra de progresso ou indicador de tempo é mostrado
- **E** tempo decorrido é exibido (ex: "2.3s")

---

### Requirement: Cores indicam status da ferramenta

O sistema SHALL usar cores distintas para indicar diferentes estados de ferramenta.

#### Scenario: Cores seguem paleta do Textual
- **QUANDO** ferramenta está pendente (antes de executar)
- **ENTÃO** cor $warning ou similar é usada
- **QUANDO** ferramenta está em execução
- **ENTÃO** cor $accent ou similar é usada
- **QUANDO** ferramenta completou com sucesso
- **ENTÃO** cor $success ou similar é usada
- **QUANDO** ferramenta falhou
- **ENTÃO** cor $error é usada

---

> "Ferramentas são os braços da IA; mostre-as em ação" – made by Sky 🚀
