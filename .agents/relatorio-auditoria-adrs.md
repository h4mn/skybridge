# Relatório de Auditoria Técnica — ADRs Skybridge

## A) Resumo executivo (incoerências mais críticas)
- **Definição de “Core” divergente**: ADR002 define Core como camada de domínio em `src/skybridge/core`, enquanto ADR003 define Core como o pacote principal `src/skybridge` (que inclui Kernel/Platform/Infra). Isso muda responsabilidades e acoplamentos. Evidências: `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:25`, `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:22`.
- **Dependências de plugins conflitantes**: ADR002 restringe plugins a depender do Kernel (e, quando permitido, ports do Core). ADR003 diz que plugins dependem do core (sem restringir a Kernel). Evidências: `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:33`, `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:107`.
- **Sequência/estado do discovery vs feature mapping**: ADR000 (aceito) define discovery baseado em snapshot + scoring com leitura mínima; ADR001 (proposto) exige leitura mais profunda para inventário de funcionalidades; ADR002 (aceito) pressupõe que mapeamento de capacidades já ocorreu. Isso gera um salto de estágio sem clarificação. Evidências: `docs/adr/ADR000-Descoberta via Score de Snapshot.md:10`, `docs/adr/ADR001-Feature-Map-Skybridge.md:10`, `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:9`.
- **Glossário e estrutura ainda não consolidados**: ADR003 assume vocabulário e padrões oficiais, mas termos centrais colidem com ADR002; falta um ADR de consolidação para unificar termos e dependências.
- **Risco de governança documental**: ADR002 define `docs/tasks/` como pasta canônica, mas a árvore real tem `docs/task/` (singular). Evidência de árvore: `docs/task` (path real). Isso indica desvio entre ADR e repo.

---

## B) Matriz de decisões

| ADR | Decisão | Onde (linhas) | Impacto | Confia? |
|---|---|---|---|---|
| ADR000 | Adotar discovery automatizado via snapshots + scoring com leitura mínima (implícita: prioriza evidência filtrada) | `docs/adr/ADR000-Descoberta via Score de Snapshot.md:10` | Define método de diagnóstico e evita leitura profunda prematura | Alta |
| ADR000 | Escopo do discovery não inclui unificação/refatoração/decisões finais | `docs/adr/ADR000-Descoberta via Score de Snapshot.md:13`, `docs/adr/ADR000-Descoberta via Score de Snapshot.md:14` | Evita decisões arquiteturais antes do mapa | Alta |
| ADR001 | Evoluir discovery para inventário de funcionalidades por entidade, com `features-report.md` | `docs/adr/ADR001-Feature-Map-Skybridge.md:10` | Muda a saída principal e exige leitura mais profunda | Alta |
| ADR001 | Escopo inclui extrair padrões e preparar mapa de domínios/infras (implícito: já começa arquitetura de alto nível) | `docs/adr/ADR001-Feature-Map-Skybridge.md:16`, `docs/adr/ADR001-Feature-Map-Skybridge.md:17` | Antecede decisões arquiteturais sem formalização explícita | Média |
| ADR002 | Adotar monólito modular com DDD e microkernel explícito | `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:22` | Define macroarquitetura | Alta |
| ADR002 | Separar camadas Kernel/Core/Platform/Infra com responsabilidades específicas | `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:24`, `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:25`, `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:26`, `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:27` | Define fronteiras e dependências | Alta |
| ADR002 | Apps são thin adapters e não carregam regra de negócio | `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:32` | Evita lógica fora do core | Alta |
| ADR002 | Plugins dependem somente do Kernel (e ports permitidos) | `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:33` | Limita acoplamento e define contrato de plugin | Alta |
| ADR003 | Adotar Monólito Modular + Plugins opcionais | `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:11` | Reforça macroarquitetura | Alta |
| ADR003 | CQRS na superfície com rotas `/cmd` e `/qry` | `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:49`, `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:50`, `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:51` | Define contrato externo | Alta |
| ADR003 | Event Sourcing apenas em `tasks` inicialmente | `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:55`, `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:56` | Define estratégia de persistência histórica | Alta |
| ADR003 | Core definido como pacote principal `src/skybridge` | `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:22` | Conflita com ADR002 sobre definição de Core | Alta |
| ADR003 | Plugins dependem do core; core não depende de plugins | `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:107` | Conflita com ADR002 sobre Kernel como contrato mínimo | Média |

---

## C) Lista de conflitos (priorizada)

1) **Conflito: definição de “Core” (escopo e responsabilidade)**
- **Evidências**:  
  - ADR002 define Core como camada de domínio e casos de uso dentro de `src/skybridge/core` (separada do Kernel/Platform/Infra). `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:25`  
  - ADR003 define Core como o pacote principal `src/skybridge` (englobando tudo). `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:22`
- **Impacto prático**: muda regras de dependência, fronteiras e o entendimento de “core” em todo o repo e docs.
- **Proposta de resolução**: adicionar **seção “Clarificações/Definições”** no ADR003 ou criar um **ADR de Consolidação** que fixe “Core” como camada de domínio (ADR002) e “Core Package” como termo separado (ex.: “Core Package = src/skybridge”).

2) **Conflito: dependência de plugins**
- **Evidências**:  
  - ADR002: plugins dependem somente do Kernel (e ports permitidos). `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:33`  
  - ADR003: plugins dependem do core (sem limitar a Kernel). `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:107`
- **Impacto prático**: risco de acoplamento de plugins ao domínio/internals, quebrando o “microkernel real”.
- **Proposta de resolução**: **editar ADR003** para alinhar com ADR002, ou criar **ADR de Consolidação** com regra explícita de dependências de plugins (Kernel-only + ports aprovados).

3) **Conflito/ambiguidade: fase do discovery e feature mapping**
- **Evidências**:  
  - ADR000 (aceito) prescreve discovery automatizado com leitura mínima. `docs/adr/ADR000-Descoberta via Score de Snapshot.md:10`  
  - ADR001 (proposto) exige leitura mais profunda e muda objetivo do discovery para inventário funcional. `docs/adr/ADR001-Feature-Map-Skybridge.md:10`, `docs/adr/ADR001-Feature-Map-Skybridge.md:31`  
  - ADR002 (aceito) afirma “após discovery e mapeamento de capacidades”. `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:9`
- **Impacto prático**: cronologia confusa (mapeamento já feito vs ainda proposto); pode gerar saltos de decisão sem evidência.
- **Proposta de resolução**: **novo ADR de Consolidação** ou **edit** no ADR002 para declarar dependência explícita do ADR001 (ou status do feature mapping).

4) **Conflito menor: estrutura documental**
- **Evidências**:  
  - ADR002 define `docs/tasks/` como pasta canônica. `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:107`  
  - Estrutura real do repo: `docs/task` (singular). Evidência adicional de árvore: `docs/task`.
- **Impacto prático**: confusão em governança/automação de docs.
- **Proposta de resolução**: **edit em ADR002** para refletir o path real, ou ajustar a árvore do repo conforme ADR.

---

## Tabela de Vocabulário/Definições

| Termo | ADR000 | ADR001 | ADR002 | ADR003 | Divergência? |
|---|---|---|---|---|---|
| Core | — | — | “Core: domínio e casos de uso (DDD por BC).” `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:25` | “Core: pacote principal `src/skybridge`.” `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:22` | Sim |
| Kernel | — | — | “Kernel: microkernel/SDK estável (contratos, envelope, registry).” `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:24` | — | Sim (ausente no ADR003) |
| Platform | — | — | “Platform: host/runtime (bootstrap, DI, observabilidade, plugin host).” `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:26` | — | Sim (ausente no ADR003) |
| Infra | — | — | “Infra: implementações concretas (IO, integrações).” `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:27` | — | Sim (ausente no ADR003) |
| Plugin | — | — | “Plugins dependem somente do Kernel (e ports permitidos).” `docs/adr/ADR002-Estrutura do Repositório Skybridge.md:33` | “Plugin: extensão opcional que depende do core.” `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:24` | Sim |
| Command | — | — | — | “Command: intenção de mudar estado.” `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:27` | — |
| Query | — | — | — | “Query: leitura sem side-effects.” `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:28` | — |
| Shared | — | — | — | “Shared: mecanismos transversais sem regra de negócio.” `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:25` | — |
| CQRS | — | — | — | “CQRS na superfície com /cmd e /qry.” `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:49` | — |
| Event Sourcing | — | — | — | “Event Sourcing apenas em tasks inicialmente.” `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md:55` | — |

---

## D) Recomendações finais (ordem sugerida)

1) **Quick win — corrigir definição de “Core” em ADR003**  
   - Ação: editar `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md` para diferenciar “Core (camada de domínio)” de “Core Package (src/skybridge)”.  
   - Racional: reduz ambiguidade estrutural e alinha com ADR002.

2) **Quick win — alinhar regra de dependências de plugins**  
   - Ação: editar ADR003 para afirmar: “Plugins dependem de Kernel + ports aprovados, nunca do domínio direto”.  
   - Racional: preserva microkernel real e evita acoplamento.

3) **Quick win — ajustar documentação de estrutura**  
   - Ação: corrigir referência `docs/tasks/` em ADR002 ou renomear a pasta real para bater com ADR.  
   - Racional: evita ruído em governança e automações.

4) **Ação estratégica — criar ADR de Consolidação**  
   - Sugestão: “ADR00X — Consolidação de Vocabulário e Dependências”.  
   - **Outline proposto**:
     - Objetivo: unificar termos Core/Kernel/Platform/Infra e regras de dependência.  
     - Escopo: ADR002 + ADR003 + implicações para plugins e documentação.  
     - Decisão: glossário único + regras de dependência.  
     - Consequências: impacto em docs/specs, revisão de README por pasta.  
     - Migração: ajustes mínimos em docs e checklists.

5) **Ação de processo — clarificar cronologia do discovery**  
   - Ação: editar ADR002 (contexto) para mencionar que o feature mapping ainda é “proposto” (ADR001) ou promover ADR001 para “aceito”.  
   - Racional: elimina ambiguidade de estágio e reduz risco de decisões antecipadas.
