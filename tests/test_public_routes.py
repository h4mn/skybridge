import sys
import unittest
import yaml
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skybridge.platform.bootstrap.app import get_app


class PublicRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(get_app().app)
    def test_openapi_public(self):
        response = self.client.get("/openapi")
        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi: 3.1.0", response.text)
        self.assertIn("/ticket:", response.text)
        self.assertIn("/envelope:", response.text)

    def test_privacy_public(self):
        response = self.client.get("/privacy")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Política de Privacidade", response.text)

    def test_public_routes_documented_in_openapi(self):
        """
        Teste preventivo: garante que rotas públicas (/openapi e /privacy)
        estão documentadas no arquivo OpenAPI para uso por GPTs personalizados.

        Este teste previne regressões onde as rotas existem no código mas não
        estão documentadas no contrato OpenAPI, fazendo com que clientes GPT
        Custom não consigam descobri-las.
        """
        # Encontra o root do repositório
        repo_root = None
        for parent in Path(__file__).resolve().parents:
            if (parent / "docs").is_dir() and (parent / "src").is_dir():
                repo_root = parent
                break
        self.assertIsNotNone(repo_root, "Could not find repository root")

        # Carrega o arquivo OpenAPI
        openapi_path = repo_root / "docs" / "spec" / "openapi" / "openapi.yaml"
        self.assertTrue(openapi_path.exists(), f"OpenAPI file not found: {openapi_path}")

        with open(openapi_path, encoding="utf-8") as f:
            openapi_spec = yaml.safe_load(f)

        # Verifica que as rotas públicas estão documentadas
        paths = openapi_spec.get("paths", {})
        public_routes = ["/openapi", "/privacy"]

        for route in public_routes:
            self.assertIn(route, paths, f"Public route '{route}' not documented in OpenAPI spec. "
                                        f"Add it to {openapi_path} to ensure GPT Custom clients can discover it.")


if __name__ == "__main__":
    unittest.main()
