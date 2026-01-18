# -*- coding: utf-8 -*-
"""
Tests para fuzzy search em query registry.

Issue #42: Implementar busca fuzzy em queries
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from kernel.registry.query_registry import QueryRegistry, QueryHandler
from kernel.registry.skyrpc_registry import SkyRpcRegistry


class MockHandler:
    """Mock handler para testes."""
    def __init__(self, name: str):
        self.name = name
        self.call_count = 0

    def __call__(self, *args, **kwargs):
        self.call_count += 1
        return f"Called {self.name}"


class FuzzySearchTests(unittest.TestCase):
    """Testes para busca fuzzy em query handlers."""

    def setUp(self):
        """Configura registry de teste."""
        self.registry = QueryRegistry()

        # Registra handlers de teste
        handlers = [
            ("fileops.read", MockHandler("fileops.read"), "Read file operations"),
            ("fileops.write", MockHandler("fileops.write"), "Write file operations"),
            ("fileops.delete", MockHandler("fileops.delete"), "Delete file operations"),
            ("webhooks.receive", MockHandler("webhooks.receive"), "Receive webhooks"),
            ("webhooks.process", MockHandler("webhooks.process"), "Process webhooks"),
            ("webhookprocessor.parse", MockHandler("webhookprocessor.parse"), "Parse webhook"),
            ("joborchestrator.run", MockHandler("joborchestrator.run"), "Run jobs"),
            ("health", MockHandler("health"), "Health check"),
        ]

        for name, handler, description in handlers:
            self.registry.register(
                name=name,
                handler=handler,
                description=description,
                kind="query"
            )

    def tearDown(self):
        """Limpa registry após testes."""
        self.registry.clear()

    def test_fuzzy_search_typo_correction(self):
        """
        Critério de aceite: Busca "fileop" encontra "fileops".
        """
        results = self.registry.fuzzy_search("fileop", limit=3, min_score=60)

        # Deve encontrar fileops.* handlers
        self.assertGreater(len(results), 0, "Deve retornar resultados para 'fileop'")

        # Primeiro resultado deve ser um fileops.*
        method_names = [name for name, _, _ in results]
        self.assertTrue(
            any("fileops" in name for name in method_names),
            f"Deve conter 'fileops' em: {method_names}"
        )

        # Scores devem ser razoavelmente altos
        for name, handler, score in results:
            self.assertGreater(score, 60, f"Score deve ser > 60 para {name}")

    def test_fuzzy_search_webhook_typo(self):
        """
        Critério de aceite: Busca "webook" encontra "webhook".
        """
        results = self.registry.fuzzy_search("webook", limit=5, min_score=60)

        # Deve encontrar webhooks.* ou webhookprocessor.*
        self.assertGreater(len(results), 0, "Deve retornar resultados para 'webook'")

        method_names = [name for name, _, _ in results]
        self.assertTrue(
            any("webhook" in name for name in method_names),
            f"Deve conter 'webhook' em: {method_names}"
        )

    def test_fuzzy_search_score_visibility(self):
        """
        Critério de aceite: Score de relevância visível.
        """
        results = self.registry.fuzzy_search("file", limit=5, min_score=50)

        # Cada resultado deve ter um score
        for name, handler, score in results:
            self.assertIsInstance(score, int, "Score deve ser inteiro")
            self.assertGreaterEqual(score, 0, "Score deve ser >= 0")
            self.assertLessEqual(score, 100, "Score deve ser <= 100")

    def test_fuzzy_search_returns_handler(self):
        """Busca fuzzy deve retornar handler completo."""
        results = self.registry.fuzzy_search("health", limit=1, min_score=80)

        self.assertEqual(len(results), 1)
        name, handler, score = results[0]

        self.assertEqual(name, "health")
        self.assertIsInstance(handler, QueryHandler)
        self.assertEqual(handler.name, "health")
        self.assertEqual(handler.kind, "query")

    def test_fuzzy_search_limit(self):
        """Respeita limite de resultados."""
        results = self.registry.fuzzy_search("webhook", limit=2, min_score=50)

        self.assertLessEqual(len(results), 2)

    def test_fuzzy_search_min_score_filter(self):
        """Filtra resultados por score mínimo."""
        results_high = self.registry.fuzzy_search("xyz", limit=10, min_score=80)
        results_low = self.registry.fuzzy_search("xyz", limit=10, min_score=40)

        # Com score alto, deve retornar menos ou iguais
        self.assertLessEqual(len(results_high), len(results_low))

    def test_fuzzy_search_no_match(self):
        """Retorna lista vazia quando não há matches."""
        results = self.registry.fuzzy_search("nonexistent_query_xyz", limit=5, min_score=80)

        self.assertEqual(len(results), 0)

    def test_fuzzy_search_ordering(self):
        """Resultados devem ser ordenados por score (decrescente)."""
        results = self.registry.fuzzy_search("webhook", limit=5, min_score=50)

        if len(results) > 1:
            scores = [score for _, _, score in results]
            # Scores devem estar em ordem decrescente
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_fuzzy_search_case_insensitive(self):
        """Busca deve ser case-insensitive."""
        results_lower = self.registry.fuzzy_search("FILE", limit=5, min_score=50)
        results_upper = self.registry.fuzzy_search("file", limit=5, min_score=50)

        # Deve retornar mesma quantidade de resultados
        self.assertEqual(len(results_lower), len(results_upper))


class SkyRpcRegistryFuzzySearchTests(unittest.TestCase):
    """Testes para fuzzy search no SkyRpcRegistry."""

    def setUp(self):
        """Configura SkyRpcRegistry de teste."""
        self.registry = SkyRpcRegistry()
        self.registry._base.clear()  # Limpa singleton

        # Registra handlers
        handlers = [
            ("fileops.read", lambda x: x, "Read file"),
            ("fileops.write", lambda x: x, "Write file"),
            ("webhooks.receive", lambda x: x, "Receive webhooks"),
            ("health", lambda: "ok", "Health check"),
        ]

        for name, handler, desc in handlers:
            self.registry.register(
                name=name,
                handler=handler,
                description=desc,
                kind="query"
            )

    def tearDown(self):
        """Limpa registry."""
        self.registry._base.clear()

    def test_skyrpc_fuzzy_search_returns_enriched_metadata(self):
        """SkyRpcRegistry deve retornar metadados enriquecidos."""
        results = self.registry.fuzzy_search("fileop", limit=5, min_score=60)

        for result in results:
            # Deve ter campos esperados
            self.assertIn("method", result)
            self.assertIn("score", result)
            self.assertIn("kind", result)
            self.assertIn("description", result)
            self.assertIn("module", result)
            self.assertIn("auth_required", result)

            # Tipos corretos
            self.assertIsInstance(result["method"], str)
            self.assertIsInstance(result["score"], int)
            self.assertIsInstance(result["kind"], str)
            self.assertIsInstance(result["auth_required"], bool)

    def test_skyrpc_fuzzy_search_typo_correction(self):
        """SkyRpcRegistry: busca "fileop" encontra "fileops"."""
        results = self.registry.fuzzy_search("fileop", limit=5, min_score=60)

        self.assertGreater(len(results), 0)
        method_names = [r["method"] for r in results]
        self.assertTrue(any("fileops" in name for name in method_names))

    def test_skyrpc_fuzzy_search_score_visible(self):
        """SkyRpcRegistry: score deve estar visível nos resultados."""
        results = self.registry.fuzzy_search("webhook", limit=5, min_score=50)

        for result in results:
            self.assertIn("score", result)
            self.assertGreaterEqual(result["score"], 0)
            self.assertLessEqual(result["score"], 100)


if __name__ == "__main__":
    unittest.main()
