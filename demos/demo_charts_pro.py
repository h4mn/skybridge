# -*- coding: utf-8 -*-
"""
Demo - Gráficos Profissionais Discord.

Demonstra gráficos matplotlib/mplfinance com dark theme profissional.

Execute: python -m demos.demo_charts_pro
"""

import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Fix UTF-8 no Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import pandas as pd
import numpy as np

sys.path.insert(0, ".")

from src.core.discord.presentation.chart_helper_pro import (
    ProChartHelper,
    ChartTheme,
    create_candlestick_chart,
)


def demo_candlestick():
    """Gera gráfico candlestick profissional."""
    print("\n📊 Gerando Candlestick Chart...")

    # Dados OHLCV simulados - mais dias para médias móveis funcionarem
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=90),  # 90 dias para MA 50
        end=datetime.now(),
        freq="D"
    )

    np.random.seed(42)
    base_price = 85000
    n = len(dates)

    # Simula random walk mais realista
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.randn() * 2000  # Volatilidade
        closes.append(closes[-1] + change)

    # Cria DataFrame OHLCV realista
    data = pd.DataFrame(index=dates)
    data["Close"] = closes

    # Open, High, Low derivados do Close (com variação)
    data["Open"] = data["Close"].shift(1).fillna(base_price)
    data["High"] = data[["Open", "Close"]].max(axis=1) + np.random.rand(n) * 500
    data["Low"] = data[["Open", "Close"]].min(axis=1) - np.random.rand(n) * 500
    data["Volume"] = np.random.randint(1000, 10000, size=n)

    # Remove primeira linha se necessário
    data = data.dropna()

    # Cria gráfico
    helper = ProChartHelper(dpi=120, width=14, height=7)
    img = helper.candlestick_chart(
        data,
        title="Bitcoin (BTC/USD)",
        symbol="BTC-USD",
        volume=True,
        ma_periods=[20, 50],
    )

    # Salva arquivo
    with open("chart_candlestick.png", "wb") as f:
        f.write(img.read())

    print("  ✅ Salvo: chart_candlestick.png")


def demo_alocacao():
    """Gera gráfico de alocação profissional."""
    print("\n📈 Gerando Alocação Donut...")

    alocacao = {
        "Cripto": Decimal("117900.00"),
        "Ações": Decimal("6702.50"),
        "FIIs": Decimal("36127.50"),
    }

    helper = ProChartHelper(dpi=120)
    img = helper.alocacao_donut(alocacao)

    with open("chart_alocacao.png", "wb") as f:
        f.write(img.read())

    print("  ✅ Salvo: chart_alocacao.png")


def demo_pnl():
    """Gera gráfico de PnL profissional."""
    print("\n💰 Gerando PnL Bar Chart...")

    ativos = [
        {"ticker": "BTC", "pnl": Decimal("7500.00")},
        {"ticker": "ETH", "pnl": Decimal("1400.00")},
        {"ticker": "HGLG11", "pnl": Decimal("1500.00")},
        {"ticker": "MXRF11", "pnl": Decimal("97.50")},
        {"ticker": "PETR4", "pnl": Decimal("430.00")},
        {"ticker": "VALE3", "pnl": Decimal("162.50")},
        {"ticker": "BOVA11", "pnl": Decimal("-200.00")},  # Prejuízo
    ]

    helper = ProChartHelper(dpi=120)
    img = helper.pnl_bar_chart(ativos)

    with open("chart_pnl.png", "wb") as f:
        f.write(img.read())

    print("  ✅ Salvo: chart_pnl.png")


def demo_evolution():
    """Gera gráfico de evolução do portfolio."""
    print("\n📊 Gerando Portfolio Evolution...")

    dates = pd.date_range(
        start=datetime.now() - timedelta(days=90),
        end=datetime.now(),
        freq="W"
    )

    np.random.seed(42)
    base_value = 150000

    # Simula evolução com tendência de alta
    values = []
    current = base_value
    for _ in range(len(dates)):
        change = np.random.randn() * 3000 + 500  # Tendência de +500 em média
        current += change
        values.append(current)

    data = pd.DataFrame({
        "valor": values,
    }, index=dates)

    helper = ProChartHelper(dpi=120)
    img = helper.portfolio_evolution(data)

    with open("chart_evolution.png", "wb") as f:
        f.write(img.read())

    print("  ✅ Salvo: chart_evolution.png")


def main():
    """Executa todos os demos."""
    print("\n" + "="*60)
    print("🎨 DEMO - Gráficos Profissionais Discord")
    print("Matplotlib + mplfinance + Dark Theme")
    print("="*60)

    print("\n📦 Prerequisites:")
    print("   pip install mplfinance pandas matplotlib")

    print("\n🎨 Tema: Dark Theme baseado em Figma")
    print(f"   Background: {ChartTheme.BG_DARK}")
    print(f"   Success: {ChartTheme.SUCCESS}")
    print(f"   Danger: {ChartTheme.DANGER}")

    # Demo 1: Candlestick
    demo_candlestick()

    # Demo 2: Alocação
    demo_alocacao()

    # Demo 3: PnL
    demo_pnl()

    # Demo 4: Evolução
    demo_evolution()

    # Resumo
    print("\n" + "="*60)
    print("✅ DEMO COMPLETA!")
    print("="*60)
    print("""
📊 Arquivos gerados:
   - chart_candlestick.png  (Gráfico de velas com médias móveis)
   - chart_alocacao.png     (Gráfico de rosca - alocação)
   - chart_pnl.png          (Gráfico de barras - PnL por ativo)
   - chart_evolution.png    (Gráfico de linha - evolução)

🎨 Características:
   - Dark theme profissional
   - Cores baseadas no design Figma
   - Alta resolução (120 DPI)
   - Prontos para enviar no Discord

💡 Uso no Discord:
   ```python
   helper = ProChartHelper()
   img = helper.candlestick_chart(data, "BTC Chart", "BTC-USD")

   await interaction.response.send_message(
       file=discord.File(img, "chart.png")
   )
   ```
    """)

    print("> " + "Matplotlib profissional + mplfinance = gráficos de nível institucional" + " – made by Sky 📈")


if __name__ == "__main__":
    main()
