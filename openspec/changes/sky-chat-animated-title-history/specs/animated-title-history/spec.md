# Spec: AnimatedTitleHistory

Capability: Histórico sequencial de títulos animados durante a sessão de chat com diálogo modal para visualização completa.

## ADDED Requirements

### Requirement: Sistema deve acumular todos os títulos animados durante a sessão

O sistema SHALL manter uma estrutura de dados (`TitleHistory`) que acumula cada `EstadoLLM` exibido no `AnimatedTitle` na ordem cronológica em que ocorrem, incluindo timestamp de início e fim de cada estado.

#### Scenario: Título é adicionado ao histórico ao ser exibido
- **GIVEN** uma sessão de chat ativa
- **WHEN** `AnimatedTitle.update_estado()` é chamado com um novo `EstadoLLM`
- **THEN** o estado é adicionado ao `TitleHistory` com timestamp de início
- **AND** o estado anterior é atualizado com timestamp de fim

#### Scenario: Histórico preserva todos os estados da sessão
- **GIVEN** uma sessão com múltiplos turnos
- **WHEN** o usuário consulta o histórico
- **THEN** todos os estados exibidos estão presentes em ordem cronológica
- **AND** cada entrada tem verbo, predicado, certeza, esforço, emoção, direção
- **AND** cada entrada tem timestamp de início e fim

---

### Requirement: Clique no AnimatedTitle deve exibir diálogo modal com histórico completo

O sistema SHALL detectar cliques em qualquer parte do `AnimatedTitle` (sujeito, verbo ou predicado) e exibir um diálogo modal com TODOS os estados acumulados na sessão, com barra de rolagem se necessário.

**NOTA**: O histórico é alimentado automaticamente pelo Item 1 — o clique serve APENAS para exibir, NÃO para adicionar entradas.

#### Scenario: Clique exibe diálogo com todos os títulos
- **GIVEN** um `AnimatedTitle` visível com histórico de 15 estados acumulados
- **WHEN** o usuário clica em qualquer parte do `AnimatedTitle`
- **THEN** um diálogo modal é exibido centralizado na tela
- **AND** todos os 15 estados estão visíveis em ordem cronológica (mais recente no topo)
- **AND** barra de rolagem está disponível quando necessário
- **AND** cada entrada mostra verbo + predicado + timestamp

#### Scenario: Diálogo tem título "Histórico da Sessão"
- **GIVEN** o diálogo de histórico aberto
- **WHEN** o usuário visualiza o diálogo
- **THEN** o título "Histórico da Sessão" é exibido no cabeçalho
- **AND** um botão de fechar ("X" ou "Fechar") está disponível
- **AND** tecla Escape fecha o diálogo

#### Scenario: Diálogo pode ser fechado por clique fora
- **GIVEN** o diálogo de histórico aberto
- **WHEN** o usuário clica fora da área do diálogo
- **THEN** o diálogo é fechado

---

### Requirement: Hover sobre TitleStatic deve exibir tooltip com resumo dos últimos 5

O sistema SHALL detectar quando o mouse passa sobre os widgets `TitleStatic` (sujeito e predicado) e exibir um resumo compacto dos últimos 5 títulos como tooltip nativo do Textual.

#### Scenario: Hover no sujeito mostra resumo dos últimos 5
- **GIVEN** um `AnimatedTitle` visível com histórico de 10 estados acumulados
- **WHEN** o usuário passa o mouse sobre o `TitleStatic` do sujeito
- **THEN** um tooltip nativo é exibido com as últimas 5 entradas do histórico
- **AND** o formato é compacto: "Sky esteve: analisando → codando → testando → refletindo → concluindo"

#### Scenario: Hover no predicado mostra resumo dos últimos 5
- **GIVEN** um `AnimatedTitle` visível com histórico de 10 estados acumulados
- **WHEN** o usuário passa o mouse sobre o `TitleStatic` do predicado
- **THEN** um tooltip nativo é exibido com as últimas 5 entradas do histórico
- **AND** o formato é compacto

---

### Requirement: Hover sobre AnimatedVerb deve manter comportamento atual

O sistema SHALL preservar o comportamento existente de tooltip no widget `AnimatedVerb` — hover sobre o verbo animado exibe o estado interno atual (`_tooltip_estado`), não o histórico.

#### Scenario: Hover no verbo animado mostra estado interno
- **GIVEN** um `AnimatedVerb` com estado ativo
- **WHEN** o usuário passa o mouse sobre o verbo animado
- **THEN** o tooltip mostra certeza, esforço, emoção e direção do estado ATUAL
- **AND** o histórico NÃO é exibido
- **AND** o texto "clique para detalhes" é mantido (abriria o histórico, não o EstadoModal anterior)

---

### Requirement: Diálogo de histórico deve ter visualização expandível

O sistema SHALL permitir que o usuário expanda cada entrada do diálogo para ver detalhes completos do `EstadoLLM` (certeza, esforço, emoção, direção, duração).

#### Scenario: Entrada expandida mostra detalhes completos
- **GIVEN** o diálogo de histórico aberto
- **WHEN** o usuário clica em uma entrada do histórico
- **THEN** a entrada é expandida para mostrar todos os campos do `EstadoLLM`
- **AND** certeza é exibida como barra de progresso + porcentagem
- **AND** esforço é exibido como barra de progresso + porcentagem
- **AND** emoção é exibida com emoji + descrição
- **AND** direção é exibida como "→ avançando" ou "← revisando"
- **AND** duração (fim - início) é exibida em formato humanizado (ex: "2m 34s")

#### Scenario: Entrada recolhida oculta detalhes
- **GIVEN** uma entrada expandida no diálogo
- **WHEN** o usuário clica novamente na entrada
- **THEN** a entrada é recolhida para o formato compacto

---

### Requirement: Sistema deve gerar resumo de sessão ao final

O sistema SHALL fornecer um método para gerar um resumo da sessão baseado no histórico acumulado: tempo total por tipo de atividade (emoção), contagem de mudanças de direção, estados mais frequentes.

#### Scenario: Resumo é gerado ao final da sessão
- **GIVEN** uma sessão com histórico de 20 estados
- **WHEN** `TitleHistory.gerar_resumo()` é chamado
- **THEN** um dicionário é retornado com:
  - tempo_total por emoção (ex: `{"pensando": 180, "codando": 300, ...}`)
  - contagem_revisoes (número de estados com direcao=-1)
  - top_estados (lista dos 3 estados mais frequentes)
  - tempo_total_sessao (soma de todas as durações)

#### Scenario: Resumo pode ser usado para SessionSummary
- **GIVEN** um resumo gerado por `TitleHistory`
- **WHEN** o `SessionSummaryScreen` é exibido ao final da sessão
- **THEN** o resumo é incorporado ao sumário da sessão
- **AND** tempo por atividade é exibido visualmente
