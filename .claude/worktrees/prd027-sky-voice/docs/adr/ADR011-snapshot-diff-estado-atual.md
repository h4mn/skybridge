---
status: emendado
data: 2025-12-27
superseded-by: ADR015-adotar-snapshot-como-serviço-plataforma
---

# ADR-011 — Adoção de Snapshot/Diff para Visão do Estado Atual

> **Nota:** Esta ADR foi emendada pela [ADR015 — Adoção de Snapshot como Serviço de Observabilidade Estrutural da Plataforma](./ADR015-adotar-snapshot-como-serviço-plataforma.md), que eleva o conceito de snapshot/diff para serviço transversal da plataforma. O conteúdo original é mantido para fins históricos.

## Contexto

Durante o desenvolvimento da Skybridge, identificamos a necessidade de capturar visões momentâneas do estado do repositório para:

1. **Discovery automatizado** (PRD000, ADR000): Mapear fragmentos espalhados em `B:\_repositorios` sem leitura profunda prematura
2. **Análise de evolução**: Comparar estados em diferentes momentos para entender mudanças estruturais
3. **Estudos comparativos**: Avaliar diferentes implementações/entidades lado a lado

A ferramenta **Pyro Snapshot** (`B:\_repositorios\pyro`) já foi desenvolvida e validada para esse propósito, gerando:

- **Snapshots**: Visões momentâneas em JSON + Markdown (estrutura de diretórios, metadados, arquivos)
- **Diffs**: Relatórios comparativos entre snapshots (mesmo projeto em tempos diferentes ou projetos diferentes)

### Diagrama de Causa (Ishikawa)

```
                            ┌─────────────────────────────────┐
                            │ Dificuldade de analisar estado │
                            └────────────┬────────────────────┘
                                         │
 ┌───────────────────────┬─────────────┼───────────────────┬──────────────────────┐
 │ Ausência de visão     │ Análise     │ Evolução         │ Comparações         │
 │ clara do estado       │ manual      │ temporal         │ complexas           │
 ├───────────────────────┼─────────────┼───────────────────┼──────────────────────┤
 │ Leitura profunda      │ Leitura     │ Sem histórico    │ Diffs manuais       │
 │ prematura            │ arquivo por │ organizado       │ propensos a erro    │
 │ Alto custo cognitivo │ arquivo     │ Mudanças         │ Falta de padrão    │
 │ Ruído do monolito    │            │ perdidas         │ na comparação       │
 └───────────────────────┴─────────────┴───────────────────┴──────────────────────┘
```

## Decisão

Adotar **snapshot como visão momentânea do estado atual** e **diff como ferramenta de comparação** como padrão para:

1. **Discovery automatizado** (especialmente para ADR000)
2. **Análise de evolução temporal** do código
3. **Estudos comparativos** entre entidades/implementações
4. **Base para decisões de refatoração/unificação**

### Definições

**Snapshot**: Visão momentânea e imutável do estado de um diretório em um ponto no tempo, contendo:
- Metadados (timestamp, path, total de arquivos/dirs, tamanho, git hash/branch)
- Estrutura hierárquica de diretórios (até profundidade configurada)
- Lista de arquivos com metadados (nome, path, tamanho, modificação)

**Diff**: Relatório comparativo entre dois snapshots, identificando:
- Arquivos adicionados/removidos/movidos
- Mudanças em métricas (tamanho, contagem)
- Evolução estrutural (novos diretórios, reorganizações)

### Propriedades Fundamentais

1. **Imutabilidade**: Snapshot nunca muda após criado
2. **Temporalidade**: Cada snapshot tem timestamp único
3. **Comparabilidade**: Snapshots são comparáveis entre si
4. **Reprodutibilidade**: Mesmo parâmetros = snapshot equivalente
5. **Leveza**: Sem conteúdo de arquivos, apenas metadados estruturais

### Formato de Saída

**Snapshot (JSON)** - Processamento automatizado:
```json
{
  "metadata": {
    "timestamp": "2025-12-22T15:32:37.969323",
    "path": "B:\\_repositorios",
    "total_files": 5472,
    "total_dirs": 2432,
    "total_size": 1820000000,
    "git_hash": "abc123",
    "git_branch": "main"
  },
  "structure": {"children": [...]},
  "files": [...],
  "dirs": [...]
}
```

**Snapshot (Markdown)** - Leitura humana:
```markdown
# Snapshot - B:\_repositorios

**Gerado em:** 2025-12-22T15:32:37.969323

## 📊 Estatísticas
- 📁 **Diretórios:** 2432
- 📄 **Arquivos:** 5472
- 📦 **Tamanho total:** 1.7 GB
```

**Diff (Markdown)** - Análise comparativa:
```markdown
# 🔄 Relatório Comparativo

### 📂 Projetos Comparados
- **Projeto A:** skybridge (2025-12-22T15:32:37)
- **Projeto B:** sky-bridge (2025-12-22T15:30:00)

### 📊 Métricas
| Métrica | Projeto A | Projeto B | Diferença |
|---------|-----------|-----------|-----------|
| 📄 Arquivos | 5472 | 123 | -5349 |
| 📁 Diretórios | 2432 | 45 | -2387 |
```

### Uso no Contexto Skybridge

#### 1. Discovery Automatizado (ADR000)

```bash
# Gerar snapshot filtrado (.py, .md) até profundidade 5
python -m src.snapshot.cli get B:\_repositorios\skybridge \
  --include-extensions .py .md \
  --depth 5

# Resultado usado como base para scoring de entidades
```

#### 2. Evolução Temporal

```bash
# Snapshot antes de uma feature
snap get . --include-extensions .py

# Trabalho na feature...

# Snapshot depois da feature
snap get . --include-extensions .py

# Comparar evolução
snap diff --old antes --new depois
```

#### 3. Comparação de Entidades

```bash
# Snapshot de cada entidade candidata
snap get B:\_repositorios\skybridge
snap get B:\_repositorios\sky-bridge
snap get B:\_repositorios\Skybridge_2

# Diff para identificar sobreposições/gaps
snap diff --old skybridge --new sky-bridge
```

### Integração com Versionamento (ADR012)

Snapshots e diffs suportam a estratégia de versionamento:

- **Timestamps** vinculam snapshots a versões do código
- **Changelogs** podem incluir diffs estruturais entre versões
- **Tags Git** podem ser automaticamente snapshotados (hook)

```bash
# Auto-snapshot em commits (feature do Pyro)
python -m src.snapshot.cli git --git-action setup

# Changelog com diffs
python -m src.snapshot.cli git --git-action changelog --from v0.1.0 --to v0.2.0
```

### Localização dos Snapshots

```
B:\_repositorios\pyro\src\snapshot\
├── snapshots/          # Visões momentâneas (.json + .md)
│   ├── _repositorios_2025-12-22-15-32.json
│   └── _repositorios_2025-12-22-15-32.md
└── diffs/              # Relatórios comparativos (.md)
    ├── diff_v1_to_v2_2025-12-22-16-00.md
    └── cross_project_sky_vs_bridge_2025-12-22-16-30.md
```

## Consequências

### Positivas

* **Visibilidade sem ruído**: Estado estrutural sem ler conteúdo dos arquivos
* **Análise temporal**: Histórico de evolução do código
* **Comparação objetiva**: Diffs padronizados entre projetos/versões
* **Base para decisões**: Evidências concretas para ADRs de unificação/refatoração
* **Ferramenta validada**: Pyro Snapshot já operacional
* **Custo zero**: Sem necessidade de novas ferramentas

### Negativas / Riscos

* **Armazenamento**: Acúmulo de snapshots ao longo do tempo
* **Manutenção**: Necessário política de limpeza/rotação de snapshots antigos
* **Falso sentido de completude**: Snapshot não substitui análise de conteúdo profunda

## Próximos Passos

1. [ ] Documentar política de retenção de snapshots (ex: 30 dias)
2. [ ] Configurar auto-snapshot em tags/releases (Git hook)
3. [ ] Integrar diffs no CHANGELOG.md gerado automaticamente
4. [ ] Criar playbook específico para uso de snapshot/diff no discovery

## Dependências

- **ADR012** (Estratégia de Versionamento): Snapshots são vinculados a versões
- **PRD000** (Discovery via Snapshot): Define o processo de descoberta automatizada
- **ADR000** (Descoberta via Score): Usa snapshots como base para scoring

## Referências

- [Pyro Snapshot Tool](B:\_repositorios\pyro\README_SNAPSHOT.md)
- [PRD000 - Discovery Skybridge (Snapshot + Score)](B:\_repositorios\skybridge\docs\prd\PRD000-Discovery_Skybridge__Snapshot___Score_.md)
- [PB000 - Discovery via Snapshot + Scoring](B:\_repositorios\skybridge\docs\playbook\PB000-Discovery_da_Skybridge_via_Snapshot___Scoring.md)
- [ADR012 - Estratégia de Versionamento](B:\_repositorios\skybridge\docs\adr\ADR012-estrategia-versionamento.md)

---

> "A visão momentânea é a base para entender evolução." – made by Sky 📸

---

## Evolução

Esta ADR foi evoluída para **[ADR015 — Adoção de Snapshot como Serviço de Observabilidade Estrutural da Plataforma](./ADR015-adotar-snapshot-como-serviço-plataforma.md)**, que:

- Eleva snapshot/diff de ferramenta de domínio para **serviço transversal da plataforma**
- Define estrutura padrão em `platform/observability/snapshot`
- Estabelece contrato RPC unificado via Sky-RPC v0.3
- Permite observação estrutural de múltiplos domínios (fileops, tasks, health)

Para implementação atual, consulte **[SPEC007 — Snapshot Service](../spec/SPEC007-Snapshot-Service.md)**.
