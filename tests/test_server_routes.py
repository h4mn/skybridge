# -*- coding: utf-8 -*-
"""
Testes de Rotas do Servidor Unificado (apps.server).

Testa o redirecionamento da raiz para WebUI e outras rotas específicas
do servidor unificado implementado em PRD022.
"""

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps"))


class ServerRoutesTests(unittest.TestCase):
    """Testes de rotas do servidor unificado apps/server."""

    @classmethod
    def setUpClass(cls):
        """Configura TestClient com o servidor unificado."""
        from server.main import SkybridgeServer
        cls.server = SkybridgeServer()
        cls.client = TestClient(cls.server.app)

    def test_root_redirects_to_web(self):
        """
        Testa que a rota raiz (/) redireciona para /web/.

        Conforme PRD022, o servidor unificado deve redirecionar
        automaticamente a raiz para a WebUI.
        """
        response = self.client.get("/", follow_redirects=False)

        # Verifica status de redirecionamento
        self.assertIn(response.status_code, [307, 308],  # Temporary/Permanent Redirect
                      f"Expected redirect status, got {response.status_code}")

        # Verifica cabeçalho de localização
        self.assertEqual(response.headers.get("location"), "/web/",
                         "Expected redirect to /web/")

    def test_root_redirect_follow(self):
        """
        Testa o redirecionamento completo de / para /web/.

        Usa follow_redirects para verificar o fluxo completo.
        """
        response = self.client.get("/", follow_redirects=True)

        # Após redirecionamento, deve ser 404 (web/dist não existe)
        # ou 200 se existir
        self.assertIn(response.status_code, [200, 404],
                      f"Expected 200 or 404 after redirect, got {response.status_code}")

    def test_web_redirect_to_web_trailing_slash(self):
        """
        Testa que /web redireciona para /web/.

        Garante consistência de URL com barra no final.
        """
        response = self.client.get("/web", follow_redirects=False)

        # Verifica status de redirecionamento
        self.assertIn(response.status_code, [307, 308],
                      f"Expected redirect status, got {response.status_code}")

        # Verifica cabeçalho de localização
        self.assertEqual(response.headers.get("location"), "/web/",
                         "Expected redirect to /web/")

    def test_api_still_accessible(self):
        """
        Testa que rotas da API ainda funcionam corretamente.

        Garante que o redirecionamento da raiz não quebra rotas da API.
        """
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())


if __name__ == "__main__":
    unittest.main()
