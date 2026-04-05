---
target: {sistema}
mode: white
generated_at: {timestamp}
insights_source: insights-{sistema}.md
spec_source: openspec/changes/{change-id}/
---

# Análise [WHITE] - {sistema}

## Resumo Executivo

{2-3 frases resumindo a análise estrutural e correlação com as specs Gherkin}

---

## Informações da Análise

| Campo | Valor |
|-------|-------|
| **Sistema** | {nome do sistema} |
| **Insights Source** | insights-{sistema}.md |
| **Spec Source** | `openspec/changes/{change-id}/` |
| **Data da Análise** | {timestamp} |
| **Complexidade Geral** | Simples/Média/Complexa |

---

## Arquivos Analisados

| Arquivo | Relevância | Gap/Bug Relacionado |
|---------|------------|---------------------|
| `{caminho1}` | Alta/Média/Baixa | GAP-1, BUG-2 |
| `{caminho2}` | ... | ... |

---

## Correlações

Conectando comportamento (BLACK) com implementação (WHITE):

| ID | Comportamento (BLACK) | Implementação (WHITE) | Arquivo:Linha | Status |
|----|----------------------|----------------------|---------------|--------|
| C-1 | {o que foi observado} | {código relacionado} | `file.py:42` | ✅/⚠️/❌ |
| C-2 | ... | ... | ... | ... |

### Legenda de Status

- ✅ **OK** - Comportamento corresponde à implementação
- ⚠️ **Parcial** - Comportamento parcialmente explicado
- ❌ **Anomalia** - Comportamento não corresponde (possível bug)

---

## Análise de Gaps

### GAP-1: {título}

| Campo | Valor |
|-------|-------|
| **Descrição** | {o que está faltando} |
| **Arquivo** | `{caminho}:{linha}` |
| **Causa Raiz** | {por que não existe} |
| **Solução Proposta** | {como implementar} |
| **Complexidade** | Simples/Média/Complexa |
| **Dependências** | {o que precisa antes} |

**Código Atual:**
```{linguagem}
// Trecho relevante do código atual
```

**Sugestão de Implementação:**
```{linguagem}
// Como poderia ser implementado
```

### GAP-2: {título}

...

---

## Análise de Bugs

### BUG-1: {título}

| Campo | Valor |
|-------|-------|
| **Descrição** | {o que está errado} |
| **Arquivo** | `{caminho}:{linha}` |
| **Causa Raiz** | {por que acontece} |
| **Tipo de Fix** | Direto/Refatoração/Redesign |
| **Complexidade** | Simples/Média/Complexa |
| **Risco de Regressão** | Baixo/Médio/Alto |

**Código com Bug:**
```{linguagem}
// Código atual com problema
```

**Código Corrigido:**
```{linguagem}
// Como deve ficar
```

**Teste Sugerido:**
```{linguagem}
// Teste para validar o fix
```

### BUG-2: {título}

...

---

## Recomendações de Complexidade

### Itens Simples → Code Mode Direto

| Item | Ação | Arquivo |
|------|------|---------|
| BUG-X | Fix direto | `file.py:linha` |

### Itens Médios → Backlog

| Item | Ação | Prioridade |
|------|------|------------|
| GAP-X | Criar issue/task | P1/P2/P3 |

### Itens Complexos → systematic-debugging

| Item | Motivo | Próximo Passo |
|------|--------|---------------|
| BUG-X | Multi-componente, causa não óbvia | Usar systematic-debugging |

---

## Sugestão de systematic-debugging

{Se houver bugs complexos, incluir seção:}

### BUG-X: {título} - Investigação Profunda Recomendada

🔍 **Bug complexo detectado.**

**Motivo da sugestão:**
- {razão 1}
- {razão 2}

**Componentes envolvidos:**
- `{arquivo1}`
- `{arquivo2}`

**Comando sugerido:**
```
systematic-debugging skill
Contexto: {descrição do bug}
Arquivos suspeitos: {lista}
Hipótese inicial: {se houver}
```

---

## Débitos Técnicos Identificados

| ID | Descrição | Impacto | Esforço | Prioridade |
|----|-----------|---------|---------|------------|
| TD-1 | ... | Alto/Médio/Baixo | Alto/Médio/Baixo | P1/P2/P3 |

---

## Melhorias Sugeridas

Oportunidades identificadas durante a análise:

| ID | Descrição | Benefício | Esforço |
|----|-----------|-----------|---------|
| M-1 | ... | ... | ... |

---

## Plano de Ação

### Fase 1: Fixes Críticos (Imediato)

1. [ ] {bug crítico} - `arquivo.py:linha`
2. [ ] {outro item crítico}

### Fase 2: Gaps de Funcionalidade (Curto Prazo)

1. [ ] {gap 1} - Prioridade P1
2. [ ] {gap 2} - Prioridade P2

### Fase 3: Débitos Técnicos (Médio Prazo)

1. [ ] {débito técnico 1}
2. [ ] {débito técnico 2}

### Fase 4: Melhorias (Longo Prazo)

1. [ ] {melhoria 1}
2. [ ] {melhoria 2}

---

## Handoff

### Para Code Mode

```markdown
## Fixes Prontos para Implementação

1. **BUG-X** em `arquivo.py:linha`
   - Causa: {resumo}
   - Fix: {resumo da solução}
   - Teste: {como validar}
```

### Para Backlog

```markdown
## Issues/Tasks para Criar

1. **GAP-X: {título}**
   - Tipo: feature/bug/manutencao
   - Prioridade: P1/P2/P3
   - Descrição: {resumo}
   - Arquivos: {lista}
```

### Para systematic-debugging

```markdown
## Bugs para Investigação Profunda

1. **BUG-X: {título}**
   - Motivo: {por que é complexo}
   - Arquivos: {lista}
   - Comando: systematic-debugging skill
```

---

## Metadados

| Campo | Valor |
|-------|-------|
| **Duração da Análise** | {tempo} |
| **Arquivos Analisados** | {número} |
| **Correlações Feitas** | {número} |
| **Causas Identificadas** | {número} |
| **Fixes Propostos** | {número} |
| **Pronto para** | Code Mode / Backlog / systematic-debugging |

---

> Gerado por testbox:white em {timestamp}
> Baseado em insights-{sistema}.md
