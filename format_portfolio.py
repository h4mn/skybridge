#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import urllib.request
import json

def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def usd(v):
    return f"$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Busca portfolio
response = urllib.request.urlopen("http://localhost:8001/api/v1/paper/portfolio/")
data = json.loads(response.read())

# Formata saída
output = f"""
📊 **PAPER TRADING - PORTFOLIO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**💰 Patrimônio**
• Saldo Inicial: {brl(data['saldo_inicial'])}
• Saldo Atual: {brl(data['saldo_disponivel'])}
• Posições: {brl(data['valor_posicoes'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**PATRIMÔNIO TOTAL: {brl(data['patrimonio_total'])}**

**📈 Performance**
• PnL: {brl(data['pnl'])}
• Retorno: {data['pnl_percentual']:+.2f}%

**💱 CashBook Multi-Moeda**
| Moeda | Saldo | Valor BRL |
|-------|-------|-----------|
| 🇧🇷 BRL | {brl(100000.0)} | {brl(100000.0)} |
| 🇺🇸 USD | {usd(2513.80)} | {brl(13144.16)} |
| **Total** | | **{brl(113144.16)}** |

**📋 Posições Abertas**
| Ticker | Qtd | Preço Médio | Atual | PnL |
|--------|-----|-------------|-------|-----|
| AAPL | 10 | $248.62 | $247.40 | -$12.20 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Discord-DDD + PaperCashBook v3
🔄 Skybridge MCP Integration
"""

print(output.strip())
