# -*- coding: utf-8 -*-
"""Testes para YahooFinanceFeed — TTL Cache e Backoff exponencial."""

import asyncio
import time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.paper.adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
from src.core.paper.ports.data_feed_port import Cotacao


def _make_cotacao(ticker="BTC-USD", preco=50000.0) -> Cotacao:
    return Cotacao(ticker=ticker, preco=Decimal(str(preco)), volume=1000, timestamp="2026-05-09T10:00:00")


class TestYahooFinanceFeedTTLCache:
    """DOC: specs/paper-guardiao-v2 — TTL Cache evita request duplicado."""

    @pytest.mark.asyncio
    async def test_cache_hit_retorna_sem_chamar_yahoo(self):
        """WHEN cotação em cache dentro do TTL THEN não chama _buscar_cotacao."""
        feed = YahooFinanceFeed(ttl_seconds=30.0)
        cotacao = _make_cotacao()

        # Pré-popular cache
        feed._cache["BTC-USD"] = (time.monotonic(), cotacao)

        with patch.object(feed, '_buscar_cotacao') as mock_buscar:
            result = await feed.obter_cotacao("BTC-USD")
            mock_buscar.assert_not_called()
            assert result.preco == cotacao.preco

    @pytest.mark.asyncio
    async def test_cache_miss_chama_yahoo(self):
        """WHEN cache vazio THEN chama _buscar_cotacao."""
        feed = YahooFinanceFeed(ttl_seconds=30.0)
        cotacao = _make_cotacao()

        with patch.object(feed, '_buscar_cotacao', return_value=cotacao):
            result = await feed.obter_cotacao("BTC-USD")
            assert result.preco == cotacao.preco

    @pytest.mark.asyncio
    async def test_cache_expirado_busca_novamente(self):
        """WHEN cache expirado (além do TTL) THEN busca nova cotação."""
        feed = YahooFinanceFeed(ttl_seconds=1.0)
        cotacao_velha = _make_cotacao(preco=40000.0)
        cotacao_nova = _make_cotacao(preco=50000.0)

        # Cache com timestamp antigo (expirado)
        feed._cache["BTC-USD"] = (time.monotonic() - 10.0, cotacao_velha)

        with patch.object(feed, '_buscar_cotacao', return_value=cotacao_nova):
            result = await feed.obter_cotacao("BTC-USD")
            assert result.preco == Decimal("50000")


class TestYahooFinanceFeedBackoff:
    """DOC: specs/paper-guardiao-v2 — Backoff exponencial em rate limit."""

    @pytest.mark.asyncio
    async def test_retry_3_vezes_antes_falhar(self):
        """WHEN Yahoo falha 3 vezes THEN raising após 3 tentativas."""
        feed = YahooFinanceFeed(ttl_seconds=0.0)

        with patch.object(feed, '_buscar_cotacao', side_effect=Exception("429 Too Many Requests")):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                with pytest.raises(Exception, match="429"):
                    await feed.obter_cotacao("BTC-USD")
                # Deve ter chamado sleep 2 vezes (tentativas 0 e 1, na 2 raise)
                assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_sucesso_na_segunda_tentativa(self):
        """WHEN primeira falha THEN retry e sucesso na segunda."""
        feed = YahooFinanceFeed(ttl_seconds=0.0)
        cotacao = _make_cotacao()

        call_count = [0]
        def _buscar_side_effect(ticker):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("timeout")
            return cotacao

        with patch.object(feed, '_buscar_cotacao', side_effect=_buscar_side_effect):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await feed.obter_cotacao("BTC-USD")
                assert result.preco == Decimal("50000")
                assert call_count[0] == 2
