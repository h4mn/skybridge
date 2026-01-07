# ADR001 - Evolucao do Discovery para Mapa de Funcionalidades (Skybridge)

## Status
Proposto

## Contexto
O relatorio `task000-discovery-report.md` consolidou um mapa das entidades-base da Skybridge. O proximo passo necessario nao e mais localizar, e sim entender cada entidade e extrair suas funcionalidades para orientar unificacao e estrategia.

## Decisao
Mudar o objetivo de discovery para **inventario de funcionalidades por entidade**, com classificacao por score e comparacao contra o nucleo. A saida principal passa a ser `features-report.md`, estruturado para uso em mapa de dominios/infras, blueprints e strategy ladder.

## Escopo
Dentro:
- Inventariar features por entidade (item, local, o que faz, proposito unificado, como agrega, score).
- Classificar entidades contra o nucleo provavel.
- Extrair padroes e preferencias (arquitetura, integracoes, estilo de CLI/API).
- Preparar mapa de dominios e infras, e rascunho de blueprints.

Fora:
- Unificacao de codigo.
- Decisoes finais de arquitetura.
- Refatoracoes ou migracoes.

## Consequencias
Positivas:
- Mapa funcional comparavel e reutilizavel.
- Clareza sobre o que reaproveitar e o que abandonar.
- Base objetiva para roadmap e strategy ladder.

Negativas / Trade-offs:
- Leitura de conteudo mais profunda (README/configs/codigo critico).
- Tempo adicional de analise por entidade.

## Riscos e mitigacoes
- Risco: vies pelo score de discovery.
  - Mitigacao: validar features por evidencia direta e registrar gaps.
- Risco: ruidao por entidades genericas.
  - Mitigacao: priorizar top scores e limitar escopo por entidade.

## Proximos passos
1) Executar PRD e Playbook de feature mapping.
2) Produzir `features-report.md`.
3) Consolidar padrões e candidatos a blueprints.

---
> "Mapa funcional antes de unificar." - made by Sky
