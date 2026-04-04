# Design: Paper State Migration

## Context

### Estado Atual
O módulo `paper-trading` possui um facade `helloworld` funcional que:
- Executa ordens reais com dados de mercado (Yahoo Finance)
- Persiste estado em `paper_state.json`
- Calcula PnL marcado a mercado
- Opera via Discord MCP e API REST

### Problemas Identificados
1. **Conflito de writers** — Dois adapters escrevem no mesmo JSON:
   - `JsonFilePaperBroker` → `{saldo, ordens, posicoes}`
   - `JsonFilePortfolioRepository` → `{portfolios}`
   - Último a salvar sobrescreve silenciosamente

2. **Lógica fora do lugar** — Commands e queries vivem no helloworld:
   - `broker.enviar_ordem()` deveria ser `CriarOrdemHandler`
   - `feed.obter_cotacao()` deveria ser `ConsultarMercadoQuery`

3. **Facades incompletas** — `facade/api` e `facade/mcp` são scaffolds:
   - `dependencies.py` com `NotImplementedError`
   - Tools MCP sem implementação real

### Stakeholders
- **Usuário**: Opera paper trading via Discord
- **API REST**: Consumida por frontends externos
- **MCP**: Integração com Claude Desktop

### Constraints
- Não quebrar o helloworld durante migração
- Manter compatibilidade com `paper_state.json` v1
- Reutilizar adapters existentes (YahooFinanceFeed, PaperBroker)

---

## Goals / Non-Goals

### Goals
- ✅ Unificar ownership do `paper_state.json` em `PaperState`
- ✅ Extrair commands/queries do helloworld para `application/`
- ✅ Implementar `facade/api` com DI real conectada aos handlers
- ✅ Implementar `facade/mcp` com tools funcionais
- ✅ Schema versionado com migração automática v1 → v2

### Non-Goals
- ❌ Conversão cambial USD/BRL (backlog separado)
- ❌ Quantidades fracionadas com `Decimal` (backlog separado)
- ❌ Script standalone de monitoramento (backlog separado)
- ❌ Lógica de risco (VaR, Sharpe) — não existe em nenhum lugar ainda
- ❌ Testes de integração end-to-end (futuro)
- ❌ Remover o helloworld (permanece como sandbox)

---

## Decisions

### D1: PaperState como Dono Único do JSON

**Decisão:** Criar `PaperStatePort` + `JsonFilePaperState` como única interface para o arquivo.

**Racional:**
- Elimina risco de sobrescrita silenciosa
- Schema versionado em um único lugar
- Abre caminho para SQLite sem tocar no domínio

**Alternativas Consideradas:**
| Alternativa | Veredito |
|-------------|----------|
| Arquivos separados (broker.json + portfolios.json) | ❌ Divide estado, dificulta backup |
| Broker como dono único | ❌ Não escala para multi-portfolio |
| Resolver na hora do conflito | ❌ Conflito é determinístico |

**Estrutura:**
```
JsonFilePaperBroker   ──┐
                        ├──► PaperStatePort ──► paper_state.json
JsonFilePortfolioRepo ──┘
```

**Decisão Importante - Sem Cache em Memória:**
Durante implementação descobrimos que cache em memória causa stale reads quando múltiplas instâncias de `JsonFilePaperState` são criadas (ex: broker e repository via DI do FastAPI).

```python
# BUG (cache antigo):
broker_state = JsonFilePaperState()  # cache próprio
repo_state = JsonFilePaperState()    # cache próprio (diferente!)
# broker salva → seu cache atualiza
# repo lê → retorna cache STALE, não vê mudança do broker

# SOLUÇÃO (sem cache):
# Sempre ler do disco a cada carregar()
# Trade-off: mais I/O, mas consistência garantida
```

**Decisão Importante - Write Atômico:**
`salvar()` usa estratégia tmp + rename para evitar corrupção se o processo morrer durante a escrita:

```python
# Write atômico: tmp + rename
tmp_path = file_path.with_suffix('.tmp')
with open(tmp_path, "w") as f:
    json.dump(data, f)
tmp_path.replace(file_path)  # atômico em POSIX e Windows
```

Se o processo morrer:
- **Durante escrita do .tmp:** arquivo principal permanece íntacto
- **Durante rename:** SO garante atomicidade (ou completa ou não)

### D2: CQRS para Commands e Queries

**Decisão:** Separar operações de escrita (Commands) de leitura (Queries).

**Racional:**
- Commands: `CriarOrdemCommand`, `DepositarCommand`, `ResetarCommand`
- Queries: `ConsultarPortfolioQuery`, `ConsultarMercadoQuery`, `ConsultarOrdensQuery`
- Handlers injetáveis via DI

**Estrutura (seguindo ADR003 - handlers flat):**
```
application/
├── commands/
│   ├── criar_ordem.py
│   ├── depositar.py
│   └── resetar.py
├── queries/
│   ├── consultar_cotacao.py
│   ├── consultar_historico.py
│   ├── consultar_portfolio.py
│   └── consultar_ordens.py
└── handlers/
    ├── criar_ordem_handler.py      # Command handler
    ├── depositar_handler.py        # Command handler
    ├── resetar_handler.py          # Command handler
    ├── consultar_cotacao_handler.py    # Query handler
    ├── consultar_historico_handler.py  # Query handler
    ├── consultar_portfolio_handler.py  # Query handler (existente)
    └── consultar_ordens_handler.py     # Query handler
```

> **Nota:** Handlers ficam em `application/handlers/` flat (ADR003), não em subpastas por tipo.

### D3: Schema Versionado com Migração

**Decisão:** Schema v2 unificado com migração automática de v1.

**Schema v2:**
```json
{
  "version": 2,
  "updated_at": "2026-03-27T20:00:00Z",
  "saldo": 95158.0,
  "saldo_inicial": 100000.0,
  "ordens": {},
  "posicoes": {},
  "portfolios": {}
}
```

**Migração:**
- Detecta `version` ausente ou `1` → migra para v2
- Backup automático: `paper_state.json.v1.bak`
- Merge de schemas: preserva dados de broker E repository

### D4: DI via FastAPI Depends

**Decisão:** Usar `dependencies.py` com funções factory injetáveis.

**Padrão:**
```python
# facade/api/dependencies.py
def get_paper_state() -> PaperStatePort:
    return JsonFilePaperState()

def get_broker(state: PaperStatePort = Depends(get_paper_state)) -> BrokerPort:
    return JsonFilePaperBroker(state)

def get_feed() -> DataFeedPort:
    return YahooFinanceFeed()
```

### D5: helloworld como Consumidor, não Dono

**Decisão:** helloworld importa handlers de `application/`, não chama broker diretamente.

**Antes:**
```
helloworld ──► broker.enviar_ordem() (direto)
```

**Depois:**
```
helloworld ──► CriarOrdemHandler ──► broker
facade/api ──► CriarOrdemHandler ──► broker  (mesmo handler)
facade/mcp ──► CriarOrdemHandler ──► broker  (mesmo handler)
```

---

## Risks / Trade-offs

### R1: Breaking Change no Schema
**Risco:** Usuários com `paper_state.json` v1 podem perder dados.
**Mitigação:**
- Backup automático antes de migrar
- Migração preserva todos os campos de v1
- Log de migração para auditoria

### R2: Regressão no helloworld
**Risco:** Refatoração pode quebrar funcionalidade existente.
**Mitigação:**
- Migração incremental por fase
- Cada fase termina com helloworld funcionando
- Testes manuais de smoke test

### R3: Complexidade de DI
**Risco:** DI adiciona camada de indireção.
**Mitigação:**
- Factory functions simples (sem containers)
- Dependencies explícitas em cada handler
- Documentação clara em cada facade

### R4: Performance de I/O
**Risco:** PaperState centraliza I/O, pode virar gargalo.
**Mitigação:**
- Cache em memória com write-through
- Batch writes quando possível
- Futuro: migração para SQLite resolve

---

## Migration Plan

### Fase 1: PaperState (pré-requisito)
**Duração:** ~2h | **Artefatos:** 5

| Tarefa | Arquivo | Ação |
|--------|---------|------|
| Criar PaperStatePort | `ports/paper_state_port.py` | NOVO |
| Criar PaperStateData | `domain/paper_state.py` | NOVO |
| Criar JsonFilePaperState | `adapters/persistence/json_file_paper_state.py` | NOVO |
| Refatorar JsonFilePaperBroker | `adapters/brokers/json_file_broker.py` | DELEGAR |
| Refatorar JsonFilePortfolioRepository | `adapters/persistence/json_file_repository.py` | DELEGAR |

**Critério de Pronto:**
- [ ] Testes unitários PaperState passando
- [ ] helloworld sobe sem erros
- [ ] `paper_state.json` tem schema v2

### Fase 2: Commands e Queries
**Duração:** ~2h | **Artefatos:** 6

| Tarefa | Arquivo | Ação |
|--------|---------|------|
| Criar CriarOrdemCommand | `application/commands/criar_ordem.py` | NOVO |
| Criar CriarOrdemHandler | `application/handlers/criar_ordem_handler.py` | NOVO |
| Criar ConsultarMercadoQuery | `application/queries/consultar_mercado.py` | NOVO |
| Criar ConsultarMercadoHandler | `application/handlers/consultar_mercado_handler.py` | NOVO |
| Expandir ConsultarPortfolioQuery | `application/queries/consultar_portfolio.py` | EXPANDIR |
| Criar ConsultarOrdensQuery | `application/queries/consultar_ordens.py` | NOVO |

**Critério de Pronto:**
- [ ] helloworld funciona identicamente ao atual
- [ ] Handlers têm testes unitários
- [ ] `application/commands/` não está vazio

### Fase 3: facade/api
**Duração:** ~3h | **Artefatos:** 4

| Tarefa | Arquivo | Ação |
|--------|---------|------|
| Implementar dependencies.py | `facade/api/dependencies.py` | IMPLEMENTAR |
| Criar routes/mercado.py | `facade/api/routes/mercado.py` | NOVO |
| Implementar routes/ordens.py | `facade/api/routes/ordens.py` | IMPLEMENTAR |
| Implementar routes/portfolio.py | `facade/api/routes/portfolio.py` | IMPLEMENTAR |

**Critério de Pronto:**
- [ ] `facade/api` sobe sem `NotImplementedError`
- [ ] Swagger documentado
- [ ] Mesmos resultados que helloworld

### Fase 4: facade/mcp
**Duração:** ~2h | **Artefatos:** 3

| Tarefa | Arquivo | Ação |
|--------|---------|------|
| Implementar CriarOrdemTool | `facade/mcp/tools/criar_ordem_tool.py` | IMPLEMENTAR |
| Implementar ConsultarPortfolioTool | `facade/mcp/tools/consultar_portfolio_tool.py` | IMPLEMENTAR |
| Criar CotacaoTickerTool | `facade/mcp/tools/cotacao_ticker_tool.py` | NOVO |

**Critério de Pronto:**
- [ ] Tools MCP testáveis via cliente MCP
- [ ] Retornam mesmos dados que REST

---

## Open Questions

1. **Cache de cotações** — Implementar cache 1min no YahooFinanceFeed?
   - **Status:** Backlog (tarefa 3.5 do verification)
   - **Decisão:** Postergar para change separada

2. **Endpoint /deposito** — Adicionar na Fase 2 ou Fase 3?
   - **Status:** Identificado como necessidade
   - **Decisão:** Adicionar como `DepositarCommand` na Fase 2

3. **Testes automatizados** — Qual cobertura mínima?
   - **Status:** 16 testes implementados
   - **Decisão:** Mínimo 1 teste por handler (smoke test) ✓

---

## Bônus Implementados

### Prompts Modulares (MCP Resources)

**Motivação:** Instruções injetáveis para LLMs via MCP, permitindo contexto dinâmico sem hardcode.

**Estrutura:**
```
src/core/paper/prompts/
├── __init__.py                    # Loader (load_prompt, load_all_prompts)
├── paper_trading_guide.md         # Visão geral, capacidades, fluxo
├── operations_reference.md        # Tools MCP, REST API, códigos de erro
└── troubleshooting.md             # Problemas comuns, soluções, debug
```

**MCP Resources registrados:**
| URI | Nome | Tamanho |
|-----|------|---------|
| `paper://prompts/guide` | Guia de Paper Trading | ~60 linhas |
| `paper://prompts/operations` | Referência de Operações | ~116 linhas |
| `paper://prompts/troubleshooting` | Guia de Troubleshooting | ~117 linhas |
| `paper://prompts/all` | Todas as Instruções | ~293 linhas |

**Uso:**
```python
from src.core.paper.prompts import load_prompt
guide = load_prompt("guide")  # Retorna markdown

# Via MCP Resource
GET paper://prompts/operations
```

**Benefícios:**
- Contexto injetável em tempo de execução
- Atualização sem redeploy (se usar filesystem)
- Reutilização entre REST API e MCP
- Base para RAG futuro
