# -*- coding: utf-8 -*-
"""Testes para ReversalCollector — coleta dados pós-entrada (SKY-136)."""

import os
from decimal import Decimal
from pathlib import Path

import pytest

from src.core.paper.facade.sandbox.workers.reversal_collector import ReversalCollector


@pytest.fixture
def csv_tmp(tmp_path):
    """Fixture: caminho CSV temporário."""
    return str(tmp_path / "estudo-reversao.csv")


class TestReversalCollectorStartStop:
    """DOC: specs/paper-guardiao-v2 — Ciclo de vida do tracking."""

    def test_start_tracking_cria_registro(self, csv_tmp):
        """WHEN start_tracking é chamado THEN tracker registra entrada."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")

        assert collector.is_tracking("BTC-USD")
        assert not collector.is_tracking("ETH-USD")

    def test_stop_tracking_retorna_registro(self, csv_tmp):
        """WHEN stop_tracking é chamado THEN retorna dados e para de rastrear."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")
        collector.update("BTC-USD", Decimal("80200"))

        record = collector.stop_tracking("BTC-USD", Decimal("80100"))

        assert record is not None
        assert record["ticker"] == "BTC-USD"
        assert record["preco_entrada"] == 80000.0
        assert record["pico"] == 80200.0
        assert record["preco_saida"] == 80100.0
        assert not collector.is_tracking("BTC-USD")

    def test_stop_tracking_sem_posicao_retorna_none(self, csv_tmp):
        """WHEN stop_tracking sem tracking ativo THEN retorna None."""
        collector = ReversalCollector(csv_path=csv_tmp)
        assert collector.stop_tracking("BTC-USD", Decimal("80000")) is None


class TestReversalCollectorUpdate:
    """DOC: specs/paper-guardiao-v2 — Atualização de preços pós-entrada."""

    def test_update_registra_pico(self, csv_tmp):
        """WHEN preço sobe acima da entrada THEN pico é atualizado."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")

        collector.update("BTC-USD", Decimal("80100"))
        collector.update("BTC-USD", Decimal("80300"))
        collector.update("BTC-USD", Decimal("80200"))

        record = collector.stop_tracking("BTC-USD", Decimal("80200"))
        assert record["pico"] == Decimal("80300")

    def test_update_registra_tempo_ate_pico(self, csv_tmp):
        """WHEN pico ocorre no tick 3 THEN tempo_ate_pico_ticks == 3."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")

        collector.update("BTC-USD", Decimal("80100"))  # tick 1
        collector.update("BTC-USD", Decimal("80300"))  # tick 2 — pico
        collector.update("BTC-USD", Decimal("80200"))  # tick 3

        record = collector.stop_tracking("BTC-USD", Decimal("80200"))
        assert record["tempo_ate_pico_ticks"] == 2

    def test_update_registra_drawdown_max(self, csv_tmp):
        """WHEN preço cai do pico THEN drawdown_max é registrado."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")

        collector.update("BTC-USD", Decimal("80300"))  # pico
        collector.update("BTC-USD", Decimal("80100"))  # drawdown
        collector.update("BTC-USD", Decimal("80200"))  # recupera parcial

        record = collector.stop_tracking("BTC-USD", Decimal("80200"))
        # drawdown = (80300 - 80100) / 80300 = 200/80300 ≈ 0.00249
        assert record["drawdown_max_pct"] > 0


class TestReversalCollectorCSV:
    """DOC: specs/paper-guardiao-v2 — Persistência em CSV."""

    def test_salva_registro_no_csv(self, csv_tmp):
        """WHEN stop_tracking THEN registro é salvo no CSV."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")
        collector.update("BTC-USD", Decimal("80300"))
        collector.stop_tracking("BTC-USD", Decimal("80100"))

        assert os.path.isfile(csv_tmp)
        with open(csv_tmp, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 2  # header + 1 data row
        assert "BTC-USD" in lines[1]

    def test_csv_header_correto(self, csv_tmp):
        """WHEN primeiro registro é salvo THEN header contém colunas esperadas."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")
        collector.stop_tracking("BTC-USD", Decimal("80000"))

        with open(csv_tmp, encoding="utf-8") as f:
            header = f.readline().strip()

        expected = "ticker,preco_entrada,preco_saida,pico,variacao_max_pct,reversao_pct,drawdown_max_pct,tempo_ate_pico_ticks,duracao_ticks"
        assert header == expected

    def test_multiplos_registros_append(self, csv_tmp):
        """WHEN múltiplos registros THEN todos são salvos (append)."""
        collector = ReversalCollector(csv_path=csv_tmp)

        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")
        collector.update("BTC-USD", Decimal("80200"))
        collector.stop_tracking("BTC-USD", Decimal("80100"))

        collector.start_tracking("ETH-USD", Decimal("3000"), "2026-05-09T11:00:00")
        collector.update("ETH-USD", Decimal("3050"))
        collector.stop_tracking("ETH-USD", Decimal("3020"))

        with open(csv_tmp, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 3  # header + 2 data rows


class TestReversalCollectorReversao:
    """DOC: specs/paper-guardiao-v2 — Cálculo de reversão."""

    def test_reversao_pct_calculada(self, csv_tmp):
        """WHEN pico=80300 e saída=80100 THEN reversao_pct = (80300-80100)/80300."""
        collector = ReversalCollector(csv_path=csv_tmp)
        collector.start_tracking("BTC-USD", Decimal("80000"), "2026-05-09T10:00:00")
        collector.update("BTC-USD", Decimal("80300"))

        record = collector.stop_tracking("BTC-USD", Decimal("80100"))

        expected_reversao = (80300 - 80100) / 80300 * 100
        assert abs(record["reversao_pct"] - expected_reversao) < 0.01
