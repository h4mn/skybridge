"""
Testes para Skylab Core - Context Manager

Testes TDD estritos: RED → GREEN → REFACTOR

Spec: tdd-core/spec.md
- Requirement: Gerenciar contexto e drift
- Scenario: Re-injeta prompt periodicamente
- Scenario: Compacta contexto quando necessário
- Scenario: Checkpoint a cada 25 iterações
"""

import pytest
from src.core.autokarpa.programs.skylab.core.context_manager import (
    ContextManager,
    DriftDetection,
)


class TestContextManagerInit:
    """Testa inicialização do ContextManager."""

    def test_inicializa_com_prompt_original(self):
        """
        DOC: spec.md - ContextManager deve guardar prompt original.

        Dado: prompt original fornecido
        Quando: ContextManager é criado
        Então: prompt_original é armazenado
        """
        prompt = "Implemente uma função de soma"
        cm = ContextManager(original_prompt=prompt)

        assert cm.original_prompt == prompt
        assert cm.iterations == []
        assert cm.best_score == 0.0

    def test_inicializa_com_max_tokens(self):
        """
        DOC: spec.md - ContextManager deve ter max_tokens configurável.

        Dado: max_tokens fornecido
        Quando: ContextManager é criado
        Então: max_tokens é configurado
        """
        cm = ContextManager(original_prompt="prompt", max_tokens=64000)

        assert cm.max_tokens == 64000


class TestShouldReinjectPrompt:
    """Testa should_reinject_prompt()."""

    def test_reinjeta_a_cada_10_iteracoes(self):
        """
        DOC: spec.md - Deve re-injetar a cada 10 iterações.

        Dado: ContextManager configurado
        Quando: iteração é múltiplo de 10
        Então: retorna True
        """
        cm = ContextManager(original_prompt="prompt")

        assert cm.should_reinject_prompt(10) is True
        assert cm.should_reinject_prompt(20) is True
        assert cm.should_reinject_prompt(30) is True

    def test_nao_reinjeta_em_outras_iteracoes(self):
        """
        DOC: spec.md - Não deve re-injetar em iterações não-múltiplas.

        Dado: ContextManager configurado
        Quando: iteração NÃO é múltiplo de 10
        Então: retorna False
        """
        cm = ContextManager(original_prompt="prompt")

        assert cm.should_reinject_prompt(5) is False
        assert cm.should_reinject_prompt(11) is False
        assert cm.should_reinject_prompt(25) is False


class TestShouldCompact:
    """Testa should_compact()."""

    def test_compacta_acima_de_80_percent(self):
        """
        DOC: spec.md - Deve compactar quando tokens > 80% da janela.

        Dado: max_tokens = 100000
        Quando: current_tokens = 85000
        Então: retorna True (85% > 80%)
        """
        cm = ContextManager(original_prompt="prompt", max_tokens=100000)

        assert cm.should_compact(85000) is True

    def test_nao_compacta_abaixo_de_80_percent(self):
        """
        DOC: spec.md - Não deve compactar quando tokens <= 80% da janela.

        Dado: max_tokens = 100000
        Quando: current_tokens = 75000
        Então: retorna False (75% < 80%)
        """
        cm = ContextManager(original_prompt="prompt", max_tokens=100000)

        assert cm.should_compact(75000) is False


class TestCompact:
    """Testa compact()."""

    def test_mantem_ultimas_20_iteracoes(self):
        """
        DOC: spec.md - compact() deve manter últimas 20 iterações.

        Dado: 30 iterações registradas
        Quando: compact() é chamado
        Então: últimas 20 iterações são mantidas
        """
        cm = ContextManager(original_prompt="prompt")

        # Adicionar 30 iterações
        for i in range(30):
            cm.add_iteration(i, f"code_{i}", 0.5 + (i * 0.01), f"iter_{i}")

        kept = cm.compact()

        assert len(kept) == 20
        assert len(cm.iterations) == 20
        assert cm.iterations[0]["iteration"] == 10  # Primeira mantida é a 10
        assert cm.iterations[-1]["iteration"] == 29  # Última é a 29


class TestShouldCheckpoint:
    """Testa should_checkpoint()."""

    def test_checkpoint_a_cada_25_iteracoes(self):
        """
        DOC: spec.md - Deve checkpoint a cada 25 iterações.

        Dado: ContextManager configurado
        Quando: iteração é múltiplo de 25
        Então: retorna True
        """
        cm = ContextManager(original_prompt="prompt")

        assert cm.should_checkpoint(25) is True
        assert cm.should_checkpoint(50) is True
        assert cm.should_checkpoint(75) is True

    def test_nao_checkpoint_em_outras_iteracoes(self):
        """
        DOC: spec.md - Não deve checkpoint em iterações não-múltiplas.

        Dado: ContextManager configurado
        Quando: iteração NÃO é múltiplo de 25
        Então: retorna False
        """
        cm = ContextManager(original_prompt="prompt")

        assert cm.should_checkpoint(10) is False
        assert cm.should_checkpoint(30) is False


class TestAddIteration:
    """Testa add_iteration()."""

    def test_adiciona_iteracao_ao_historico(self):
        """
        DOC: spec.md - add_iteration() deve registrar iteração.

        Dado: dados de iteração fornecidos
        Quando: add_iteration() é chamado
        Então: iteração é adicionada ao histórico
        """
        cm = ContextManager(original_prompt="prompt")

        cm.add_iteration(0, "code", 0.75, "primeira iteração")

        assert len(cm.iterations) == 1
        assert cm.iterations[0]["iteration"] == 0
        assert cm.iterations[0]["code"] == "code"
        assert cm.iterations[0]["code_health"] == 0.75

    def test_atualiza_melhor_codigo(self):
        """
        DOC: spec.md - Melhor código deve ser atualizado se score maior.

        Dado: iteração com score maior que best_score
        Quando: add_iteration() é chamado
        Então: best_code e best_score são atualizados
        """
        cm = ContextManager(original_prompt="prompt")

        cm.add_iteration(0, "code_v1", 0.50, "v1")
        assert cm.best_score == 0.50
        assert cm.best_code == "code_v1"

        cm.add_iteration(1, "code_v2", 0.75, "v2")
        assert cm.best_score == 0.75
        assert cm.best_code == "code_v2"


class TestDetectStagnation:
    """Testa detect_stagnation()."""

    def test_detecta_stagnation_quando_variencia_baixa(self):
        """
        DOC: spec.md - Deve detectar stagnation quando variância < 0.01.

        Dado: 10 iterações com scores muito similares (0.50, 0.51, 0.50, ...)
        Quando: detect_stagnation() é chamado
        Então: retorna DriftDetection com type="stagnation"
        """
        cm = ContextManager(original_prompt="prompt")

        # Adicionar 10 iterações com scores similares
        for i in range(10):
            score = 0.50 + (0.001 if i % 2 == 0 else 0.0)
            cm.add_iteration(i, f"code_{i}", score, f"iter_{i}")

        drift = cm.detect_stagnation()

        assert drift is not None
        assert drift.drift_type == "stagnation"
        assert drift.action == "compact_context"

    def test_nao_detecta_stagnation_com_variencia_alta(self):
        """
        DOC: spec.md - Não deve detectar stagnation quando variância >= 0.01.

        Dado: 10 iterações com scores variados (0.30, 0.80, 0.40, ...)
        Quando: detect_stagnation() é chamado
        Então: retorna None
        """
        cm = ContextManager(original_prompt="prompt")

        # Adicionar 10 iterações com scores variados
        scores = [0.30, 0.80, 0.40, 0.90, 0.35, 0.85, 0.45, 0.75, 0.50, 0.70]
        for i, score in enumerate(scores):
            cm.add_iteration(i, f"code_{i}", score, f"iter_{i}")

        drift = cm.detect_stagnation()

        assert drift is None


class TestDetectDecline:
    """Testa detect_decline()."""

    def test_detecta_decline_segunda_metade_pior(self):
        """
        DOC: spec.md - Deve detectar decline quando 2ª metade 10% pior.

        Dado: 20 iterações, segunda metade com média 10% menor
        Quando: detect_decline() é chamado
        Então: retorna DriftDetection com type="decline"
        """
        cm = ContextManager(original_prompt="prompt")

        # Primeiras 10 iterações: score ~0.80
        for i in range(10):
            cm.add_iteration(i, f"code_{i}", 0.80, f"iter_{i}")

        # Próximas 10 iterações: score ~0.70 (12.5% pior que 0.80)
        for i in range(10, 20):
            cm.add_iteration(i, f"code_{i}", 0.70, f"iter_{i}")

        drift = cm.detect_decline()

        assert drift is not None
        assert drift.drift_type == "decline"
        assert drift.action == "reinject_prompt"

    def test_nao_detecta_decline_sem_diferenca_significativa(self):
        """
        DOC: spec.md - Não deve detectar decline sem diferença significativa.

        Dado: 20 iterações com scores similares
        Quando: detect_decline() é chamado
        Então: retorna None
        """
        cm = ContextManager(original_prompt="prompt")

        # 20 iterações com scores similares
        for i in range(20):
            score = 0.70 + (0.01 if i % 2 == 0 else 0.0)
            cm.add_iteration(i, f"code_{i}", score, f"iter_{i}")

        drift = cm.detect_decline()

        assert drift is None


class TestDetectRepetition:
    """Testa detect_repetition()."""

    def test_detecta_repetition_descricoes_iguais(self):
        """
        DOC: spec.md - Deve detectar repetition quando descrições idênticas.

        Dado: 3 iterações com mesma descrição
        Quando: detect_repetition() é chamado
        Então: retorna DriftDetection com type="repetition"
        """
        cm = ContextManager(original_prompt="prompt")

        for i in range(3):
            cm.add_iteration(i, f"code_{i}", 0.50 + (i * 0.01), "adicionou helper")

        drift = cm.detect_repetition()

        assert drift is not None
        assert drift.drift_type == "repetition"
        assert drift.action == "increase_temperature"

    def test_nao_detecta_repetition_descricoes_diferentes(self):
        """
        DOC: spec.md - Não deve detectar repetition com descrições diferentes.

        Dado: 3 iterações com descrições diferentes
        Quando: detect_repetition() é chamado
        Então: retorna None
        """
        cm = ContextManager(original_prompt="prompt")

        descriptions = ["adicionou foo", "implementou bar", "refatorou baz"]
        for i, desc in enumerate(descriptions):
            cm.add_iteration(i, f"code_{i}", 0.50, desc)

        drift = cm.detect_repetition()

        assert drift is None


class TestReinjectPrompt:
    """Testa reinject_prompt()."""

    def test_retorna_prompt_com_contexto_essencial(self):
        """
        DOC: spec.md - reinject_prompt() deve retornar prompt com contexto essencial.

        Dado: ContextManager com iterações
        Quando: reinject_prompt() é chamado
        Então: retorna prompt com: original, melhor código, últimas iterações
        """
        cm = ContextManager(original_prompt="Implemente soma")

        cm.add_iteration(0, "def soma(): return 0", 0.5, "baseline")
        cm.add_iteration(1, "def soma(a,b): return a+b", 0.9, "implementou")

        prompt = cm.reinject_prompt()

        assert "Implemente soma" in prompt
        assert "def soma(a,b): return a+b" in prompt  # Melhor código
        assert "Iteration 1" in prompt  # Última iteração


class TestGetContextSummary:
    """Testa get_context_summary()."""

    def test_retorna_resumo_do_contexto(self):
        """
        DOC: spec.md - get_context_summary() deve retornar estatísticas.

        Dado: ContextManager com iterações
        Quando: get_context_summary() é chamado
        Então: retorna dict com estatísticas completas
        """
        cm = ContextManager(original_prompt="prompt", max_tokens=100000)

        cm.add_iteration(0, "code", 0.75, "iteração")
        cm.current_tokens = 50000

        summary = cm.get_context_summary()

        assert summary["total_iterations"] == 1
        assert summary["best_score"] == 0.75
        assert summary["current_tokens"] == 50000
        assert summary["max_tokens"] == 100000
        assert summary["token_usage"] == 0.5
        assert summary["needs_compaction"] is False


__all__ = []
