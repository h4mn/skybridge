# -*- coding: utf-8 -*-
"""Adapter - Paper Broker com persistência delegada ao PaperStatePort."""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from .paper_broker import PaperBroker
from ...ports.data_feed_port import DataFeedPort
from ...ports.paper_state_port import PaperStatePort
from ...domain.cashbook import CashBook
from ...domain.currency import Currency

if TYPE_CHECKING:
    from ...ports.currency_converter_port import CurrencyConverterPort


class StatefulPaperBroker(PaperBroker):
    """Paper Broker com persistência delegada ao PaperStatePort.

    Toda persistência é delegada ao PaperStatePort injetado (SQLite).
    Suporta CashBook multi-moeda sincronizado com PaperState.
    """

    def __init__(
        self,
        feed: DataFeedPort,
        paper_state: PaperStatePort,
        converter: Optional["CurrencyConverterPort"] = None,
        saldo_inicial: Decimal = Decimal("100000"),
    ):
        # Inicializa PaperBroker com dependências
        super().__init__(
            feed=feed,
            converter=converter,
            cashbook=None,  # Será carregado do estado
            saldo_inicial=saldo_inicial,
        )
        self._paper_state = paper_state
        # Carrega estado do PaperStatePort
        self._load_from_state()

    def _load_from_state(self) -> None:
        """Carrega estado do PaperStatePort."""
        estado = self._paper_state.carregar()

        # Sincroniza saldo do broker com estado
        self.saldo_inicial = estado.saldo_inicial
        self._ordens = estado.ordens.copy()
        self._posicoes = estado.posicoes.copy()

        # Carrega CashBook do estado (se existir)
        if hasattr(estado, "cashbook") and estado.cashbook:
            self.cashbook = CashBook.from_dict(estado.cashbook)
        else:
            # Compatibilidade: cria CashBook a partir do saldo
            base_currency = getattr(estado, "base_currency", Currency.BRL)
            if isinstance(base_currency, str):
                base_currency = Currency(base_currency)
            self.cashbook = CashBook.from_single_currency(base_currency, estado.saldo)

    def reload(self) -> None:
        """Recarrega estado do arquivo (público).

        Use quando o estado foi modificado externamente (ex: reset via handler).
        """
        self._load_from_state()

    def _save_to_state(self) -> None:
        """Salva estado no PaperStatePort."""
        estado = self._paper_state.carregar()

        # Atualiza campos do broker (saldo agora e calculado do cashbook)
        estado.saldo_inicial = self.saldo_inicial
        estado.ordens = self._ordens.copy()
        estado.posicoes = self._posicoes.copy()

        # Salva CashBook no estado (saldo e derivado)
        estado.cashbook = self.cashbook.to_dict()

        self._paper_state.salvar(estado)

    async def enviar_ordem(
        self,
        ticker: str,
        lado: str,
        quantidade: int,
        preco_limite: Optional[Decimal] = None,
    ) -> str:
        """Envia ordem e persiste estado via PaperStatePort."""
        # Recarrega estado antes de executar
        self._load_from_state()
        ordem_id = await super().enviar_ordem(ticker, lado, quantidade, preco_limite)
        self._save_to_state()
        return ordem_id
