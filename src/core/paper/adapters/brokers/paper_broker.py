"""Adapter - Paper Broker.

Implementa BrokerPort simulando execução de ordens com preços reais
do Yahoo Finance. Nenhum dinheiro real é movimentado.
"""
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from uuid import uuid4
from datetime import datetime

from ...ports.broker_port import BrokerPort
from ...ports.data_feed_port import DataFeedPort
from ...domain.currency import Currency
from ...domain.cashbook import CashBook, InsufficientFundsError

if TYPE_CHECKING:
    from ...ports.currency_converter_port import CurrencyConverterPort


class OrdemNaoEncontradaError(Exception):
    pass


class SaldoInsuficienteError(Exception):
    pass


class PaperBroker(BrokerPort):
    """Broker de paper trading com preços reais.

    Executa ordens simuladas usando cotações reais do Yahoo Finance.
    Suporta multi-moeda via CashBook e CurrencyConverterPort.

    Attributes:
        cashbook:  Livro de caixa multi-moeda.
        ordens:    Histórico de ordens enviadas.
        posicoes:  Posições abertas { ticker: { quantidade, preco_medio, currency } }.
    """

    def __init__(
        self,
        feed: DataFeedPort,
        converter: Optional["CurrencyConverterPort"] = None,
        cashbook: Optional[CashBook] = None,
        saldo_inicial: Decimal = Decimal("100000"),
    ):
        self._feed = feed
        self._converter = converter

        # Inicializa CashBook (compatibilidade: saldo_inicial → BRL)
        if cashbook is not None:
            self.cashbook = cashbook
        else:
            self.cashbook = CashBook.from_single_currency(Currency.BRL, saldo_inicial)

        # Compatibilidade: property saldo
        self.saldo_inicial: Decimal = saldo_inicial
        self._ordens: dict[str, dict] = {}
        self._posicoes: dict[str, dict] = {}
        self._conectado = False

    @property
    def saldo(self) -> Decimal:
        """Compatibilidade: retorna total em moeda base."""
        return self.cashbook.total_in_base_currency

    # ── Conexão ──────────────────────────────────────────────────────────────

    async def conectar(self) -> None:
        await self._feed.conectar()
        self._conectado = True

    async def desconectar(self) -> None:
        await self._feed.desconectar()
        self._conectado = False

    # ── Ordens ───────────────────────────────────────────────────────────────

    async def enviar_ordem(
        self,
        ticker: str,
        lado: str,
        quantidade: int,
        preco_limite: Optional[Decimal] = None,
    ) -> str:
        """Executa a ordem ao preço de mercado atual (real via Yahoo Finance).

        Args:
            ticker:       Código do ativo (ex: "PETR4.SA", "BTC-USD").
            lado:         "COMPRA" ou "VENDA".
            quantidade:   Número de unidades.
            preco_limite: Preço limite para execução. Se fornecido, usa esse preço
                     em vez do preço de mercado.

        Returns:
            ID da ordem executada.

        Raises:
            SaldoInsuficienteError: Se não houver saldo para a compra.
            ValueError:             Se o lado for inválido ou quantidade <= 0.
        """
        ticker = ticker.upper()
        lado = lado.upper()

        if lado not in ("COMPRA", "VENDA"):
            raise ValueError(f"Lado inválido: '{lado}'. Use 'COMPRA' ou 'VENDA'.")
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")

        if preco_limite is not None:
            preco_execucao = preco_limite
        else:
            cotacao = await self._feed.obter_cotacao(ticker)
            preco_execucao = cotacao.preco
        asset_currency = self._infer_currency(ticker)
        valor_total = preco_execucao * quantidade

        if lado == "COMPRA":
            # Tenta debitar da moeda do ativo primeiro
            if self.cashbook.has_sufficient_funds(asset_currency, valor_total):
                self.cashbook.subtract(asset_currency, valor_total)
            else:
                # Precisa converter: verifica se tem saldo total suficiente
                if self._converter is None:
                    # Sem conversor: usa verificação antiga (compatibilidade)
                    if valor_total > self.cashbook.total_in_base_currency:
                        raise SaldoInsuficienteError(
                            f"Saldo insuficiente. Necessário: {valor_total:.2f} | "
                            f"Disponível: {self.cashbook.total_in_base_currency:.2f}"
                        )
                    # Debita da moeda base
                    self.cashbook.subtract(self.cashbook.base_currency, valor_total)
                else:
                    # Com conversor: converte valor_total para base_currency
                    rate = await self._converter.get_rate(
                        asset_currency, self.cashbook.base_currency
                    )
                    valor_em_base = valor_total * rate

                    if valor_em_base > self.cashbook.total_in_base_currency:
                        raise SaldoInsuficienteError(
                            f"Saldo insuficiente. Necessário: {valor_em_base:.2f} "
                            f"{self.cashbook.base_currency.value} | "
                            f"Disponível: {self.cashbook.total_in_base_currency:.2f}"
                        )

                    # Converte e debita da moeda base (sem creditar na moeda do ativo)
                    # O valor em BRL já está sendo debitado como pagamento
                    self.cashbook.subtract(self.cashbook.base_currency, valor_em_base)

            self._atualizar_posicao_compra(ticker, quantidade, preco_execucao, asset_currency)

        elif lado == "VENDA":
            posicao = self._posicoes.get(ticker)
            if not posicao or posicao["quantidade"] < quantidade:
                qtd_atual = posicao["quantidade"] if posicao else 0
                raise ValueError(
                    f"Posição insuficiente em {ticker}. "
                    f"Solicitado: {quantidade} | Em carteira: {qtd_atual}"
                )

            # Creditifica na moeda do ativo
            pos_currency = Currency(posicao.get("currency", asset_currency.value))
            rate = Decimal("1")
            if self._converter is not None and pos_currency != self.cashbook.base_currency:
                rate = await self._converter.get_rate(pos_currency, self.cashbook.base_currency)

            self.cashbook.add(pos_currency, valor_total, rate)
            self._atualizar_posicao_venda(ticker, quantidade)

        ordem_id = str(uuid4())
        self._ordens[ordem_id] = {
            "id": ordem_id,
            "ticker": ticker,
            "lado": lado,
            "quantidade": quantidade,
            "preco_execucao": float(preco_execucao),
            "valor_total": float(valor_total),
            "currency": asset_currency.value,
            "status": "EXECUTADA",
            "timestamp": datetime.now().isoformat(),
        }
        return ordem_id

    def _infer_currency(self, ticker: str) -> Currency:
        """Infere moeda do ativo pelo ticker.

        Convenções:
        - Tickers brasileiros (.SA) → BRL
        - BTC-USD, ETH-USD → USD
        - Outros com hífen → segunda parte (BTC-BRL → BRL)
        - Default → USD
        """
        ticker = ticker.upper()

        # B3 (Brasil)
        if ticker.endswith(".SA"):
            return Currency.BRL

        # Cripto com par explícito
        if "-" in ticker:
            parts = ticker.split("-")
            quote_currency = parts[-1]
            try:
                return Currency(quote_currency)
            except ValueError:
                pass

        # Default USD
        return Currency.USD

    async def cancelar_ordem(self, ordem_id: str) -> bool:
        """Ordens paper são executadas instantaneamente — não há cancelamento."""
        if ordem_id not in self._ordens:
            raise OrdemNaoEncontradaError(f"Ordem '{ordem_id}' não encontrada.")
        return False

    async def consultar_ordem(self, ordem_id: str) -> dict:
        if ordem_id not in self._ordens:
            raise OrdemNaoEncontradaError(f"Ordem '{ordem_id}' não encontrada.")
        return self._ordens[ordem_id]

    async def obter_saldo(self) -> Decimal:
        return self.saldo

    # ── Posições ─────────────────────────────────────────────────────────────

    def listar_posicoes(self) -> list[dict]:
        """Retorna posições abertas com quantidade e preço médio."""
        return [
            {
                "ticker": ticker,
                "quantidade": dados["quantidade"],
                "preco_medio": round(dados["preco_medio"], 2),
                "custo_total": round(dados["quantidade"] * dados["preco_medio"], 2),
            }
            for ticker, dados in self._posicoes.items()
            if dados["quantidade"] > 0
        ]

    async def listar_posicoes_marcadas(self) -> list[dict]:
        """Posições marcadas a mercado com PnL calculado ao preço atual."""
        resultado = []
        for ticker, dados in self._posicoes.items():
            if dados["quantidade"] <= 0:
                continue
            cotacao = await self._feed.obter_cotacao(ticker)
            preco_atual = float(cotacao.preco)
            preco_medio = dados["preco_medio"]
            quantidade = dados["quantidade"]
            custo_total = quantidade * preco_medio
            valor_atual = quantidade * preco_atual
            pnl = valor_atual - custo_total
            pnl_pct = (pnl / custo_total * 100) if custo_total else 0

            # Moeda da posição
            currency = dados.get("currency", "USD")

            resultado.append({
                "ticker": ticker,
                "quantidade": quantidade,
                "preco_medio": round(preco_medio, 2),
                "preco_atual": round(preco_atual, 2),
                "custo_total": round(custo_total, 2),
                "valor_atual": round(valor_atual, 2),
                "pnl": round(pnl, 2),
                "pnl_percentual": round(pnl_pct, 2),
                "currency": currency,
            })
        return resultado

    def listar_ordens(self) -> list[dict]:
        """Retorna histórico de ordens executadas."""
        return list(self._ordens.values())

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _atualizar_posicao_compra(
        self, ticker: str, quantidade: int, preco: Decimal, currency: Currency
    ) -> None:
        """Atualiza posição com preço médio ponderado."""
        if ticker not in self._posicoes:
            self._posicoes[ticker] = {
                "quantidade": 0,
                "preco_medio": 0.0,
                "currency": currency.value,
            }

        pos = self._posicoes[ticker]
        qtd_anterior = pos["quantidade"]
        custo_anterior = qtd_anterior * pos["preco_medio"]
        custo_novo = quantidade * float(preco)

        pos["quantidade"] = qtd_anterior + quantidade
        pos["preco_medio"] = (custo_anterior + custo_novo) / pos["quantidade"]

    def _atualizar_posicao_venda(self, ticker: str, quantidade: int) -> None:
        """Reduz posição. Preço médio permanece inalterado."""
        self._posicoes[ticker]["quantidade"] -= quantidade
