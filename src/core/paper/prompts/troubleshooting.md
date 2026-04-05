# Troubleshooting

## Problemas Comuns

### Cotação não retorna

**Sintoma:** `{"sucesso": false, "erro": "Ticker não encontrado"}`

**Possíveis causas:**
1. Ticker incorreto (verifique sufixo `.SA` para B3)
2. Mercado fechado (Yahoo não retorna cotação fora do horário)
3. Ativo delistado ou código alterado

**Solução:**
```
# Tickers B3 exigem sufixo .SA
ERRADO: PETR4
CORRETO: PETR4.SA

# Cripto não tem sufixo
BTC-USD (correto)
ETH-USD (correto)
```

---

### Saldo insuficiente

**Sintoma:** `{"sucesso": false, "erro": "Saldo insuficiente..."}`

**Causa:** Valor da ordem excede saldo disponível

**Solução:**
1. Consulte portfolio para ver saldo atual
2. Reduza quantidade ou escolha ativo mais barato
3. Faça depósito adicional se necessário

---

### Posição insuficiente para venda

**Sintoma:** `{"sucesso": false, "erro": "Posição insuficiente..."}`

**Causa:** Tentativa de vender mais do que possui

**Solução:**
1. Consulte posições abertas
2. Verifique quantidade disponível
3. Ajuste quantidade da ordem de venda

---

### Arquivo paper_state.json corrompido

**Sintoma:** Estado inesperado, saldos errados

**Causa:** Processo interrompido durante escrita

**Solução:**
```bash
# Backup automático é criado como paper_state.json.v1.bak
# Restaure manualmente se necessário:
cp paper_state.json.v1.bak paper_state.json

# Ou resete o portfolio:
# POST /api/v1/paper/portfolio/reset
```

---

### API não sobe

**Sintoma:** `ImportError` ou `ModuleNotFoundError`

**Causa:** Dependências não instaladas

**Solução:**
```bash
# Instale dependências do paper trading
pip install yfinance fastapi uvicorn

# Verifique importações
python -c "from src.core.paper.facade.api.app import app; print('OK')"
```

---

### Yahoo Finance retorna erro 502

**Sintoma:** `"Erro ao buscar dados: Yahoo Finance..."`

**Causa:** API do Yahoo temporariamente indisponível ou rate limit

**Solução:**
1. Aguarde alguns segundos e tente novamente
2. Yahoo tem rate limit de ~2000 requisições/hora
3. Considere cache local para cotações frequentes

---

## Logs e Debug

```bash
# Verificar estado do paper_state.json
cat paper_state.json | python -m json.tool

# Rodar testes unitários
python -m pytest tests/unit/core/paper/ -v

# Verificar saúde da API
curl http://localhost:8000/health
```

---

> "Debug é 90% paciência, 10% log." – made by Sky 🔧
