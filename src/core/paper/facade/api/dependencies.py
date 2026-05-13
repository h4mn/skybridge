# -*- coding: utf-8 -*-
"""
Dependencies - Paper Trading API

Injeção de dependências para as rotas FastAPI.

Este módulo configura a injeção de dependências para:
- PaperState: Persistência unificada do estado
- Broker: Execução de ordens
- DataFeed: Dados de mercado
- CurrencyConverter: Conversão de moedas
- Handlers: Orquestração de commands/queries
"""
from functools import lru_cache
from decimal import Decimal

from fastapi import Depends

from ...adapters.persistence.sqlite_paper_state import SQLitePaperState
from ...adapters.brokers.stateful_broker import StatefulPaperBroker
from ...adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
from ...adapters.currency.yahoo_currency_adapter import YahooCurrencyAdapter
from ...application.handlers.criar_ordem_handler import CriarOrdemHandler
from ...application.handlers.depositar_handler import DepositarHandler
from ...application.handlers.resetar_handler import ResetarHandler
from ...application.handlers.consultar_cotacao_handler import ConsultarCotacaoHandler
from ...application.handlers.consultar_historico_handler import ConsultarHistoricoHandler
from ...application.handlers.consultar_portfolio_handler import ConsultarPortfolioHandler
from ...application.handlers.consultar_ordens_handler import ConsultarOrdensHandler
from ...ports.paper_state_port import PaperStatePort
from ...ports.currency_converter_port import CurrencyConverterPort


# ==================== Infrastructure ====================

SALDO_INICIAL = Decimal("100000")
PAPER_STATE_DB = "paper_state.db"


# @lru_cache  # REMOVIDO: pode causar problemas de concorrência
def get_paper_state() -> PaperStatePort:
    """Retorna instância do PaperState (SQLite com fallback JSON)."""
    return SQLitePaperState(PAPER_STATE_DB)


# @lru_cache  # REMOVIDO: evitar problemas de concorrência
def get_feed() -> YahooFinanceFeed:
    """Retorna instância do DataFeed."""
    return YahooFinanceFeed()


# @lru_cache  # REMOVIDO: evitar problemas de concorrência
def get_currency_converter() -> CurrencyConverterPort:
    """Retorna instância do CurrencyConverter."""
    return YahooCurrencyAdapter()


def get_broker(
    paper_state: PaperStatePort = Depends(get_paper_state),
    feed: YahooFinanceFeed = Depends(get_feed),
    converter: YahooCurrencyAdapter = Depends(get_currency_converter),
) -> StatefulPaperBroker:
    """Retorna instância do broker com DI (SEM CACHE).

    Cada request cria uma nova instância que lê o estado atualizado do SQLite.
    Isso garante sincronização com mudanças externas.
    """
    return StatefulPaperBroker(
        feed=feed,
        paper_state=paper_state,
        converter=converter,
        saldo_inicial=SALDO_INICIAL,
    )


# ==================== Command Handlers ====================


def get_criar_ordem_handler(
    broker: StatefulPaperBroker = Depends(get_broker),
) -> CriarOrdemHandler:
    """Retorna handler para criação de ordens."""
    return CriarOrdemHandler(broker)


def get_depositar_handler(
    paper_state: PaperStatePort = Depends(get_paper_state),
) -> DepositarHandler:
    """Retorna handler para depósitos."""
    return DepositarHandler(paper_state)


def get_resetar_handler(
    paper_state: PaperStatePort = Depends(get_paper_state),
) -> ResetarHandler:
    """Retorna handler para reset."""
    return ResetarHandler(paper_state)


# ==================== Query Handlers ====================


def get_consultar_cotacao_handler(
    feed: YahooFinanceFeed = Depends(get_feed),
) -> ConsultarCotacaoHandler:
    """Retorna handler para consulta de cotação."""
    return ConsultarCotacaoHandler(feed)


def get_consultar_historico_handler(
    feed: YahooFinanceFeed = Depends(get_feed),
) -> ConsultarHistoricoHandler:
    """Retorna handler para consulta de histórico."""
    return ConsultarHistoricoHandler(feed)


def get_consultar_portfolio_handler(
    broker: StatefulPaperBroker = Depends(get_broker),
    feed: YahooFinanceFeed = Depends(get_feed),
    converter: YahooCurrencyAdapter = Depends(get_currency_converter),
) -> ConsultarPortfolioHandler:
    """Retorna handler para consulta de portfolio."""
    return ConsultarPortfolioHandler(broker, feed, converter)


def get_consultar_ordens_handler(
    broker: StatefulPaperBroker = Depends(get_broker),
    paper_state: PaperStatePort = Depends(get_paper_state),
) -> ConsultarOrdensHandler:
    """Retorna handler para consulta de ordens."""
    return ConsultarOrdensHandler(broker, paper_state)
