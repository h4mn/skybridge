# Operations Reference

## MCP Tools Disponíveis

### paper_cotacao_ticker

Consulta cotação atual de um ativo.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| ticker | string | sim | Código do ativo (ex: PETR4.SA) |

**Retorno:**
```json
{
  "sucesso": true,
  "ticker": "PETR4.SA",
  "preco": 49.26,
  "variacao": 1.5,
  "timestamp": "2026-03-27T10:30:00"
}
```

---

### paper_consultar_portfolio

Consulta estado atual do portfolio.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| portfolio_id | string | não | ID do portfolio (padrão: "default") |

**Retorno:**
```json
{
  "sucesso": true,
  "portfolio_id": "default",
  "saldo_atual": 95074.0,
  "pnl": -4926.0,
  "pnl_percentual": -4.93
}
```

---

### paper_criar_ordem

Executa ordem de compra ou venda.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| ticker | string | sim | Código do ativo |
| lado | string | sim | "COMPRA" ou "VENDA" |
| quantidade | integer | sim | Número de unidades |
| preco_limite | number | não | Preço limite (opcional) |

**Retorno (sucesso):**
```json
{
  "sucesso": true,
  "ordem_id": "uuid-gerado",
  "ticker": "PETR4.SA",
  "lado": "COMPRA",
  "quantidade": 100,
  "preco_execucao": 49.26,
  "valor_total": 4926.0,
  "status": "EXECUTADA"
}
```

**Retorno (erro):**
```json
{
  "sucesso": false,
  "erro": "Saldo insuficiente. Necessário: R$ 5000 | Disponível: R$ 3000"
}
```

---

## REST API Endpoints

### Mercado
- `GET /api/v1/paper/mercado/cotacao/{ticker}` - Cotação atual
- `GET /api/v1/paper/mercado/historico/{ticker}?dias=30` - Histórico

### Trading
- `POST /api/v1/paper/ordens` - Criar ordem
- `GET /api/v1/paper/ordens` - Listar ordens

### Portfolio
- `GET /api/v1/paper/portfolio` - Consultar portfolio
- `GET /api/v1/paper/portfolio/posicoes` - Posições abertas
- `POST /api/v1/paper/portfolio/deposito` - Depositar saldo
- `POST /api/v1/paper/portfolio/reset` - Resetar portfolio

---

## Códigos de Erro

| Código | Mensagem | Causa |
|--------|----------|-------|
| 400 | Parâmetro inválido | Ticker vazio, quantidade <= 0 |
| 404 | Ticker não encontrado | Código inexistente |
| 422 | Saldo insuficiente | Compra maior que saldo |
| 422 | Posição insuficiente | Venda maior que posição |
| 502 | Erro ao buscar dados | Yahoo Finance indisponível |

---

> "Execute com precisão, não com pressa." – made by Sky 🎯
