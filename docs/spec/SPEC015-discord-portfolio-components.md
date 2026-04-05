# SPEC015 - Discord Portfolio Components

Especificação dos componentes Discord para o módulo Paper Trading.

## Status
🟢 Implementado (2026-03-31)
🔄 **ATUALIZAÇÃO:** Migração para gráficos profissionais (SPEC016)

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     Discord Bot Client                       │
├─────────────────────────────────────────────────────────────┤
│  Presentation Layer                                         │
│  ├── portfolio_views.py    (Views + Read Models)            │
│  ├── chart_helper.py       (QuickChart integration)         │
│  └── __init__.py            (Exports)                       │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                          │
│  └── commands/portfolio_commands.py  (Slash commands)       │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                       │
│  └── portfolio_adapter.py   (DDD placeholder)               │
├─────────────────────────────────────────────────────────────┤
│                     Paper Module                            │
│              (integration TBD)                              │
└─────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. PortfolioMainView

View principal com 4 botões interativos:

```python
class PortfolioMainView(View):
    @button("💰 Saldo/Posições", primary, row=0)
    async def saldo_button(interaction, button):
        # Mostra saldo, PnL, contagem de ativos

    @button("📊 Portfolio Completo", secondary, row=0)
    async def completo_button(interaction, button):
        # Lista todos os ativos com detalhes

    @button("📈 Ver Alocação", secondary, row=1)
    async def alocacao_button(interaction, button):
        # Gráfico de alocação por tipo

    @button("⚙️ Configurações", secondary, row=1)
    async def config_button(interaction, button):
        # Placeholder para configurações
```

### 2. Read Models

```python
@dataclass
class AssetCardReadModel:
    ticker: str
    nome: str
    tipo: str  # "Ação", "Cripto", "FII"
    variação_percentual: float
    quantidade: Decimal
    preco_medio: Decimal
    preco_atual: Decimal
    valor_total: Decimal
    lucro_prejuizo: Decimal

@dataclass
class PortfolioReadModel:
    valor_total: Decimal
    valor_investido: Decimal
    lucro_prejuizo: Decimal
    lucro_prejuizo_percentual: float
    ativos: list[AssetCardReadModel]
    alocacao_por_tipo: dict[str, Decimal]
```

### 3. QuickChart Helper

Gera gráficos visuais via QuickChart API:

```python
from src.core.discord.presentation.chart_helper import create_alocacao_chart

url = create_alocacao_chart({
    "Cripto": Decimal("117900"),
    "Ações": Decimal("6702.50"),
    "FIIs": Decimal("36127.50")
})
# URL: https://quickchart.io/chart?c=...
```

**Tipos suportados:**
- `pie_chart()` - Gráfico de pizza
- `doughnut_chart()` - Gráfico de rosca
- `bar_chart()` - Gráfico de barras (PnL)
- `line_chart()` - Gráfico de linha (evolução)

## Slash Commands

```
/portfolio mostrar
    → Mostra painel principal com embed + botões

/portfolio saldo
    → Mostra saldo e posições (ephemeral)

/portfolio alocacao
    → Mostra alocação com gráfico (ephemeral)
```

## Integração com Paper Module

**TODO:**
1. Implementar `GetPortfolioQuery`, `GetSaldoQuery`, `GetAlocacaoQuery`
2. Implementar handlers no Application Layer do Paper
3. Substituir dados mockados por queries reais
4. Adicionar gráficos aos embeds das views

## Design Tokens (Figma)

Cores baseadas no design "Portfolio Embed":

```python
class PortfolioColors:
    SUCCESS = 0x22C55E    # Verde +15.09%
    DANGER = 0xEF4444     # Vermelho
    PRIMARY = 0x3B82F6    # Azul primary
    CRYPTO = 0xF59E0B     # Laranja
    STOCK = 0x6366F1      # Índigo
    FII = 0x8B5CF6        # Roxo
```

## Testes

Testes manuais:
1. Iniciar bot Discord
2. Enviar `/portfolio mostrar`
3. Clicar em cada botão
4. Verificar respostas

## Referências

- Design Figma: `figma.com/make/odvbXbbCeh6BE4AcNh5Ll9/Portfolio-Embed`
- Skill Discord Interactions: `.claude/skills/discord-interaction/`
- QuickChart API: `https://quickchart.io/` (simples, sem candlestick)

## 📊 Gráficos Profissionais

**NOTA:** Para visualizações mais profissionais com candlestick charts, ver **SPEC016**:

- `chart_helper_pro.py` - matplotlib + mplfinance
- Candlestick com 3 estilos (custom, nightclouds, hollow_filled)
- Dark theme com cores neon TradingView
- Donut, barras PnL, evolução com annotations

**Migração:**
```python
# Antes (QuickChart - simples)
from src.core.discord.presentation.chart_helper import create_alocacao_chart
url = create_alocacao_chart(alocacao)

# Depois (Pro - profissional)
from src.core.discord.presentation.chart_helper_pro import ProChartHelper
helper = ProChartHelper()
img = helper.alocacao_donut(alocacao)
await interaction.response.send_message(file=discord.File(img, "chart.png"))
```

> "Gráficos profissionais = credibilidade" – made by Sky 📈
