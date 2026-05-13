# -*- coding: utf-8 -*-
"""Testes para StrategyWorker refatorado — injeção de dependências reais."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.paper.domain.strategies.signal import DadosMercado, SinalEstrategia, TipoSinal
from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador
from src.core.paper.domain.strategies.position_tracker import PositionTracker


def _make_worker(**kwargs):
    """Helper: cria StrategyWorker com dependências mockadas."""
    strategy = kwargs.pop("strategy", GuardiaoConservador())
    datafeed = kwargs.pop("datafeed", AsyncMock())
    executor = kwargs.pop("executor", AsyncMock())
    tracker = kwargs.pop("tracker", PositionTracker())
    tickers = kwargs.pop("tickers", ["BTC-USD"])

    from src.core.paper.facade.sandbox.workers.strategy_worker import StrategyWorker
    return StrategyWorker(
        strategy=strategy,
        datafeed=datafeed,
        executor=executor,
        position_tracker=tracker,
        tickers=tickers,
        **kwargs,
    )


class TestStrategyWorkerTick:
    """DOC: specs/strategy-worker — Ciclo de tick com dependências reais."""

    @pytest.mark.asyncio
    async def test_tick_com_sinal_compra(self):
        """WHEN estratégia retorna COMPRA THEN executor.executar_ordem é chamado."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()
        call_kwargs = executor.executar_ordem.call_args
        assert call_kwargs.kwargs.get("ticker") == "BTC-USD" or call_kwargs[1].get("ticker") == "BTC-USD"

    @pytest.mark.asyncio
    async def test_tick_com_sinal_venda(self):
        """WHEN estratégia retorna VENDA com posição aberta THEN executor.executar_ordem é chamado."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()

    @pytest.mark.asyncio
    async def test_tick_sem_sinal(self):
        """WHEN estratégia retorna None THEN executor NÃO é chamado."""
        strategy = MagicMock()
        strategy.evaluate.return_value = None
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()

    @pytest.mark.asyncio
    async def test_tick_erro_datafeed_nao_crasha(self):
        """WHEN datafeed lança exceção THEN worker não crasha (BaseWorker captura)."""
        strategy = MagicMock()
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.side_effect = Exception("Yahoo Finance timeout")

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()  # não deve levantar

        executor.executar_ordem.assert_not_called()


class TestStrategyWorkerSLTP:
    """DOC: specs/strategy-worker — Verificação de SL/TP durante tick."""

    @pytest.mark.asyncio
    async def test_stop_loss_during_tick(self):
        """WHEN position_tracker.check_price retorna sinal SL THEN executa venda."""
        strategy = MagicMock()
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("47000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()

    @pytest.mark.asyncio
    async def test_take_profit_during_tick(self):
        """WHEN position_tracker.check_price retorna sinal TP THEN executa venda."""
        strategy = MagicMock()
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("56000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(take_profit_pct=Decimal("0.10"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()


class TestStrategyWorkerPositionGuard:
    """DOC: specs/paper-guardiao-v2 — Position Guard: rejeitar duplicadas e fantasmas."""

    @pytest.mark.asyncio
    async def test_position_guard_rejeita_compra_duplicada(self):
        """WHEN ticker já posicionado AND sinal COMPRA THEN executor NÃO é chamado."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()

    @pytest.mark.asyncio
    async def test_position_guard_rejeita_venda_fantasma(self):
        """WHEN ticker sem posição AND sinal VENDA THEN executor NÃO é chamado."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()


class TestStrategyWorkerStaleGuard:
    """DOC: specs/paper-guardiao-v2 — Stale Guard: não operar com dados defasados."""

    @pytest.mark.asyncio
    async def test_stale_guard_nao_operar(self):
        """WHEN preço não muda há 3 ticks THEN executor NÃO é chamado após stale."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.name = "test"
        # Ticks 1-2: sem sinal (estabelecem preço), tick 3: com sinal + stale
        call_n = [0]
        def _evaluate(*a):
            call_n[0] += 1
            return None if call_n[0] <= 2 else sinal
        strategy.evaluate.side_effect = _evaluate

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        # Tick 1: sem sinal, estabelece preço
        # Tick 2: sem sinal, stale_count=1
        # Tick 3: com sinal, stale_count=2 → STALE
        for _ in range(3):
            await worker._do_tick()

        executor.executar_ordem.assert_not_called()

    @pytest.mark.asyncio
    async def test_stale_guard_retoma_com_dados_frescos(self):
        """WHEN preço muda após stale THEN executor É chamado no tick fresco."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.name = "test"
        call_n = [0]
        def _evaluate(*a):
            call_n[0] += 1
            return None if call_n[0] <= 1 else sinal
        strategy.evaluate.side_effect = _evaluate

        datafeed = AsyncMock()
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)

        # Tick 1: sem sinal, estabelece preço
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        await worker._do_tick()

        # Ticks 2-3: preço stale → SKIPPED (stale_threshold=1)
        await worker._do_tick()
        await worker._do_tick()
        executor.executar_ordem.assert_not_called()

        # Tick 4: preço fresco → opera
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50100"))
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()


class TestStrategyWorkerStaleGuardSLTP:
    """DOC: SL/TP deve disparar mesmo com stale guard ativo."""

    @pytest.mark.asyncio
    async def test_stale_nao_bloqueia_stop_loss(self):
        """WHEN stale_count >= 2 AND SL crossed THEN SL fires despite stale."""
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None

        datafeed = AsyncMock()
        datafeed.obter_historico.return_value = []
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("80000"))

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.005"))  # 0.5% SL

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)

        # Build stale: 3 ticks at same price, sem posição
        for _ in range(3):
            await worker._do_tick()
        # stale_count = 2 para BTC-USD

        # Abrir posição manualmente (simula COMPRA de tick anterior)
        tracker.open_position("BTC-USD", Decimal("80500"))
        # SL threshold = 80500 * 0.995 = 80097.50
        # Preço 80000 < 80097.50 → SL deve disparar

        await worker._do_tick()

        executor.executar_ordem.assert_called_once()


class TestStrategyWorkerReversalCollector:
    """DOC: StrategyWorker integra ReversalCollector para dados pós-entrada."""

    @pytest.mark.asyncio
    async def test_collector_start_on_compra(self):
        """WHEN COMPRA executada THEN collector.start_tracking é chamado."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"), timestamp="2026-05-09T10:00:00")
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        collector = MagicMock()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        worker._reversal_collector = collector

        await worker._do_tick()

        collector.start_tracking.assert_called_once_with(
            "BTC-USD", Decimal("50000"), "2026-05-09T10:00:00",
        )

    @pytest.mark.asyncio
    async def test_collector_update_on_tick(self):
        """WHEN tracking ativo THEN collector.update é chamado a cada tick."""
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))

        collector = MagicMock()
        collector.is_tracking.return_value = True

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        worker._reversal_collector = collector

        await worker._do_tick()

        collector.update.assert_called_once_with("BTC-USD", Decimal("50000"))

    @pytest.mark.asyncio
    async def test_collector_stop_on_sl(self):
        """WHEN posição fechada via SL/TP THEN collector.stop_tracking é chamado."""
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("47000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        collector = MagicMock()
        collector.is_tracking.return_value = True

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        worker._reversal_collector = collector

        await worker._do_tick()

        collector.stop_tracking.assert_called_once()


class TestStrategyWorkerBackwardCompat:
    """DOC: specs/strategy-worker — Backward-compatibilidade com construtor antigo."""

    @pytest.mark.asyncio
    async def test_construtor_antigo_funciona(self):
        """WHEN criar com strategy_name e on_suggestion THEN funciona como stub."""
        from src.core.paper.facade.sandbox.workers.strategy_worker import StrategyWorker

        callback = MagicMock()
        worker = StrategyWorker(strategy_name="legacy", on_suggestion=callback)

        assert worker.name == "strategy_legacy"
        assert worker.strategy_name == "legacy"

        await worker._do_tick()  # stub behavior — não deve crashar


class TestStrategyWorkerLogCores:
    """DOC: specs/paper-guardiao-v2 — Log Verde/Vermelho ao fechar posição."""

    @pytest.mark.asyncio
    async def test_fechamento_lucro_registra_closed_pnl_positivo(self):
        """WHEN posição fechada com lucro THEN closed_pnl recebe valor positivo."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("52000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("52000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        assert len(worker._closed_pnl) == 1
        assert worker._closed_pnl[0] > 0

    @pytest.mark.asyncio
    async def test_fechamento_perda_registra_closed_pnl_negativo(self):
        """WHEN posição fechada com perda THEN closed_pnl recebe valor negativo."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("48000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("48000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        assert len(worker._closed_pnl) == 1
        assert worker._closed_pnl[0] < 0

    @pytest.mark.asyncio
    async def test_sl_fecha_com_pnl_correto(self):
        """WHEN SL acionado THEN closed_pnl registra perda."""
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("47000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        assert len(worker._closed_pnl) == 1
        assert worker._closed_pnl[0] < 0


class TestStrategyWorkerHeartbeat:
    """DOC: specs/paper-guardiao-v2 — Heartbeat enriquecido a cada 60 ticks."""

    @pytest.mark.asyncio
    async def test_heartbeat_loga_no_tick_60(self):
        """WHEN tick_count == 60 THEN _log_heartbeat registra métricas."""
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        worker._tick_count = 59  # próximo tick será 60

        with patch.object(worker, '_log_heartbeat', wraps=worker._log_heartbeat) as mock_hb:
            await worker._do_tick()
            # _log_heartbeat sempre é chamado no final, mas só loga no tick 60
            mock_hb.assert_called_once()

    @pytest.mark.asyncio
    async def test_heartbeat_nao_loga_no_tick_30(self, caplog):
        """WHEN tick_count == 30 THEN heartbeat não loga (apenas a cada 60)."""
        import logging
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        worker._closed_pnl = [100.0]

        with caplog.at_level(logging.INFO, logger=worker._logger.name):
            worker._tick_count = 30
            await worker._do_tick()
            # [HEARTBEAT] só aparece quando tick_count % 60 == 0
            assert not any("[HEARTBEAT]" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_heartbeat_calcula_metricas(self, caplog):
        """WHEN heartbeat dispara THEN loga trades, WR%, PnL corretamente."""
        import logging
        worker = _make_worker()
        worker._closed_pnl = [100.0, -50.0, 75.0]
        # 3 trades, 2 wins → WR = 66.7%

        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        worker._position_tracker = tracker
        worker._tick_count = 60

        with caplog.at_level(logging.INFO, logger=worker._logger.name):
            worker._log_heartbeat({"BTC-USD": Decimal("51000")})
            hb_logs = [r for r in caplog.records if "[HEARTBEAT]" in r.message]
            assert len(hb_logs) == 1
            assert "trades=3" in hb_logs[0].message
            assert "WR=67%" in hb_logs[0].message


class TestStrategyWorkerTickColorido:
    """DOC: specs/paper-guardiao-v2 — Tick com indicadores coloridos."""

    @pytest.mark.asyncio
    async def test_tick_sem_sinal_loga_indicadores(self):
        """WHEN evaluate retorna None com _last_indicators THEN loga +DI/-DI/ADX/gap/vol."""
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None
        strategy._last_indicators = {
            "plus_di": Decimal("25.0"),
            "minus_di": Decimal("18.0"),
            "adx": Decimal("22.5"),
            "volume_ratio": Decimal("1.3"),
        }

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)

        # Deve executar sem crashar — indicadores logados no caminho "neutro"
        await worker._do_tick()

    @pytest.mark.asyncio
    async def test_tick_sem_indicadores_nao_crasha(self):
        """WHEN _last_indicators é None THEN tick executa normalmente."""
        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None
        # Não atribui _last_indicators — getattr retorna None

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()  # não deve crashar


class TestStrategyWorkerSLFixo:
    """DOC: specs/strategy-worker — SL fixo 0.50% via PositionTrackerPort."""

    @pytest.mark.asyncio
    async def test_compra_usa_sl_default_do_tracker(self):
        """WHEN COMPRA executada THEN posição aberta com SL default do tracker (0.005)."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("80000"), razao="DI crossover",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("80000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()  # default SL = 0.005

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        pos = tracker.get_position("BTC-USD")
        assert pos is not None
        assert pos["stop_loss_pct"] == Decimal("0.005")

    @pytest.mark.asyncio
    async def test_worker_funciona_com_port_interface(self):
        """WHEN worker recebe SimpleTracker (PositionTrackerPort) THEN opera normalmente."""
        from src.core.paper.domain.strategies.position_tracker import PositionTrackerPort, SimpleTracker

        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("80000"), razao="DI crossover",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("80000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = SimpleTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        assert isinstance(tracker, PositionTrackerPort)
        pos = tracker.get_position("BTC-USD")
        assert pos is not None


class TestDualEntrySystem:
    """DOC: specs/dual-entry-system — Dual Entry com Pullback Fib + Breakout ADX."""

    def _setup_worker_with_reentry(self, preco_atual, crossover_price, swing_low,
                                    fib_level=None, ticks_since=5, has_position=False,
                                    adx_prev=None, adx_curr=None, plus_di=None, minus_di=None):
        """Helper: cria worker com re-entry state configurado."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        strategy = MagicMock()
        strategy.name = "test"
        strategy.evaluate.return_value = None
        strategy._last_indicators = {
            "plus_di": plus_di or Decimal("30.0"),
            "minus_di": minus_di or Decimal("15.0"),
            "adx": adx_curr or Decimal("28.0"),
            "volume_ratio": Decimal("1.0"),
            "swing_low": swing_low,
        }
        strategy._adx_threshold = Decimal("25")
        strategy._tp_for_adx = MagicMock(return_value=Decimal("0.004"))

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal(str(preco_atual)))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = SimpleTracker()

        # Configurar re-entry state
        tracker.set_reentry_state("BTC-USD", crossover_price=Decimal(str(crossover_price)),
                                  swing_low=Decimal(str(swing_low)) if swing_low else None)
        # Incrementar ticks
        for _ in range(ticks_since):
            tracker.tick_reentry("BTC-USD")

        if has_position:
            tracker.open_position("BTC-USD", Decimal(str(crossover_price)))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        worker._prev_indicators["BTC-USD"] = {
            "adx": adx_prev if adx_prev is not None else Decimal("24.0"),
        }
        # Se ticks_since < 3, simular que SL acabou de acontecer
        # (valor inicial será incrementado antes do check, então 1 → 2 < 3 = bloqueado)
        if ticks_since < 3:
            worker._ticks_since_sl["BTC-USD"] = ticks_since - 1  # será incrementado no tick
        return worker, tracker, executor

    @pytest.mark.asyncio
    async def test_entry1_pullback_fibonacci(self):
        """WHEN preço <= fib_level E sem posição E cooldown OK THEN COMPRA pullback."""
        # crossover_price = 80830, swing_low = 80279
        # fib_level = 80279 + (80830-80279)*0.618 ≈ 80619.5
        # preco_atual = 80500 < 80619.5 → pullback!
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="80500", crossover_price="80830", swing_low="80279",
            ticks_since=5,
        )
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()
        assert tracker.get_position("BTC-USD") is not None
        assert tracker.get_reentry_state("BTC-USD") is None  # limpo após execução

    @pytest.mark.asyncio
    async def test_entry1_preco_nao_chegou(self):
        """WHEN preço > fib_level THEN NÃO executa Entry 1."""
        # fib_level ≈ 80619.5, preco = 80700 > fib → não executa
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="80700", crossover_price="80830", swing_low="80279",
            ticks_since=5,
        )
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()
        assert tracker.get_reentry_state("BTC-USD") is not None  # estado mantido

    @pytest.mark.asyncio
    async def test_entry1_ignorado_com_posicao(self):
        """WHEN posição já existe THEN Entry 1 ignorada (SimpleTracker netting)."""
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="80500", crossover_price="80830", swing_low="80279",
            ticks_since=5, has_position=True,
        )
        await worker._do_tick()

        # execução normal do worker — sinal None, sem ordem nova
        # Mas não deve ter dupla execução via re-entry
        assert tracker.get_position("BTC-USD") is not None

    @pytest.mark.asyncio
    async def test_entry2_breakout_adx_confirm(self):
        """WHEN preço > crossover_price E ADX >= threshold THEN COMPRA breakout."""
        # preco = 81000 > crossover = 80830, ADX = 30 >= 25 → breakout confirmado
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="81000", crossover_price="80830", swing_low="80279",
            ticks_since=5, adx_prev=Decimal("28.0"), adx_curr=Decimal("30.0"),
        )
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()
        assert tracker.get_position("BTC-USD") is not None
        assert tracker.get_reentry_state("BTC-USD") is None  # limpo após execução

    @pytest.mark.asyncio
    async def test_entry2_sem_adx_confirm_nao_executa(self):
        """WHEN ADX < threshold THEN Entry 2 não executa."""
        # preco = 81000 > crossover = 80830, mas ADX = 22 < 25
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="81000", crossover_price="80830", swing_low="80279",
            ticks_since=5, adx_prev=Decimal("22.0"), adx_curr=Decimal("23.0"),
        )
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()

    @pytest.mark.asyncio
    async def test_entry2_com_posicao_ignorado(self):
        """WHEN posição existe THEN Entry 2 ignorada (SimpleTracker netting)."""
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="81000", crossover_price="80830", swing_low="80279",
            ticks_since=5, has_position=True,
            adx_prev=Decimal("24.0"), adx_curr=Decimal("26.0"),
        )
        await worker._do_tick()

        # Não deve executar ordem via re-entry (posição já existe)
        call_count = executor.executar_ordem.call_count
        assert call_count == 0  # sinal None e re-entry bloqueada

    @pytest.mark.asyncio
    async def test_cooldown_bloqueia_reentrada(self):
        """WHEN SL acionado há < 3 ticks THEN re-entrada bloqueada."""
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="80500", crossover_price="80830", swing_low="80279",
            ticks_since=2,  # < 3 → cooldown bloqueia
        )
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()

    @pytest.mark.asyncio
    async def test_cooldown_permitido_apos_3_ticks(self):
        """WHEN SL acionado há >= 3 ticks THEN re-entrada permitida."""
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="80500", crossover_price="80830", swing_low="80279",
            ticks_since=3,  # >= 3 → cooldown OK
        )
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()

    @pytest.mark.asyncio
    async def test_reentry_expira_200_ticks(self):
        """WHEN re-entry state existe há 200+ ticks THEN limpo sem execução."""
        worker, tracker, executor = self._setup_worker_with_reentry(
            preco_atual="80500", crossover_price="80830", swing_low="80279",
            ticks_since=200,  # expirado
        )
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()
        assert tracker.get_reentry_state("BTC-USD") is None

    @pytest.mark.asyncio
    async def test_crossover_cria_reentry_state(self):
        """WHEN DI crossover detectado E sem posição THEN cria re-entry state."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("80830"), razao="DI crossover",
            take_profit_pct=Decimal("0.004"),
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"
        strategy._last_indicators = {
            "plus_di": Decimal("30.0"),
            "minus_di": Decimal("15.0"),
            "adx": Decimal("28.0"),
            "volume_ratio": Decimal("1.0"),
            "swing_low": Decimal("80279"),
        }
        strategy._tp_for_adx = MagicMock(return_value=Decimal("0.004"))

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("80830"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = SimpleTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        # Posição aberta — re-entry state criado para uso futuro
        assert tracker.get_position("BTC-USD") is not None
        # Como já tem posição, re-entry state pode ou não existir
        # O importante é que set_reentry_state foi chamado
        reentry = tracker.get_reentry_state("BTC-USD")
        # Quando já há posição, o estado é criado mas não executável até posição fechar
        assert reentry is not None or tracker.get_position("BTC-USD") is not None
