---
status: aprovado
data: 2025-12-28
supersedes: ADR011-snapshot-diff-estado-atual
responsavel: arquitetura.skybridge
---

# ADR015 — Adoção de Snapshot/Diff como Serviço de Observabilidade Estrutural da Plataforma

## Contexto

O ADR011 definiu o uso de **snapshot/diff** como mecanismo de visão momentânea do estado de repositórios e projetos no contexto da **Skybridge**, principalmente voltado para discovery automatizado e comparações estruturais.

Com a evolução da arquitetura e da Sky-RPC, o conceito amadureceu: snapshots e diffs deixaram de ser artefatos de um único domínio (fileops/Skybridge) para se tornarem uma **capacidade transversal de observação de estado** — útil para qualquer domínio ou serviço da plataforma.

A necessidade de **observar estruturas e evoluções em diferentes contextos (código, tarefas, métricas, saúde do sistema)** levou à elevação do snapshot/diff à categoria de **serviço de observabilidade estrutural** dentro da camada de plataforma.

---

## Decisão

O módulo de **Snapshot/Diff** passa a ser tratado como um **serviço da plataforma**, alocado sob `platform/observability/snapshot`, com responsabilidade de:

1. **Capturar visões momentâneas de estado (snapshot)** em qualquer domínio observável
2. **Gerar comparações estruturais (diff)** entre snapshots de diferentes momentos ou contextos
3. **Oferecer API unificada (via Sky-RPC)** para captura e diffs em domínios distintos
4. **Manter persistência, versionamento e retenção dos artefatos estruturais**

---

## Arquitetura

### 📁 Estrutura proposta

```plaintext
platform/
└── observability/
    └── snapshot/
        ├── capture.py          # captura genérica de estado
        ├── diff.py             # comparação universal
        ├── registry.py         # registro de extratores por domínio
        ├── adapters/
        │   ├── fileops_extractor.py
        │   ├── task_extractor.py
        │   └── health_extractor.py
        └── rpc/
            ├── capture_rpc.py
            └── diff_rpc.py
```

Cada domínio (ex: `fileops`, `task`, `health`) registra um **extrator de estado** — responsável por descrever como capturar sua visão estrutural.
O snapshot não conhece a semântica dos domínios; apenas executa os extratores e formata os resultados.

---

## Integração via Sky-RPC

Exemplo de requisições padronizadas:

### Captura de snapshot

```json
{
  "context": "snapshot.capture",
  "subject": "fileops",
  "action": "capture",
  "payload": {
    "path": "B:\\_repositorios",
    "depth": 5,
    "include": [".py", ".md"]
  }
}
```

### Comparação de snapshots

```json
{
  "context": "snapshot.compare",
  "subject": "task",
  "action": "compare",
  "payload": {
    "old": "snapshot_2025-12-22",
    "new": "snapshot_2025-12-27"
  }
}
```

---

## Propriedades Fundamentais

1. **Transversalidade** — Aplicável a qualquer domínio observável
2. **Imutabilidade** — Snapshots nunca são alterados após criação
3. **Comparabilidade** — Snapshots podem ser comparados entre si
4. **Reprodutibilidade** — Parâmetros iguais = snapshot idêntico
5. **Temporalidade** — Cada snapshot tem timestamp único
6. **Leveza** — Captura estrutural, sem conteúdo dos arquivos
7. **Desacoplamento** — Nenhum domínio depende diretamente de outro para observação

---

## Consequências

### Positivas

* **Observabilidade estrutural unificada** (estado de arquivos, tarefas, serviços)
* **Reuso e padronização** de formatos de snapshot/diff (JSON/Markdown)
* **Histórico evolutivo confiável** para auditoria e decisão técnica
* **Integração simples via RPC**, sem acoplamento de domínios
* **Suporte nativo** a múltiplas camadas da plataforma

### Negativas / Riscos

* **Crescimento de armazenamento** com o tempo → exige política de retenção
* **Possibilidade de snapshots redundantes** → requer deduplicação
* **Custo de manutenção** de extratores multi-domínio
* **Confusão conceitual inicial** (migração de ADR011)

---

## Ações e Próximos Passos

1. [x] Atualizar ADR011 para status `emendado` (referenciando este ADR) ✅
2. [ ] Migrar código existente de `domain.fileops` para `platform/observability/snapshot`
3. [ ] Implementar `snapshot.registry` para extratores de domínio
4. [x] Publicar contrato RPC unificado (`snapshot.capture`, `snapshot.compare`) → **[SPEC007 — Snapshot Service](../spec/SPEC007-Snapshot-Service.md)** ✅
5. [ ] Definir política de retenção e versionamento de snapshots (por idade, hash ou tag)
6. [ ] Integrar auto-snapshot em hooks de eventos da plataforma (git, deploy, health-checks)

---

## Dependências

* **ADR010** — Adoção do Sky-RPC
* **ADR012** — Estratégia de Versionamento
* **ADR011** — Contexto original (visão de estado atual) — agora emendado
* **PRD000** — Discovery automatizado via snapshot

---

## Referências

* [ADR011 - Snapshot/Diff como visão do estado atual (emendado)](./ADR011-snapshot-diff-estado-atual.md)
* [ADR012 - Estratégia de Versionamento](./ADR012-estrategia-versionamento.md)
* [SPEC007 - Snapshot Service](../spec/SPEC007-Snapshot-Service.md) — Contrato RPC e especificação técnica
* [PRD000 - Discovery automatizado via snapshot](../prd/PRD000-Discovery_Skybridge__Snapshot___Score_.md)
* [Pyro Snapshot Tool](B:\_repositorios\pyro\README_SNAPSHOT.md)

---

> "O observador se torna parte da plataforma quando sua visão alcança todos os domínios."
> — made by Sky 👁️✨
