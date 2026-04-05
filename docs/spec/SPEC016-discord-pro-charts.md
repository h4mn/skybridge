# SPEC016 - Gráficos Profissionais Discord

Especificação dos gráficos profissionais com matplotlib + mplfinance.

## Status
🟢 Implementado (2026-03-31)

## Motivação

QuickChart era simples demais. Usuário exigia visual profissional com:
- Candlestick charts (velas)
- Dark theme moderno
- Cores neon (TradingView style)
- Estilos configuráveis

## Arquitetura

```
chart_helper_pro.py
├── ChartTheme (design tokens Figma)
├── create_dark_style()      → Custom neon theme
├── create_nightclouds_style() → Built-in mplfinance
├── create_hollow_filled_style() → TradingView style
└── ProChartHelper
    ├── candlestick_chart()       [3 estilos]
    ├── candlestick_nightclouds()
    ├── candlestick_hollow_filled()
    ├── alocacao_donut()
    ├── pnl_bar_chart()
    └── portfolio_evolution()
```

## Dependências

```bash
pip install mplfinance pandas matplotlib
```

## Estilos de Candlestick

### 1. Custom (Neon Dark Theme)

Cores neon TradingView com dark_background:

```python
from src.core.discord.presentation.chart_helper_pro import ProChartHelper

helper = ProChartHelper()
img = helper.candlestick_chart(
    data,           # DataFrame OHLCV
    title="Bitcoin",
    symbol="BTC-USD",
    volume=True,
    ma_periods=[20, 50],  # Médias móveis
    style="custom"
)
```

Características:
- Up: `#00e676` (verde neon)
- Down: `#ff1744` (vermelho neon)
- Wick: Herda cor da vela
- Background: `#0F172A` (Slate 900)

### 2. Nightclouds (Built-in)

Estilo nativo do mplfinance:

```python
img = helper.candlestick_nightclouds(data, "BTC", "BTC-USD")
```

Look profissional sem customização.

### 3. Hollow & Filled (TradingView)

```python
img = helper.candlestick_hollow_filled(data, "BTC", "BTC-USD")
```

Corpo hollow = fechamento > abertura  
Corpo filled = fechamento < abertura

## Outros Gráficos

### Alocação (Donut)

```python
img = helper.alocacao_donut({
    "Cripto": Decimal("117900"),
    "Ações": Decimal("6702.50"),
    "FIIs": Decimal("36127.50")
})
```

### PnL (Barras Horizontais)

```python
ativos = [
    {"ticker": "BTC", "pnl": Decimal("7500.00")},
    {"ticker": "ETH", "pnl": Decimal("1400.00")},
    {"ticker": "BOVA11", "pnl": Decimal("-200.00")},
]
img = helper.pnl_bar_chart(ativos)
```

### Evolução (Line + Annotations)

```python
data = pd.DataFrame({"valor": [...]}, index=dates)
img = helper.portfolio_evolution(data)
```

Annotações automáticas de máximo/mínimo.

## Uso no Discord

```python
import discord
from src.core.discord.presentation.chart_helper_pro import ProChartHelper

async def show_chart(interaction):
    helper = ProChartHelper(dpi=120, width=14, height=7)
    img = helper.candlestick_chart(data, "BTC", "BTC-USD")

    await interaction.response.send_message(
        "📊 Candlestick BTC/USD",
        file=discord.File(img, "chart.png")
    )
```

## Design Tokens (Figma)

```python
class ChartTheme:
    BG_DARK = "#0F172A"        # Slate 900
    BG_CARD = "#1E293B"        # Slate 800
    TEXT_PRIMARY = "#F8FAFC"   # Slate 50
    TEXT_SECONDARY = "#94A3B8" # Slate 400
    SUCCESS = "#22C55E"        # Green 500
    DANGER = "#EF4444"         # Red 500
    WARNING = "#F59E0B"        # Amber 500
    INFO = "#3B82F6"           # Blue 500
    CRYPTO = "#F59E0B"         # Amber
    STOCKS = "#6366F1"         # Indigo
    FIIS = "#8B5CF6"           # Violet
```

## Demo

```bash
python -m demos.demo_charts_pro
```

Gera 4 gráficos PNG:
- `chart_candlestick.png`
- `chart_alocacao.png`
- `chart_pnl.png`
- `chart_evolution.png`

## Referências

- mplfinance docs: https://github.com/matplotlib/mplfinance
- TradingView colors: User research
- Design Figma: `Portfolio Embed`

> "Gráficos profissionais = credibilidade" – made by Sky 📈
