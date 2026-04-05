# -*- coding: utf-8 -*-
"""Handler para processar ConsultarPortfolioQuery com marcação a mercado."""
from decimal import Decimal

from ..queries.consultar_portfolio import ConsultarPortfolioQuery, PortfolioResult
from ...ports.broker_port import BrokerPort
from ...ports.data_feed_port import DataFeedPort
from ...ports.currency_converter_port import CurrencyConverterPort
from ...domain.currency import Currency
from ...domain.money import Money


class ConsultarPortfolioHandler:
    """Handler para consultas de portfolio com marcação a mercado.

    Calcula PnL marcando posições ao preço atual de mercado.
    Suporta conversão para moeda alvo via base_currency.
    """

    def __init__(
        self,
        broker: BrokerPort,
        feed: DataFeedPort,
        converter: CurrencyConverterPort,
    ):
        self._broker = broker
        self._feed = feed
        self._converter = converter

    async def handle(self, query: ConsultarPortfolioQuery) -> PortfolioResult:
        """Processa a query de portfolio.

        Args:
            query: Query (portfolio_id opcional, base_currency opcional)

        Returns:
            PortfolioResult com PnL calculado na moeda solicitada + cashbook
        """
        # Recarrega estado do broker antes de ler (sync com arquivo)
        if hasattr(self._broker, "reload"):
            self._broker.reload()

        # Obtém cashbook do broker (multi-moeda)
        broker_cashbook = self._broker.cashbook
        base_currency = broker_cashbook.base_currency

        # Converte cashbook para dict serializável
        cashbook_dict = {
            "base_currency": base_currency.value,
            "entries": [],
            "total_in_base_currency": float(broker_cashbook.total_in_base_currency),
        }
        for currency, entry in broker_cashbook.entries.items():
            cashbook_dict["entries"].append({
                "currency": currency.value,
                "amount": float(entry.amount),
                "conversion_rate": float(entry.conversion_rate),
                "value_in_base_currency": float(entry.value_in_base_currency),
            })

        # Obtém posições marcadas a mercado
        posicoes = await self._broker.listar_posicoes_marcadas()

        # Calcula valor total do portfolio (cashbook + posições)
        valor_posicoes = Decimal(str(sum(p["valor_atual"] for p in posicoes)))
        valor_total = broker_cashbook.total_in_base_currency + valor_posicoes

        # PnL: valor total - saldo inicial
        saldo_inicial = Decimal(str(getattr(self._broker, "saldo_inicial", Decimal("100000"))))
        pnl = valor_total - saldo_inicial
        pnl_percentual = (pnl / saldo_inicial * 100) if saldo_inicial else Decimal("0")

        # Moeda nativa do portfolio (base do cashbook)
        native_currency = base_currency
        target_currency = query.base_currency or native_currency

        # Converte se necessário
        if target_currency != native_currency:
            # Converte saldo_total
            money_total = Money(valor_total, native_currency)
            converted_total = await self._converter.convert(money_total, target_currency)
            valor_total = converted_total.amount

            # Converte saldo_inicial
            money_inicial = Money(saldo_inicial, native_currency)
            converted_inicial = await self._converter.convert(money_inicial, target_currency)
            saldo_inicial = converted_inicial.amount

            # Recalcula PnL na nova moeda
            pnl = valor_total - saldo_inicial
            pnl_percentual = (pnl / saldo_inicial * 100) if saldo_inicial else Decimal("0")

        return PortfolioResult(
            id=query.portfolio_id or "default",
            nome="Portfolio Principal",
            saldo_inicial=float(saldo_inicial),
            saldo_atual=float(valor_total),
            pnl=float(pnl),
            pnl_percentual=float(pnl_percentual),
            currency=target_currency,
            cashbook=cashbook_dict,
            base_currency=base_currency.value,
        )
