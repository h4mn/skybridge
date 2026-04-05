# -*- coding: utf-8 -*-
"""
Demo - Painel Portfolio Discord Completo.

Simula o painel interativo do Portfolio com botões.
"""

import asyncio
import sys
from decimal import Decimal

# Fix UTF-8 no Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from src.core.discord.presentation.portfolio_views import (
    PortfolioMainView,
    PortfolioReadModel,
    AssetCardReadModel,
    PortfolioColors,
)


def create_sample_portfolio() -> PortfolioReadModel:
    """Cria portfolio de exemplo."""
    return PortfolioReadModel(
        valor_total=Decimal("160730.00"),
        valor_investido=Decimal("149640.00"),
        lucro_prejuizo=Decimal("11090.00"),
        lucro_prejuizo_percentual=7.41,
        ativos=[
            AssetCardReadModel(
                ticker="BTC",
                nome="Bitcoin",
                tipo="Cripto",
                variação_percentual=8.33,
                quantidade=Decimal("0.5"),
                preco_medio=Decimal("180000.00"),
                preco_atual=Decimal("195000.00"),
                valor_total=Decimal("97500.00"),
                lucro_prejuizo=Decimal("7500.00"),
            ),
            AssetCardReadModel(
                ticker="ETH",
                nome="Ethereum",
                tipo="Cripto",
                variação_percentual=7.37,
                quantidade=Decimal("2"),
                preco_medio=Decimal("9500.00"),
                preco_atual=Decimal("10200.00"),
                valor_total=Decimal("20400.00"),
                lucro_prejuizo=Decimal("1400.00"),
            ),
            AssetCardReadModel(
                ticker="HGLG11",
                nome="CSHG Logística",
                tipo="FII",
                variação_percentual=4.55,
                quantidade=Decimal("200"),
                preco_medio=Decimal("165.00"),
                preco_atual=Decimal("172.50"),
                valor_total=Decimal("34500.00"),
                lucro_prejuizo=Decimal("1500.00"),
            ),
            AssetCardReadModel(
                ticker="MXRF11",
                nome="Maxi Renda",
                tipo="FII",
                variação_percentual=6.37,
                quantidade=Decimal("150"),
                preco_medio=Decimal("10.20"),
                preco_atual=Decimal("10.85"),
                valor_total=Decimal("1627.50"),
                lucro_prejuizo=Decimal("97.50"),
            ),
            AssetCardReadModel(
                ticker="PETR4",
                nome="Petrobras PN",
                tipo="Ação",
                variação_percentual=15.09,
                quantidade=Decimal("100"),
                preco_medio=Decimal("28.50"),
                preco_atual=Decimal("32.80"),
                valor_total=Decimal("3280.00"),
                lucro_prejuizo=Decimal("430.00"),
            ),
            AssetCardReadModel(
                ticker="VALE3",
                nome="Vale ON",
                tipo="Ação",
                variação_percentual=4.98,
                quantidade=Decimal("50"),
                preco_medio=Decimal("65.20"),
                preco_atual=Decimal("68.45"),
                valor_total=Decimal("3422.50"),
                lucro_prejuizo=Decimal("162.50"),
            ),
        ],
        alocacao_por_tipo={
            "Cripto": Decimal("117900.00"),
            "Ações": Decimal("6702.50"),
            "FIIs": Decimal("36127.50"),
            "total": Decimal("160730.00"),
        },
    )


def show_main_panel(portfolio: PortfolioReadModel):
    """Mostra painel principal."""
    total = portfolio.valor_total
    invested = portfolio.valor_investido
    pnl = portfolio.lucro_prejuizo
    pnl_percent = portfolio.lucro_prejuizo_percentual

    color_emoji = "🟢" if pnl >= 0 else "🔴"
    pnl_sign = "+" if pnl >= 0 else ""

    print("\n" + "=" * 60)
    print("📊 MEU PORTFÓLIO")
    print("=" * 60)
    print(f"💰 Valor Total:      R$ {total:,.2f}")
    print(f"💵 Investido:       R$ {invested:,.2f}")
    print(f"📈 Lucro/Prejuízo:   {color_emoji} R$ {pnl:,.2f} ({pnl_sign}{pnl_percent:.2f}%)")
    print(f"📊 Ativos:         {len(portfolio.ativos)}")

    print("\n" + "─" * 60)
    print("BOTÕES DE AÇÃO:")
    print("─" * 60)
    print("  [💰 Saldo/Posições]     Mostra saldo e posições atuais")
    print("  [📊 Portfolio Completo]  Lista todos os ativos com detalhes")
    print("  [📈 Ver Alocação]      Gráfico de alocação por tipo")
    print("  [⚙️  Configurações]      Configurações do portfolio")
    print("=" * 60)


def show_saldo(portfolio: PortfolioReadModel):
    """Mostra saldo e posições."""
    print("\n" + "=" * 60)
    print("💰 SALDO E POSIÇÕES")
    print("=" * 60)
    print(f"Valor Total:    R$ {portfolio.valor_total:,.2f}")
    print(f"Investido:      R$ {portfolio.valor_investido:,.2f}")
    print(f"Lucro/PnL:      R$ {portfolio.lucro_prejuizo:,.2f}")
    print(f"PnL %:         {portfolio.lucro_prejuizo_percentual:+.2f}%")
    print(f"Ativos:        {len(portfolio.ativos)}")
    print("=" * 60)


def show_assets(portfolio: PortfolioReadModel):
    """Mostra todos os ativos."""
    print("\n" + "=" * 60)
    print("📊 PORTFOLIO COMPLETO")
    print("=" * 60)

    for ativo in portfolio.ativos:
        var_emoji = "📈" if ativo.variação_percentual >= 0 else "📉"
        tipo_emoji = {"Cripto": "₿", "Ação": "📈", "FII": "🏢"}.get(ativo.tipo, "📊")

        print(f"\n{tipo_emoji} {ativo.ticker} - {ativo.nome}")
        print(f"   Tipo:       {ativo.tipo}")
        print(f"   Variação:    {var_emoji} {ativo.variação_percentual:+.2f}%")
        print(f"   Qtd:        {ativo.quantidade}")
        print(f"   Preço Méd:  R$ {ativo.preco_medio:,.2f}")
        print(f"   Preço Atual: R$ {ativo.preco_atual:,.2f}")
        print(f"   Total:      R$ {ativo.valor_total:,.2f}")
        print(f"   PnL:        R$ {ativo.lucro_prejuizo:,.2f}")

    print("\n" + "=" * 60)


def show_alocacao(portfolio: PortfolioReadModel):
    """Mostra alocação por tipo."""
    alloc = portfolio.alocacao_por_tipo
    total = alloc.get("total", Decimal("1"))

    print("\n" + "=" * 60)
    print("📈 ALOCAÇÃO POR TIPO")
    print("=" * 60)

    for tipo, valor in alloc.items():
        if tipo == "total":
            continue

        percent = (valor / total * 100) if total > 0 else 0
        emoji = {"Cripto": "₿", "Ações": "📈", "FIIs": "🏢"}.get(tipo, "📊")

        # Barra visual
        bars = "█" * int(percent / 5)
        print(f"{emoji} {tipo:10s} {bars} {percent:5.1f}%  R$ {valor:,.2f}")

    print("\n" + f"Total: R$ {total:,.2f}")
    print("=" * 60)


def main():
    """Executa demo do painel."""
    portfolio = create_sample_portfolio()
    view = PortfolioMainView(portfolio)

    # Menu interativo
    while True:
        show_main_panel(portfolio)

        print("\nDigite a opção:")
        print("  1 - 💰 Saldo/Posições")
        print("  2 - 📊 Portfolio Completo")
        print("  3 - 📈 Ver Alocação")
        print("  0 - Sair")

        choice = input("\n> ").strip()

        if choice == "1":
            show_saldo(portfolio)
            input("\n[Enter] para voltar...")
        elif choice == "2":
            show_assets(portfolio)
            input("\n[Enter] para voltar...")
        elif choice == "3":
            show_alocacao(portfolio)
            input("\n[Enter] para voltar...")
        elif choice == "0":
            print("\n👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")


if __name__ == "__main__":
    print("\n🎮 DEMO - Painel Portfolio Discord")
    print("=" * 60)
    print("Simulação interativa do painel no terminal.")
    print("No Discord, seriam botões clicáveis!\n")
    main()
