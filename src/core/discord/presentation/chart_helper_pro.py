# -*- coding: utf-8 -*-
"""
Discord Presentation - Professional Chart Helper.

Gráficos profissionais com matplotlib + mplfinance.
Estilos dark theme modernos baseados em design Figma.

Dependencies:
    pip install mplfinance pandas matplotlib
"""

from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Any
import io

import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.figure import Figure


# ═══════════════════════════════════════════════════════════════════════
# Design Tokens - Figma Inspired
# ═══════════════════════════════════════════════════════════════════════

class ChartTheme:
    """Tema de gráficos profissional dark theme."""

    # Background colors
    BG_DARK = "#0F172A"        # Slate 900
    BG_CARD = "#1E293B"        # Slate 800
    BG_HOVER = "#334155"       # Slate 700

    # Text colors
    TEXT_PRIMARY = "#F8FAFC"   # Slate 50
    TEXT_SECONDARY = "#94A3B8" # Slate 400
    TEXT_MUTED = "#64748B"     # Slate 500

    # Accent colors
    SUCCESS = "#22C55E"        # Green 500
    DANGER = "#EF4444"         # Red 500
    WARNING = "#F59E0B"        # Amber 500
    INFO = "#3B82F6"           # Blue 500
    PURPLE = "#8B5CF6"         # Violet 500
    CYAN = "#06B6D4"           # Cyan 500

    # Grid colors
    GRID_MAJOR = "#334155"     # Slate 700
    GRID_MINOR = "#1E293B"     # Slate 800

    # Type-specific colors
    CRYPTO = "#F59E0B"         # Amber
    STOCKS = "#6366F1"         # Indigo
    FIIS = "#8B5CF6"           # Violet
    CASH = "#22C55E"           # Green


# ═══════════════════════════════════════════════════════════════════════
# mplfinance Styles
# ═══════════════════════════════════════════════════════════════════════

def create_dark_style() -> dict:
    """
    Cria estilo dark theme para mplfinance.

    Baseado em research 2026 - usa neon colors e dark_background.
    """
    market_colors = mpf.make_marketcolors(
        up="#00e676",      # Verde neon para alta (TradingView style)
        down="#ff1744",    # Vermelho neon para baixa
        edge="inherit",
        wick={"up": "#00e676", "down": "#ff1744"},
        volume={"up": "#00e676", "down": "#ff1744"},
        inherit=True,
    )

    style = mpf.make_mpf_style(
        base_mpl_style="dark_background",  # Base do matplotlib
        marketcolors=market_colors,
        facecolor=ChartTheme.BG_DARK,
        edgecolor=ChartTheme.BG_DARK,
        figcolor=ChartTheme.BG_DARK,
        gridcolor="#2a2a2a",
        gridstyle="--",
        y_on_right=False,
        rc={
            "text.color": ChartTheme.TEXT_PRIMARY,
            "axes.labelcolor": ChartTheme.TEXT_SECONDARY,
            "axes.facecolor": ChartTheme.BG_CARD,
            "axes.edgecolor": ChartTheme.GRID_MAJOR,
            "axes.titlecolor": ChartTheme.TEXT_PRIMARY,
            "xtick.color": ChartTheme.TEXT_SECONDARY,
            "ytick.color": ChartTheme.TEXT_SECONDARY,
            "grid.color": "#2a2a2a",
            "grid.alpha": 0.3,
            "font.family": "sans-serif",
            "font.size": 10,
            "figure.facecolor": ChartTheme.BG_DARK,
        }
    )

    return style


def create_nightclouds_style() -> dict:
    """
    Estilo built-in 'nightclouds' do mplfinance.

    Alternativa rápida com look profissional nativo.
    """
    return "nightclouds"


def create_hollow_filled_style() -> dict:
    """
    Estilo hollow_and_filled (TradingView style).

    Corpo hollow = fechamento maior que abertura
    Corpo filled = fechamento menor que abertura
    """
    market_colors = mpf.make_marketcolors(
        up="#00e676",
        down="#ff1744",
        edge="inherit",
        wick={"up": "#00e676", "down": "#ff1744"},
        volume="in",
        inherit=True,
    )

    style = mpf.make_mpf_style(
        base_mpl_style="dark_background",
        marketcolors=market_colors,
        facecolor=ChartTheme.BG_DARK,
        gridcolor="#2a2a2a",
    )

    return {"style": style, "type": "hollow_and_filled"}


DARK_STYLE = create_dark_style()
NIGHTCLOUDS_STYLE = create_nightclouds_style()


# ═══════════════════════════════════════════════════════════════════════
# Professional Chart Helper
# ═══════════════════════════════════════════════════════════════════════

class ProChartHelper:
    """
    Helper para gráficos profissionais com matplotlib.

    Salva gráficos como bytes para envio no Discord.

    Example:
        helper = ProChartHelper()

        # Candlestick
        img = helper.candlestick_chart(ohlcv_data, "BTC-USD")

        # Alocação
        img = helper.alocacao_donut(alocacao_dict)

        # Envia no Discord
        await interaction.response.send_message(file=discord.File(img, "chart.png"))
    """

    def __init__(self, dpi: int = 100, width: int = 12, height: int = 6):
        """
        Inicializa helper.

        Args:
            dpi: Resolução (padrão: 100)
            width: Largura em polegadas (padrão: 12)
            height: Altura em polegadas (padrão: 6)
        """
        self.dpi = dpi
        self.width = width
        self.height = height

        # Configura matplotlib para dark theme
        plt.style.use("dark_background")

    def candlestick_chart(
        self,
        data: pd.DataFrame,
        title: str,
        symbol: str = "",
        volume: bool = True,
        ma_periods: list[int] | None = None,
        style: str | dict = "custom",
    ) -> io.BytesIO:
        """
        Cria gráfico candlestick profissional.

        Args:
            data: DataFrame OHLCV com columns: Open, High, Low, Close, Volume
                Index deve ser DatetimeIndex
            title: Título do gráfico
            symbol: Símbolo do ativo (ex: "BTC-USD")
            volume: Incluir volume
            ma_periods: Períodos de médias móveis (ex: [20, 50])
            style: Estilo do gráfico ("custom", "nightclouds", "hollow_filled")

        Returns:
            BytesIO com imagem PNG
        """
        # Prepara dados
        df = data.copy()

        # Adiciona médias móveis se solicitado
        addplot_list = []
        if ma_periods:
            for period in ma_periods:
                ma = df["Close"].rolling(window=period).mean()
                color = ChartTheme.INFO if period == 20 else ChartTheme.WARNING
                ap = mpf.make_addplot(
                    ma,
                    type="line",
                    color=color,
                    width=1.5,
                    alpha=0.8,
                )
                addplot_list.append(ap)

        # Seleciona estilo
        if style == "nightclouds":
            chart_style = NIGHTCLOUDS_STYLE
        elif style == "hollow_filled":
            chart_config = create_hollow_filled_style()
            # hollow_filled usa type diferente
            return self._hollow_filled_chart(df, title, symbol, volume, ma_periods, chart_config)
        else:
            chart_style = DARK_STYLE

        # Configurações do plot
        kwargs = {
            "type": "candle",
            "style": chart_style,
            "title": f"{title}\n{symbol}",
            "ylabel": "Preço",
            "volume": volume,
            "addplot": addplot_list if addplot_list else None,
            "figsize": (self.width, self.height),
            "returnfig": True,
        }

        # Cria o gráfico
        fig, axes = mpf.plot(df, **kwargs)

        # Ajustes finos
        if isinstance(axes, (list, tuple)):
            for ax in axes:
                if hasattr(ax, "grid"):
                    ax.grid(True, alpha=0.2, linestyle="--")

        # Salva em bytes
        return self._fig_to_bytes(fig)

    def candlestick_nightclouds(
        self,
        data: pd.DataFrame,
        title: str,
        symbol: str = "",
        volume: bool = True,
        ma_periods: list[int] | None = None,
    ) -> io.BytesIO:
        """
        Candlestick com estilo built-in 'nightclouds'.

        Estilo nativo do mplfinance com look profissional.
        """
        return self.candlestick_chart(
            data, title, symbol, volume, ma_periods, style="nightclouds"
        )

    def candlestick_hollow_filled(
        self,
        data: pd.DataFrame,
        title: str,
        symbol: str = "",
        volume: bool = True,
        ma_periods: list[int] | None = None,
    ) -> io.BytesIO:
        """
        Candlestick estilo TradingView (hollow & filled).

        Corpo hollow = fechamento maior que abertura
        Corpo filled = fechamento menor que abertura
        """
        return self.candlestick_chart(
            data, title, symbol, volume, ma_periods, style="hollow_filled"
        )

    def _hollow_filled_chart(
        self,
        data: pd.DataFrame,
        title: str,
        symbol: str,
        volume: bool,
        ma_periods: list[int] | None,
        style_config: dict,
    ) -> io.BytesIO:
        """Implementação interna para hollow_and_filled."""
        df = data.copy()

        # Adiciona médias móveis se solicitado
        addplot_list = []
        if ma_periods:
            for period in ma_periods:
                ma = df["Close"].rolling(window=period).mean()
                color = ChartTheme.INFO if period == 20 else ChartTheme.WARNING
                ap = mpf.make_addplot(
                    ma,
                    type="line",
                    color=color,
                    width=1.5,
                    alpha=0.8,
                )
                addplot_list.append(ap)

        kwargs = {
            "title": f"{title}\n{symbol}",
            "ylabel": "Preço",
            "volume": volume,
            "addplot": addplot_list if addplot_list else None,
            "figsize": (self.width, self.height),
            "returnfig": True,
        }
        kwargs.update(style_config)

        fig, axes = mpf.plot(df, **kwargs)

        if isinstance(axes, (list, tuple)):
            for ax in axes:
                if hasattr(ax, "grid"):
                    ax.grid(True, alpha=0.2, linestyle="--")

        return self._fig_to_bytes(fig)

    def alocacao_donut(
        self,
        alocacao: dict[str, Decimal | float],
        title: str = "Alocação por Tipo",
    ) -> io.BytesIO:
        """
        Cria gráfico de rosca para alocação.

        Args:
            alocacao: Dict {tipo: valor} - ignora chave "total"
            title: Título do gráfico

        Returns:
            BytesIO com imagem PNG
        """
        # Remove "total" se presente
        data = {k: float(v) for k, v in alocacao.items() if k != "total"}

        labels = list(data.keys())
        values = list(data.values())

        # Cores por tipo
        colors = [
            self._color_for_tipo(t)
            for t in labels
        ]

        # Cria figura
        fig, ax = plt.subplots(
            figsize=(8, 8),
            facecolor=ChartTheme.BG_DARK,
            dpi=self.dpi,
        )

        # Gráfico de rosca
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            pctdistance=0.85,
            startangle=90,
            wedgeprops={
                "linewidth": 2,
                "edgecolor": ChartTheme.BG_DARK,
            },
            textprops={
                "color": ChartTheme.TEXT_PRIMARY,
                "fontsize": 12,
                "fontweight": "bold",
            },
        )

        # Centraliza o buraco (donut)
        centre_circle = plt.Circle(
            (0, 0),
            0.70,
            fc=ChartTheme.BG_CARD,
            ec=ChartTheme.GRID_MAJOR,
            linewidth=2,
        )
        ax.add_artist(centre_circle)

        # Texto central - valor total
        total = sum(values)
        ax.text(
            0,
            0,
            f"R$\n{total:,.0f}",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            color=ChartTheme.TEXT_PRIMARY,
        )

        # Título
        ax.set_title(
            title,
            fontsize=16,
            fontweight="bold",
            color=ChartTheme.TEXT_PRIMARY,
            pad=20,
        )

        # Legenda
        ax.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, -0.15),
            ncol=len(labels),
            frameon=False,
            labelcolor=ChartTheme.TEXT_SECONDARY,
        )

        return self._fig_to_bytes(fig)

    def pnl_bar_chart(
        self,
        ativos: list[dict[str, Any]],
        title: str = "Lucro/Prejuízo por Ativo",
    ) -> io.BytesIO:
        """
        Cria gráfico de barras horizontal para PnL.

        Args:
            ativos: Lista de dicts com {"ticker": str, "pnl": float}
            title: Título do gráfico

        Returns:
            BytesIO com imagem PNG
        """
        tickers = [a["ticker"] for a in ativos]
        pnls = [float(a["pnl"]) for a in ativos]

        # Cores baseadas no PnL
        colors = [
            ChartTheme.SUCCESS if p >= 0 else ChartTheme.DANGER
            for p in pnls
        ]

        # Ordena por PnL (maiores primeiro)
        sorted_data = sorted(zip(tickers, pnls, colors), key=lambda x: x[1])
        tickers = [x[0] for x in sorted_data]
        pnls = [x[1] for x in sorted_data]
        colors = [x[2] for x in sorted_data]

        # Cria figura
        fig, ax = plt.subplots(
            figsize=(10, max(6, len(tickers) * 0.5)),
            facecolor=ChartTheme.BG_DARK,
            dpi=self.dpi,
        )

        # Barras horizontais
        bars = ax.barh(tickers, pnls, color=colors, alpha=0.8, edgecolor="white", linewidth=0.5)

        # Valores nas barras
        for bar, pnl in zip(bars, pnls):
            width = bar.get_width()
            ax.text(
                width + (max(pnls) * 0.01 if width >= 0 else max(pnls) * 0.05),
                bar.get_y() + bar.get_height() / 2,
                f"R$ {pnl:,.2f}",
                ha="left" if width >= 0 else "right",
                va="center",
                color=ChartTheme.TEXT_PRIMARY,
                fontweight="bold",
                fontsize=9,
            )

        # Linha zero
        ax.axvline(x=0, color=ChartTheme.GRID_MAJOR, linewidth=1, linestyle="-")

        # Styling
        ax.set_xlabel(
            "Lucro/Prejuízo (R$)",
            color=ChartTheme.TEXT_SECONDARY,
            fontsize=11,
        )
        ax.set_ylabel(
            "Ativo",
            color=ChartTheme.TEXT_SECONDARY,
            fontsize=11,
        )
        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            color=ChartTheme.TEXT_PRIMARY,
            pad=15,
        )

        # Grid
        ax.grid(
            True,
            axis="x",
            alpha=0.2,
            linestyle="--",
            color=ChartTheme.GRID_MAJOR,
        )
        ax.set_axisbelow(True)

        # Tick colors
        ax.tick_params(
            axis="both",
            colors=ChartTheme.TEXT_SECONDARY,
            labelsize=10,
        )

        # Spines
        for spine in ax.spines.values():
            spine.set_color(ChartTheme.GRID_MAJOR)
            spine.set_linewidth(0.5)

        plt.tight_layout()

        return self._fig_to_bytes(fig)

    def portfolio_evolution(
        self,
        data: pd.DataFrame,
        title: str = "Evolução do Portfolio",
    ) -> io.BytesIO:
        """
        Cria gráfico de linha para evolução do portfolio.

        Args:
            data: DataFrame com index DatetimeIndex e coluna "valor"
            title: Título do gráfico

        Returns:
            BytesIO com imagem PNG
        """
        fig, ax = plt.subplots(
            figsize=(12, 6),
            facecolor=ChartTheme.BG_DARK,
            dpi=self.dpi,
        )

        # Área preenchida
        ax.fill_between(
            data.index,
            data["valor"],
            color=ChartTheme.INFO,
            alpha=0.3,
        )

        # Linha principal
        ax.plot(
            data.index,
            data["valor"],
            color=ChartTheme.INFO,
            linewidth=2.5,
            marker="o",
            markersize=4,
            markerfacecolor=ChartTheme.BG_DARK,
            markeredgewidth=1.5,
        )

        # Destaca máximo e mínimo
        max_val = data["valor"].max()
        min_val = data["valor"].min()
        max_idx = data["valor"].idxmax()
        min_idx = data["valor"].idxmin()

        ax.scatter(
            [max_idx],
            [max_val],
            color=ChartTheme.SUCCESS,
            s=100,
            zorder=5,
            marker="^",
        )
        ax.scatter(
            [min_idx],
            [min_val],
            color=ChartTheme.DANGER,
            s=100,
            zorder=5,
            marker="v",
        )

        # Anotações
        ax.annotate(
            f"Max: R$ {max_val:,.2f}",
            xy=(max_idx, max_val),
            xytext=(10, 10),
            textcoords="offset points",
            color=ChartTheme.SUCCESS,
            fontweight="bold",
            fontsize=9,
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor=ChartTheme.BG_CARD,
                edgecolor=ChartTheme.SUCCESS,
            ),
        )

        ax.annotate(
            f"Min: R$ {min_val:,.2f}",
            xy=(min_idx, min_val),
            xytext=(10, -20),
            textcoords="offset points",
            color=ChartTheme.DANGER,
            fontweight="bold",
            fontsize=9,
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor=ChartTheme.BG_CARD,
                edgecolor=ChartTheme.DANGER,
            ),
        )

        # Styling
        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            color=ChartTheme.TEXT_PRIMARY,
            pad=15,
        )
        ax.set_ylabel(
            "Valor (R$)",
            color=ChartTheme.TEXT_SECONDARY,
            fontsize=11,
        )
        ax.grid(
            True,
            alpha=0.2,
            linestyle="--",
            color=ChartTheme.GRID_MAJOR,
        )

        # Formatação do eixo Y (moeda)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, p: f"R$ {x:,.0f}")
        )

        # Tick colors
        ax.tick_params(
            axis="both",
            colors=ChartTheme.TEXT_SECONDARY,
        )

        # Spines
        for spine in ax.spines.values():
            spine.set_color(ChartTheme.GRID_MAJOR)

        plt.tight_layout()

        return self._fig_to_bytes(fig)

    def _fig_to_bytes(self, fig: Figure) -> io.BytesIO:
        """
        Converte figura matplotlib para bytes PNG.

        Args:
            fig: Figure matplotlib

        Returns:
            BytesIO com PNG
        """
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=self.dpi,
            facecolor=ChartTheme.BG_DARK,
            edgecolor="none",
            bbox_inches="tight",
        )
        buf.seek(0)
        plt.close(fig)
        return buf

    def _color_for_tipo(self, tipo: str) -> str:
        """Retorna cor para tipo de ativo."""
        return {
            "Cripto": ChartTheme.CRYPTO,
            "Ações": ChartTheme.STOCKS,
            "FIIs": ChartTheme.FIIS,
            "Cash": ChartTheme.CASH,
        }.get(tipo, ChartTheme.INFO)


# ═══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════

def create_candlestick_chart(
    data: pd.DataFrame,
    symbol: str,
    title: str = "Candlestick Chart"
) -> io.BytesIO:
    """
    Wrapper rápido para candlestick.

    Args:
        data: DataFrame OHLCV
        symbol: Símbolo (ex: "BTC-USD")
        title: Título

    Returns:
        BytesIO com PNG
    """
    helper = ProChartHelper()
    return helper.candlestick_chart(data, title, symbol)


__all__ = [
    "ProChartHelper",
    "ChartTheme",
    "DARK_STYLE",
    "NIGHTCLOUDS_STYLE",
    "create_dark_style",
    "create_nightclouds_style",
    "create_hollow_filled_style",
    "create_candlestick_chart",
]
