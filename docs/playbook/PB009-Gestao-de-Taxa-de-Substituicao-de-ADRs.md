---
status: Ativo
versão: 1.0.0
data: 2025-12-28
---

# PB009 — Gestão de Taxa de Substituição de ADRs

## Contexto

A taxa de substituição de ADRs (Architecture Decision Records) é um indicador de saúde da governança arquitetural. ADRs substituídos indicam aprendizado e correção de curso, mas taxas muito altas ou muito baixas podem sinalizar problemas.

**Fórmula:**
```
Taxa de Substituição = (ADRs substituídos / Total de ADRs) × 100
```

---

## Níveis de Indicação

| Taxa | Classificação | Sinal | Cor de Alerta |
|------|---------------|-------|---------------|
| **0-3%** | Estagnação | Pouca evolução, risco de decisões obsoletas | 🟡 |
| **4-10%** | Evolução normal | Saudável, aprendizado e adaptação | 🟢 |
| **11-20%** | Alta volatilidade | Indecisão ou requisitos instáveis | 🟠 |
| **20%+** | Caos governamental | Requer revisão urgente do processo | 🔴 |

---

## Ações por Nível

### 0-3%: Estagnação 🟡

**Sintomas:**
- ADRs antigos sem revisão
- Decisões desalinhadas com a realidade atual
- Equipe evita revisar ou atualizar decisões

**Ações Imediatas:**
1. **Auditoria de relevância**: Revisar ADRs com >6 meses
2. **Check de alinhamento**: Verificar se código reflete as decisões
3. **Forçar revisões**: Estabelecer revisão periódica (ex: trimestral)

**Ações de Médio Prazo:**
- Criar ritual de "Decision Health Check" em retrospectivas
- Incentivar atualizações de ADRs quando o código evolui
- Documentar quando um ADR é confirmado (não substituído)

**Perguntas de Reflexão:**
- Estamos presos em decisões obsoletas por medo de mudar?
- Há barreiras culturais para questionar decisões passadas?
- Os ADRs estão sendo consultados ou apenas arquivados?

---

### 4-10%: Evolução Normal 🟢

**Sintomas:**
- Substituições ocasionais com justificativa clara
- Documentação de supersession bem feita
- ADRs substituídos têm histórico preservado

**Ações de Manutenção:**
1. **Continuar monitoramento**: Calcular taxa a cada novo ADR
2. **Celebrar correções**: Reconhecer publicamente quando o time corrige curso
3. **Documentar aprendizado**: Adicionar seção "Por que foi substituído" em ADRs

**Boas Práticas:**
- Sempre manter ADR substituído no repositório (nunca deletar)
- Usar campo `supersedes:` no frontmatter para rastrear
- Adicionar sumário de mudanças no novo ADR

**Exemplo de documentação de supersession:**
```yaml
---
status: aceito
data: 2025-12-28
supersedes: ADR004-adotar-json-rpc-contrato-canonico.md
---
```

---

### 11-20%: Alta Volatilidade 🟠

**Sintomas:**
- Múltiplos ADRs substituídos em curto período
- Decisões revertidas após pouco tempo
- Confusão sobre qual ADR é a fonte atual

**Ações Imediatas:**
1. **Pausa em novas decisões**: Congelar novos ADRs até análise
2. **Root cause analysis**: Investigar por que as decisões não estão se sustentando
3. **Comunicação clara**: Publicar estado atual das decisões para a equipe

**Investigação (Root Cause):**
- **Requisitos instáveis?** O produto/mundo externo está mudando muito rápido?
- **Falta de pesquisa?** Decisões estão sendo tomadas sem análise suficiente?
- **Pressão por velocidade?** ADRs estão sendo criados para "justificar" decisões já tomadas?
- **Mudança de liderança?** Novas pessoas derrubando decisões anteriores por preferência pessoal, não por causa técnica?

**Ações Corretivas:**
| Causa Raiz | Ação Corretiva |
|------------|----------------|
| Requisitos instáveis | Adotar abordagem experimental (ADR provisório) antes de consolidar |
| Falta de pesquisa | Exigir evidências antes de aprovar ADR (POCs, testes) |
| Pressão por velocidade | Separar "decisões técnicas" de "experimentos rápidos" |
- ADR004 → ADR010: JSON-RPC substituído por Sky-RPC (justificado: limitações técnicas descobertas na prática)
- ADR001 → ADR002: Evolução de discovery para estrutura (justificado: aprendizado do domínio)

**Ações de Medium Prazo:**
- Reforçar critérios de aprovação de ADRs
- Criar ritual de "Decision Review" antes de consolidar
- Considerar "ADR provisório" para decisões experimentais

---

### 20%+: Caos Governamental 🔴

**Sintomas:**
- Taxa de substituição igual ou superior a 20%
- Equipe não sabe mais qual é a fonte de verdade
- Desconfiança nas decisões arquiteturais
- ADRs ignorados em prática

**Ações de Emergência:**
1. **Parar tudo**: Congelar novos ADRs imediatamente
2. **Comunicação transparente**: Reconhecer o problema publicamente
3. **Task force de governança**: Nomear grupo para revisar processo

**Reestruturação do Processo:**
- Revisar quem pode aprovar ADRs (talvez esteja muito fácil)
- Exigir evidências obrigatórias (POCs, análise de alternativas)
- Criar "período de estabilidade" antes de substituir um ADR (ex: 30 dias mínimo)
- Considerar "Decision Gates" para ADRs de alto impacto

**Reconstrução de Confiança:**
- Realizar "Decision Audit" externo ou por terceiros
- Criar visibilidade de quais decisões estão sendo seguidas na prática
- Celebrar ADRs que se mantêm estáveis por longo período

**Exemplo de critérios de aprovação mais rigorosos:**
```yaml
# Requisitos para ADR de alto impacto
impacto: alto
evidencias_obrigatorias:
  - POC ou prova técnica
  - Análise de alternativas (mínimo 3)
  - Revisão por peer sênior
  - Avaliação de risco de rollback
periodo_estabilidade: 30 dias antes de substituir
```

---

## Métricas Complementares

A taxa de substituição não deve ser analisada isoladamente. Complementar com:

| Métrica | Como calcular | O que indica |
|---------|---------------|--------------|
| **Idade média dos ADRs** | Média de idade dos ADRs ativos | Maturidade das decisões |
| **Taxa de ADRs propostos** | Propostos / Total | Gargalo de decisão |
| **Tempo até substituição** | Tempo entre criação e supersession | Qualidade da decisão original |
| **ADRs por domínio** | Distribuição por contexto | Cobertura de decisões |

---

## Playbook de Resposta Rápida

### Quando a taxa subir acima de 10%:

1. **Stop**: Congelar novos ADRs
2. **Audit**: Listar todos os ADRs substituídos e motivos
3. **Analyze**: Identificar padrões (mesmo autor? mesmo domínio? mesmo tipo de decisão?)
4. **Communicate**: Compartilhar findings com a equipe
5. **Adjust**: Ajustar processo de aprovação se necessário

### Quando a taxa estiver abaixo de 3%:

1. **Review**: Agendar revisão de ADRs antigos
2. **Challenge**: Questionar se decisões ainda são válidas
3. **Update**: Atualizar ou confirmar ADRs
4. **Celebrate**: Reconhecer estabilidade quando saudável

---

## Exemplos Práticos (Skybridge)

**Taxa Atual:** 6.7% (1 de 15 ADRs substituído)

**Classificação:** Evolução normal 🟢

**ADRs Substituídos:**
| ADR | Substituído por | Motivo | Justificado? |
|-----|-----------------|--------|--------------|
| ADR004 (JSON-RPC) | ADR010 (Sky-RPC) | Limitações do envelope JSON-RPC descobertas na prática | Sim |

**Ações de Manutenção:**
- Continuar monitorando a cada novo ADR
- Documentar motivação quando substituir
- Preservar histórico de decisões anteriores

**Gatilhos de Ação:**
- 🔴 Acima de 20%: Congelar e revisar processo
- 🟠 Acima de 10%: Investigar causas raiz
- 🟢 4-10%: Manter e monitorar
- 🟡 Abaixo de 3%: Agendar revisão de ADRs antigos

---

## Referências

- [ADR000-ADR014 do Skybridge](B:\_repositorios\skybridge\docs\adr\)
- [Relatório de Auditoria v2](B:\_repositorios\skybridge\.agents\relatorio-auditoria-adrs-v2.md)
- Pattern: "Decision Records" por ThoughtWorks
- "Architecture Decision Records" por Michael Nygard

---

> "Decisões são hypotheses; substituições são aprendizados. O problema não é mudar de ideia, é mudar sem entender por quê." – made by Sky 📊
