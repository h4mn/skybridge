---
status: proposto
data: 2026-03-27
contexto: src/core/paper
prioridade: alta
---

# PRD029 — Migração helloworld → DDD + PaperState

## Por que

O helloworld cumpriu seu papel: validou dados reais de mercado, execução de
ordens, persistência e PnL marcado a mercado — tudo funcionando em produção
no mesmo dia. Agora a lógica que vive concentrada no `facade/helloworld/facade.py`
precisa ser extraída para a camada DDD para que `facade/api` e `facade/mcp`
possam usar os mesmos adapters sem duplicar código.

Dois problemas bloqueiam essa migração hoje:

1. **Conflito de JSON** — `JsonFilePaperBroker` e `JsonFilePortfolioRepository`
   escrevem schemas incompatíveis no mesmo arquivo (ver ADR028)
2. **Lógica de aplicação no helloworld** — commands e queries que deveriam
   estar em `application/` vivem diretamente no facade

## O que muda

### Fase 1 — PaperState (pré-requisito, ~2h)

Resolve o conflito de JSON antes de qualquer migração.

| Artefato | Ação | Onde |
|---|---|---|
| `PaperStatePort` | criar | `ports/paper_state_port.py` |
| `JsonFilePaperState` | criar | `adapters/persistence/json_file_paper_state.py` |
| `JsonFilePaperBroker` | refatorar (delegar) | `adapters/brokers/json_file_broker.py` |
| `JsonFilePortfolioRepository` | refatorar (delegar) | `adapters/persistence/json_file_repository.py` |
| testes unitários PaperState | criar | `tests/unit/test_paper_state.py` |

**Contrato mínimo de `PaperStatePort`:**
```python
class PaperStatePort(ABC):
    @abstractmethod
    def carregar(self) -> PaperStateData: ...

    @abstractmethod
    def salvar(self, data: PaperStateData) -> None: ...

    @abstractmethod
    def resetar(self, saldo_inicial: Decimal) -> None: ...
```

**Schema canônico do JSON após esta fase:**
```json
{
  "version": 2,
  "updated_at": "...",
  "saldo": 95158.0,
  "saldo_inicial": 100000.0,
  "ordens": {},
  "posicoes": {},
  "portfolios": {}
}
```

**Critério de pronto:** testes unitários passando; helloworld sobe sem erros;
`paper_state.json` tem schema unificado.

---

### Fase 2 — Commands e Queries na camada Application (~2h)

Extrai a lógica de negócio do helloworld para onde ela pertence.

| Artefato | Ação | Onde | Origem |
|---|---|---|---|
| `CriarOrdemCommand` | criar | `application/commands/criar_ordem.py` | lógica do broker |
| `CriarOrdemHandler` | criar | `application/handlers/criar_ordem_handler.py` | lógica do broker |
| `ConsultarMercadoQuery` | criar | `application/queries/consultar_mercado.py` | endpoints /cotacao e /historico |
| `ConsultarMercadoHandler` | criar | `application/handlers/consultar_mercado_handler.py` | chamada direta ao feed |
| `ConsultarPortfolioQuery` | expandir | `application/queries/consultar_portfolio.py` | adicionar PnL real |

O helloworld **não é reescrito** — ele passa a importar os handlers da
camada de application em vez de chamar o broker diretamente.

**Critério de pronto:** helloworld funciona identicamente ao atual;
novos handlers têm testes unitários; `application/commands/` não está vazio.

---

### Fase 3 — Implementar facade/api com DI real (~3h)

Liga as rotas do scaffold aos handlers da camada de application.

| Artefato | Ação | O que faz |
|---|---|---|
| `dependencies.py` | implementar | `get_broker()`, `get_feed()`, `get_state()` retornam adapters reais |
| `routes/mercado.py` | criar | `GET /api/v1/paper/mercado/cotacao/{ticker}` e `/historico/{ticker}` |
| `routes/ordens.py` | implementar | `POST /ordens` via `CriarOrdemHandler` |
| `routes/portfolio.py` | implementar | `GET /portfolio`, `GET /posicoes` via handlers |

**Critério de pronto:** `facade/api` sobe sem `NotImplementedError`;
Swagger documentado; mesmos resultados que o helloworld para mesmos inputs.

---

### Fase 4 — Implementar facade/mcp com tools reais (~2h)

Liga as tools MCP aos handlers já implementados na Fase 2.

| Artefato | Ação | O que faz |
|---|---|---|
| `CriarOrdemTool.execute()` | implementar | chama `CriarOrdemHandler` |
| `ConsultarPortfolioTool.execute()` | implementar | chama `ConsultarPortfolioQuery` expandida |
| `paper_cotacao_ticker` | criar | nova tool — chama `ConsultarMercadoHandler` |

`paper_avaliar_risco` permanece como `NotImplementedError` — lógica de risco
é um item genuinamente novo, não existe em nenhum lugar ainda.

**Critério de pronto:** tools MCP testáveis via cliente MCP; retornam os
mesmos dados que os endpoints REST equivalentes.

---

## O que o helloworld vira depois disso

O helloworld **permanece** como sandbox de experimentação rápida. Ele não é
descontinuado. A diferença é que passa a ser um consumidor das camadas DDD,
não o detentor da lógica.

```
Antes:  helloworld ──► broker (direto)
Depois: helloworld ──► CriarOrdemHandler ──► broker
        facade/api ──► CriarOrdemHandler ──► broker   (mesmo handler)
        facade/mcp ──► CriarOrdemHandler ──► broker   (mesmo handler)
```

## Mapa de extração completo

| Lógica hoje (helloworld) | Vai para | Tipo |
|---|---|---|
| `feed.obter_cotacao()` direto | `ConsultarMercadoHandler` | Query |
| `feed.obter_historico()` direto | `ConsultarMercadoHandler` | Query |
| `broker.enviar_ordem()` direto | `CriarOrdemHandler` | Command |
| `broker.listar_posicoes_marcadas()` | `ConsultarPortfolioQuery` (expandida) | Query |
| `broker.listar_ordens()` | `ConsultarOrdensQuery` (nova) | Query |
| cálculo de PnL no endpoint | `ConsultarPortfolioQuery` (expandida) | Query |
| instanciação de feed+broker | `dependencies.py` (facade/api) | DI |

## Não entra neste PRD

- Conversão cambial USD/BRL (backlog separado)
- Quantidades fracionadas com `Decimal` (backlog separado)
- Script standalone de monitoramento (backlog separado)
- Lógica de risco — VaR, Sharpe, concentração (futuro)
- Testes de integração end-to-end (futuro)

## Ordem de execução recomendada

```
Fase 1 (PaperState) → validar → Fase 2 (Commands/Queries)
→ validar → Fase 3 (facade/api) → validar → Fase 4 (facade/mcp)
```

Cada fase termina com o helloworld funcionando. Nunca quebra o que existe.
