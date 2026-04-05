# -*- coding: utf-8 -*-
"""
Discord Presentation - QuickChart Helper.

Gera gráficos visuais bonitos usando QuickChart API.
Gráficos são embedados como imagens no Discord.

QuickChart: https://quickchart.io/
"""

from decimal import Decimal
from typing import Any
import json
from urllib.parse import quote


# ═══════════════════════════════════════════════════════════════════════
# Chart Configurations
# ═══════════════════════════════════════════════════════════════════════

class ChartColors:
    """Cores para gráficos - baseadas no design Figma."""

    # Pie/Doughnut colors
    CRYPTO = "#F59E0B"     # Laranja
    STOCKS = "#6366F1"     # Índigo
    FIIS = "#8B5CF6"       # Roxo
    SUCCESS = "#22C55E"    # Verde
    DANGER = "#EF4444"     # Vermelho

    @classmethod
    def for_tipo(cls, tipo: str) -> str:
        """Retorna cor para tipo de ativo."""
        return {
            "Cripto": cls.CRYPTO,
            "Ações": cls.STOCKS,
            "FIIs": cls.FIIS,
        }.get(tipo, "#6B7280")  # Cinza padrão


class QuickChartHelper:
    """
    Helper para gerar URLs de gráficos QuickChart.

    Uso:
        helper = QuickChartHelper()
        url = helper.pie_chart(alocacao)
        await interaction.response.send_message(url)
    """

    BASE_URL = "https://quickchart.io/chart"

    def __init__(self, width: int = 500, height: int = 300):
        """
        Inicializa helper.

        Args:
            width: Largura do gráfico (padrão: 500px)
            height: Altura do gráfico (padrão: 300px)
        """
        self.width = width
        self.height = height

    def pie_chart(
        self,
        labels: list[str],
        values: list[float | Decimal],
        colors: list[str] | None = None,
        title: str = "Alocação"
    ) -> str:
        """
        Gera URL de gráfico de pizza (pie chart).

        Args:
            labels: Labels das fatias
            values: Valores das fatias
            colors: Cores (opcional, usa padrão se None)
            title: Título do gráfico

        Returns:
            URL do gráfico QuickChart
        """
        # Converte Decimal para float se necessário
        values_float = [float(v) for v in values]

        # Cores padrão se não fornecidas
        if colors is None:
            colors = [
                ChartColors.CRYPTO,
                ChartColors.STOCKS,
                ChartColors.FIIS,
                "#10B981",  # Verde esmeralda
                "#EC4899",  # Rosa
            ]

        config = {
            "type": "pie",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values_float,
                    "backgroundColor": colors[:len(labels)],
                    "borderColor": "#1F2937",  # Borda escura
                    "borderWidth": 2,
                }]
            },
            "options": {
                "title": {
                    "display": True,
                    "text": title,
                    "fontColor": "#FFFFFF",
                    "fontSize": 16,
                },
                "legend": {
                    "position": "bottom",
                    "labels": {
                        "fontColor": "#FFFFFF",
                        "padding": 15,
                    }
                }
            },
            "backgroundColor": "#1F2937",  # Fundo escuro
        }

        return self._build_url(config)

    def doughnut_chart(
        self,
        labels: list[str],
        values: list[float | Decimal],
        colors: list[str] | None = None,
        title: str = "Alocação"
    ) -> str:
        """
        Gera URL de gráfico de rosca (doughnut chart).

        Mesmo parâmetros do pie_chart, mas visual diferente.
        """
        # Converte Decimal para float se necessário
        values_float = [float(v) for v in values]

        # Cores padrão se não fornecidas
        if colors is None:
            colors = [
                ChartColors.CRYPTO,
                ChartColors.STOCKS,
                ChartColors.FIIS,
                "#10B981",
                "#EC4899",
            ]

        config = {
            "type": "doughnut",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values_float,
                    "backgroundColor": colors[:len(labels)],
                    "borderColor": "#1F2937",
                    "borderWidth": 2,
                }]
            },
            "options": {
                "title": {
                    "display": True,
                    "text": title,
                    "fontColor": "#FFFFFF",
                    "fontSize": 16,
                },
                "legend": {
                    "position": "bottom",
                    "labels": {
                        "fontColor": "#FFFFFF",
                        "padding": 15,
                    }
                },
                "cutoutPercentage": 60,  # Tamanho do buraco central
            },
            "backgroundColor": "#1F2937",
        }

        return self._build_url(config)

    def bar_chart(
        self,
        labels: list[str],
        values: list[float | Decimal],
        colors: list[str] | None = None,
        title: str = "Comparação"
    ) -> str:
        """
        Gera URL de gráfico de barras (bar chart).

        Args:
            labels: Labels das barras
            values: Valores das barras
            colors: Cores das barras
            title: Título do gráfico

        Returns:
            URL do gráfico QuickChart
        """
        values_float = [float(v) for v in values]

        # Cores baseadas em valor (positivo=verde, negativo=vermelho)
        if colors is None:
            colors = [
                ChartColors.SUCCESS if v >= 0 else ChartColors.DANGER
                for v in values_float
            ]

        config = {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": title,
                    "data": values_float,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "borderWidth": 1,
                }]
            },
            "options": {
                "title": {
                    "display": True,
                    "text": title,
                    "fontColor": "#FFFFFF",
                    "fontSize": 16,
                },
                "scales": {
                    "yAxes": [{
                        "ticks": {
                            "fontColor": "#FFFFFF",
                        },
                        "gridLines": {
                            "color": "#374151",
                        }
                    }],
                    "xAxes": [{
                        "ticks": {
                            "fontColor": "#FFFFFF",
                        },
                        "gridLines": {
                            "color": "#374151",
                        }
                    }]
                },
                "legend": {
                    "display": False,
                }
            },
            "backgroundColor": "#1F2937",
        }

        return self._build_url(config)

    def line_chart(
        self,
        labels: list[str],
        datasets: list[dict[str, Any]],
        title: str = "Evolução"
    ) -> str:
        """
        Gera URL de gráfico de linha (line chart).

        Args:
            labels: Labels do eixo X (ex: datas)
            datasets: Lista de datasets com formato:
                {
                    "label": "Nome",
                    "data": [valores],
                    "color": "#HEX" (opcional)
                }
            title: Título do gráfico

        Returns:
            URL do gráfico QuickChart
        """
        # Cores padrão para datasets
        colors = [ChartColors.CRYPTO, ChartColors.STOCKS, ChartColors.FIIS, "#10B981"]

        chart_datasets = []
        for i, ds in enumerate(datasets):
            data = [float(v) for v in ds["data"]]
            chart_datasets.append({
                "label": ds["label"],
                "data": data,
                "borderColor": ds.get("color", colors[i % len(colors)]),
                "backgroundColor": ds.get("color", colors[i % len(colors)]),
                "fill": False,
                "tension": 0.3,  # Curva suave
            })

        config = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": chart_datasets,
            },
            "options": {
                "title": {
                    "display": True,
                    "text": title,
                    "fontColor": "#FFFFFF",
                    "fontSize": 16,
                },
                "scales": {
                    "yAxes": [{
                        "ticks": {
                            "fontColor": "#FFFFFF",
                        },
                        "gridLines": {
                            "color": "#374151",
                        }
                    }],
                    "xAxes": [{
                        "ticks": {
                            "fontColor": "#FFFFFF",
                        },
                        "gridLines": {
                            "color": "#374151",
                        }
                    }]
                },
                "legend": {
                    "display": True,
                    "position": "top",
                    "labels": {
                        "fontColor": "#FFFFFF",
                    }
                }
            },
            "backgroundColor": "#1F2937",
        }

        return self._build_url(config)

    def _build_url(self, config: dict) -> str:
        """
        Constrói URL completa do QuickChart.

        Args:
            config: Configuração do gráfico Chart.js

        Returns:
            URL completa
        """
        config_json = json.dumps(config, separators=(",", ":"))
        encoded = quote(config_json, safe="")

        url = f"{self.BASE_URL}?c={encoded}&width={self.width}&height={self.height}"

        return url


# ═══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════

def create_alocacao_chart(alocacao: dict[str, Decimal]) -> str:
    """
    Cria gráfico de alocação por tipo.

    Args:
        alocacao: Dict com {tipo: valor}

    Returns:
        URL do gráfico doughnut
    """
    helper = QuickChartHelper(width=400, height=250)

    # Remove "total" do dict se presente
    data = {k: v for k, v in alocacao.items() if k != "total"}

    labels = list(data.keys())
    values = list(data.values())
    colors = [ChartColors.for_tipo(t) for t in labels]

    return helper.doughnut_chart(
        labels=labels,
        values=values,
        colors=colors,
        title="Alocação por Tipo"
    )


def create_pnl_chart(ativos: list[dict]) -> str:
    """
    Cria gráfico de barras de PnL por ativo.

    Args:
        ativos: Lista de dicts com {"ticker": str, "pnl": Decimal}

    Returns:
        URL do gráfico de barras
    """
    helper = QuickChartHelper(width=500, height=300)

    labels = [a["ticker"] for a in ativos]
    values = [a["pnl"] for a in ativos]

    return helper.bar_chart(
        labels=labels,
        values=values,
        title="Lucro/Prejuízo por Ativo"
    )


__all__ = [
    "QuickChartHelper",
    "ChartColors",
    "create_alocacao_chart",
    "create_pnl_chart",
]
