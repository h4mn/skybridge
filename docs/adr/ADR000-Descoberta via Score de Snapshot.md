---
status: aceito
data: 2025-12-22
---

# ADR-000 — Descoberta e Unificação da Skybridge via Snapshot + Scoring

## Status
Aceito

## Contexto
A Skybridge possui múltiplas tentativas de implementação espalhadas em diferentes repositórios e subpastas, incluindo um legado monolítico. A ausência de um mapa confiável impede decisões claras de unificação e retoma de desenvolvimento. É necessário um diagnóstico objetivo, com baixo ruído, que identifique núcleos reais, fragmentos reaproveitáveis e tentativas abandonadas.

## Decisão
Adotar um processo de **descoberta automatizada** usando snapshots filtrados (paths, nomes e extensões) com **cálculo de score por entidade**, para identificar implementações e fragmentos da Skybridge em `B:\_repositorios`, limitando a leitura de conteúdo a evidências essenciais e funcionalidades aproveitáveis.

**Escopo**
- Dentro: varredura até depth=5, scoring por marcadores, relatório comparativo.
- Fora: refatoração, unificação de código e decisões de arquitetura final (tratadas em ADRs posteriores).

## Opções consideradas
1) Análise manual dos repositórios  
2) Migração imediata para um novo repositório “limpo”  
3) Descoberta automatizada via snapshot + scoring (**escolhida**)

## Critérios de decisão
- Redução de ruído do monolito
- Objetividade e reprodutibilidade
- Baixo custo cognitivo e operacional
- Evidências auditáveis
- Preparação para roadmap e unificação

## Consequências
### Positivas
- Diagnóstico claro e replicável
- Ranking objetivo de candidatos
- Base sólida para unificação incremental
- Artefato reutilizável no ecossistema

### Negativas / Trade-offs
- Falsos positivos possíveis sem marcadores fortes
- Necessidade de calibrar pesos de score

### Riscos e mitigação
- **Risco:** monolito dominar resultados  
  **Mitigação:** penalização sem marcadores fortes e leitura mínima de conteúdo
- **Risco:** escopo excessivo  
  **Mitigação:** depth=5 e leitura sob demanda

## Plano / Próximos passos
1) Executar varredura em `B:\_repositorios` com filtros definidos.
2) Gerar relatório com ranking, evidências e tabela comparativa.
3) Identificar núcleo provável da Skybridge.
4) Abrir ADR(s) subsequente(s) para unificação e roadmap.

## Evidências / Referências
- `PRD000-Discovery Skybridge (Snapshot + Score).md`
- `README_SNAPSHOT.md`
- Relatórios de snapshot/diff existentes
- Data: 2025-12-22

---
> "Decisão bem registrada economiza futuro." – made by Sky ✨
