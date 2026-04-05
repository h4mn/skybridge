---
target: {sistema}
mode: black
generated_at: {timestamp}
ready_for_white: true
spec_source: {caminho para spec gherkin}
---

# Insights [BLACK] - {sistema}

## Resumo Executivo

{2-3 frases resumindo o que foi observado em comparação com as specs}

---

## Informações do Sistema

| Campo | Valor |
|-------|-------|
| **Sistema** | {nome do sistema} |
| **Interface** | {API/CLI/Discord/etc} |
| **Versão** | {se disponível} |
| **Ambiente** | {dev/staging/prod} |
| **Data da Análise** | {timestamp} |
| **Spec Source** | `openspec/changes/{change-id}/` |

---

## Specs Gherkin de Referência

| Spec | Caminho | Cenários |
|------|---------|----------|
| {nome} | `openspec/changes/{change-id}/{change-id}.feature` | {número} |

---

## Entradas Testadas (baseado em Gherkin)

| ID | Entrada | Tipo | Obrigatório | Descrição |
|----|---------|------|-------------|-----------|
| IN-1 | ... | string/number/... | Sim/Não | ... |
| IN-2 | ... | ... | ... | ... |

---

## Cenários Testados (conforme Gherkin)

### Cenário C-1: {nome do cenário}

**Source:** `openspec/changes/{change-id}/scenarios/{cenario}.feature`

| Gherkin | Esperado | Observado | Status |
|---------|----------|-----------|--------|
| Given: {pré-condição} | {esperado} | {observado} | ✅/❌/⚠️ |
| When: {ação} | {esperado} | {observado} | ✅/❌/⚠️ |
| Then: {resultado} | {esperado} | {observado} | ✅/❌/⚠️ |

### Cenário C-2: {nome do cenário}

**Source:** `openspec/changes/{change-id}/scenarios/{cenario}.feature`

| Gherkin | Esperado | Observado | Status |
|---------|----------|-----------|--------|
| ... | ... | ... | ... |

---

## Saídas Observadas

| Cenário | Saída Esperada | Saída Real | Match? | Notas |
|---------|----------------|------------|--------|-------|
| C-1 | ... | ... | ✅/❌ | ... |
| C-2 | ... | ... | ✅/❌ | ... |

---

## Gaps Identificados

Funcionalidades esperadas mas não encontradas:

| ID | Descrição | Impacto | Prioridade | Workaround |
|----|-----------|---------|------------|------------|
| GAP-1 | ... | Alto/Médio/Baixo | P1/P2/P3 | ... |
| GAP-2 | ... | ... | ... | ... |

### Detalhamento dos Gaps

#### GAP-1: {título}

- **Descrição:** {o que está faltando}
- **Impacto:** {como afeta o usuário/sistema}
- **Frequência:** {sempre/às vezes/raramente}
- **Reprodução:** {passos para reproduzir}
- **Evidência:** {logs/screenshots se houver}

---

## Bugs Encontrados

Comportamentos incorretos ou inesperados:

| ID | Descrição | Severidade | Reproduzível | Status |
|----|-----------|------------|--------------|--------|
| BUG-1 | ... | Crítico/Alto/Médio/Baixo | Sim/Não | Novo/Confirmado |
| BUG-2 | ... | ... | ... | ... |

### Detalhamento dos Bugs

#### BUG-1: {título}

- **Descrição:** {o que está errado}
- **Severidade:** {Crítico/Alto/Médio/Baixo}
- **Reprodução:**
  1. Passo 1
  2. Passo 2
  3. ...
- **Resultado Esperado:** {o que deveria acontecer}
- **Resultado Real:** {o que acontece}
- **Evidência:** {logs/screenshots}
- **Hipótese:** {possível causa}

---

## Padrões Identificados

Comportamentos consistentes observados:

| Padrão | Descrição | Consistência |
|--------|-----------|--------------|
| P1 | ... | Sempre/Frequente |
| P2 | ... | ... |

---

## Hipóteses para WHITE

Questões para investigar no modo caixa branca:

- [ ] Verificar se {X} é implementado como {Y}
- [ ] Investigar por que {Z} acontece
- [ ] Confirmar estrutura de {W}
- [ ] Entender relação entre {A} e {B}
- [ ] Validar se {C} é intencional ou bug

---

## Arquivos Suspeitos

Baseado no comportamento, prováveis arquivos envolvidos:

| Arquivo | Motivo | Confiança |
|---------|--------|-----------|
| {caminho} | {razão} | Alta/Média/Baixa |

---

## Próximos Passos

1. **Rodar modo WHITE:**
   ```
   testbox white {sistema}
   ```

2. **Arquivos para analisar:**
   - `{arquivo1}`
   - `{arquivo2}`

3. **Foco principal:**
   - {gap ou bug mais crítico}

---

## Metadados

| Campo | Valor |
|-------|-------|
| **Duração da Análise** | {tempo} |
| **Cenários Executados** | {número} |
| **Bugs Encontrados** | {número} |
| **Gaps Identificados** | {número} |
| **Pronto para WHITE** | ✅ |

---

> Gerado por testbox:black em {timestamp}
