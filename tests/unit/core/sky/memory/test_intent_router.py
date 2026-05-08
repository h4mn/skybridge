# coding: utf-8
"""
Testes unitários para IntentRouter.
"""

import pytest

from src.core.sky.memory.cognitive_layer import IntentRouter


class TestIntentRouter:
    """Testes para IntentRouter."""

    def setup_method(self):
        """Configura teste."""
        self.router = IntentRouter()

    def test_route_identity_query(self):
        """Testa roteamento para queries de identidade."""
        queries = [
            "Quem é você?",
            "O que você sabe fazer?",
            "Descreva-se",
        ]

        for query in queries:
            result = self.router.route_query(query)
            assert "identity" in result

    def test_route_teachings_query(self):
        """Testa roteamento para queries de ensinamentos."""
        queries = [
            "O que papai me ensinou?",
            "Papai disse algo importante"
            "Qual ensinamento?",
        ]

        for query in queries:
            result = self.router.route_query(query)
            assert "teachings" in result

    def test_route_shared_moments_query(self):
        """Testa roteamento para queries de memórias compartilhadas."""
        queries = [
            "Lembra da vez que resolvemos o bug?",
            "Nosso momento especial",
            "Compartilhamos algo",
        ]

        for query in queries:
            result = self.router.route_query(query)
            assert "shared-moments" in result

    def test_route_operational_query(self):
        """Testa roteamento para queries operacionais."""
        queries = [
            "O que aconteceu hoje?",
            "Status atual",
            "O que está acontecendo?",
        ]

        for query in queries:
            result = self.router.route_query(query)
            assert "operational" in result

    def test_route_ambiguous_to_all(self):
        """Testa que queries ambíguas roteiam para todas as coleções."""
        query = "Como está o sistema?"
        result = self.router.route_query(query)

        # Deve retornar todas as coleções
        assert len(result) == 4
        assert "identity" in result
        assert "shared-moments" in result
        assert "teachings" in result
        assert "operational" in result

    def test_detect_intent(self):
        """Testa detecção de intenção principal."""
        assert self.router.detect_intent("Quem é você?") == "identity"
        assert self.router.detect_intent("O que papai ensinou?") == "teachings"
        assert self.router.detect_intent("Lembra de nós?") == "shared-moments"
        assert self.router.detect_intent("O que rolou hoje?") == "operational"
