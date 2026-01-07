import os
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skybridge.platform.bootstrap.app import get_app
from skybridge.platform.config import config as config_module
from skybridge.platform.delivery import routes as routes_module
from skybridge.platform.delivery.routes import EnvelopeDetail, _parse_detail


class SkyRpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SKYBRIDGE_API_KEYS"] = "test-key:test-client"
        os.environ["SKYBRIDGE_METHOD_POLICY"] = "test-client:health,fileops.read"
        os.environ["SKYBRIDGE_RATE_LIMIT_PER_MINUTE"] = "0"
        os.environ["ALLOW_LOCALHOST"] = "false"
        config_module._security_config = None
        cls.client = TestClient(get_app().app)

    def setUp(self):
        self._apply_security_env({})
        routes_module._rate_limit_state.clear()
        routes_module._ticket_store.clear()

    def _apply_security_env(self, overrides: dict[str, str]) -> None:
        base_env = {
            "SKYBRIDGE_API_KEYS": "test-key:test-client",
            "SKYBRIDGE_METHOD_POLICY": "test-client:health,fileops.read",
            "SKYBRIDGE_RATE_LIMIT_PER_MINUTE": "0",
            "ALLOW_LOCALHOST": "false",
        }
        base_env.update(overrides)
        for key, value in base_env.items():
            os.environ[key] = value
        config_module._security_config = config_module.load_security_config()
        routes_module._rate_limit_state.clear()
        routes_module._ticket_store.clear()

    def test_ticket_and_envelope_health(self):
        response = self.client.get("/ticket", params={"method": "health"}, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("ok"))
        ticket_id = body["ticket"]["id"]

        envelope = {"ticket_id": ticket_id}
        response = self.client.post("/envelope", json=envelope, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertIn("result", body)
        self.assertEqual(body["result"].get("status"), "healthy")

    def test_ticket_and_envelope_fileops_read(self):
        response = self.client.get("/ticket", params={"method": "fileops.read"}, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("ok"))
        ticket_id = body["ticket"]["id"]

        envelope = {"ticket_id": ticket_id, "detalhe": "README.md"}
        response = self.client.post("/envelope", json=envelope, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body["result"].get("path"), "README.md")
        self.assertIn("content", body["result"])

    # ============ Sky-RPC v0.2 Tests ============

    def test_envelope_v02_detail_as_string_legacy(self):
        """Teste v0.2: detail como string (compatibilidade legado)."""
        response = self.client.get("/ticket", params={"method": "health"}, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        ticket_id = response.json()["ticket"]["id"]

        envelope = {"ticket_id": ticket_id, "detail": "ping"}
        response = self.client.post("/envelope", json=envelope, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("ok"))

    def test_envelope_v02_detail_as_structured(self):
        """Teste v0.2: detail como objeto estruturado."""
        response = self.client.get("/ticket", params={"method": "fileops.read"}, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        ticket_id = response.json()["ticket"]["id"]

        envelope = {
            "ticket_id": ticket_id,
            "detail": {
                "context": "fileops.read",
                "subject": "README.md",
                "action": "read",
                "payload": {"encoding": "utf-8"}
            }
        }
        response = self.client.post("/envelope", json=envelope, headers={"X-API-Key": "test-key"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body["result"].get("path"), "README.md")

    def test_envelope_v02_payload_empty_4221(self):
        """Teste v0.2: payload vazio deve retornar erro 4221."""
        with self.assertRaises(ValidationError) as ctx:
            EnvelopeDetail(
                context="fileops.read",
                action="read",
                payload={}
            )
        self.assertIn("empty", str(ctx.exception).lower())

    def test_envelope_v02_payload_minProperties_1(self):
        """Teste v0.2: payload com 0 propriedades deve falhar."""
        with self.assertRaises(ValidationError):
            EnvelopeDetail(
                context="fileops.read",
                action="read",
                payload={}
            )

    def test_envelope_v02_payload_with_one_property_ok(self):
        """Teste v0.2: payload com 1+ propriedades deve OK."""
        detail = EnvelopeDetail(
            context="fileops.read",
            subject="README.md",
            action="read",
            payload={"encoding": "utf-8"}
        )
        self.assertEqual(detail.payload, {"encoding": "utf-8"})

    def test_parse_detail_string_legacy(self):
        """Teste _parse_detail: detail como string retorna formato legado."""
        flat_params, error, detail_type = _parse_detail("README.md", {})
        self.assertIsNone(error)
        self.assertEqual(detail_type, "legacy")
        self.assertEqual(flat_params, {"detalhe": "README.md"})

    def test_parse_detail_structured_object(self):
        """Teste _parse_detail: detail como EnvelopeDetail."""
        detail = EnvelopeDetail(
            context="fileops.read",
            subject="test.txt",
            action="read",
            payload={"encoding": "utf-8"}
        )
        flat_params, error, detail_type = _parse_detail(detail, {})
        self.assertIsNone(error)
        self.assertEqual(detail_type, "structured")
        # subject é mapeado como "detalhe" para o primeiro parâmetro required
        self.assertEqual(flat_params, {"encoding": "utf-8", "detalhe": "test.txt"})

    def test_parse_detail_reverse_mapping(self):
        """Teste _parse_detail: mapeamento reverso detalhe -> detail."""
        model_extra = {"detalhe": "README.md", "other_field": "ignored"}
        flat_params, error, detail_type = _parse_detail(None, model_extra)
        self.assertIsNone(error)
        self.assertEqual(detail_type, "legacy")
        self.assertEqual(flat_params, {"detalhe": "README.md"})

    def test_envelope_v02_required_fields(self):
        """Teste v0.2: campos obrigatórios do EnvelopeDetail."""
        # context faltando
        with self.assertRaises(ValidationError):
            EnvelopeDetail(subject="x", action="read", payload={})
        # action faltando
        with self.assertRaises(ValidationError):
            EnvelopeDetail(context="x", subject="y", payload={})
        # payload faltando
        with self.assertRaises(ValidationError):
            EnvelopeDetail(context="x", action="read")

    def test_envelope_v02_subject_optional(self):
        """Teste v0.2: subject é opcional."""
        detail = EnvelopeDetail(
            context="tasks.list",
            action="list",
            payload={"limit": 10}
        )
        self.assertIsNone(detail.subject)


if __name__ == "__main__":
    unittest.main()
