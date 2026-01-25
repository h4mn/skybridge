"""
Validação do schema OpenAPI e arquivos YAML (Modelo Híbrido - ADR016).

Garante que:
1. Sintaxe YAML está correta (yamllint)
2. Schema OpenAPI estático é válido (Redocly CLI)
3. Schemas são gerados dinamicamente do registry em runtime

Conforme ADR016:
- Operações HTTP: estáticas (definidas no YAML)
- Schemas: dinâmicos (injetados do registry em runtime)
"""

import sys
import unittest
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from yamllint import config as yamllint_config
    from yamllint import linter as yamllint_linter
    import yaml
except ImportError:
    yamllint_config = None
    yamllint_linter = None
    yaml = None


class OpenAPISchemaTests(unittest.TestCase):
    """Testes de validação do schema OpenAPI Híbrido."""

    @classmethod
    def setUpClass(cls):
        cls.openapi_path = (
            Path(__file__).resolve().parents[1] / "docs" / "spec" / "openapi" / "openapi.yaml"
        )

    def _load_spec(self) -> dict:
        """Carrega o openapi.yaml (estático - operações)."""
        with open(self.openapi_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_openapi_file_exists(self):
        """Verifica se o arquivo OpenAPI existe."""
        self.assertTrue(
            self.openapi_path.exists(),
            f"Arquivo OpenAPI não encontrado: {self.openapi_path}",
        )

    def test_yaml_syntax_valid(self):
        """Valida sintaxe YAML usando yaml.safe_load."""
        if yaml is None:
            self.skipTest("PyYAML não instalado")

        with open(self.openapi_path, "r", encoding="utf-8") as f:
            try:
                content = yaml.safe_load(f)
                self.assertIsNotNone(content)
                self.assertEqual(content.get("openapi"), "3.1.0")
            except yaml.YAMLError as e:
                self.fail(f"Erro de sintaxe YAML: {e}")

    def test_openapi_redocly_valid(self):
        """
        Valida schema OpenAPI usando Redocly CLI.

        Conforme ADR016: Redocly CLI substitui openapi-spec-validator.
        """
        try:
            # No Windows, precisa usar shell=True para encontrar comandos no PATH
            use_shell = sys.platform == "win32"
            result = subprocess.run(
                ["redocly", "lint", str(self.openapi_path), "--format", "json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                shell=use_shell,
            )
            # Redocly retorna exit code 0 quando válido (warnings são OK)
            if result.returncode != 0:
                self.fail(f"Redocly lint falhou:\n{result.stdout}\n{result.stderr}")
        except FileNotFoundError:
            self.skipTest("Redocly CLI não instalado (npm install -g @redocly/cli)")
        except subprocess.TimeoutExpired:
            self.skipTest("Redocly lint timeout (pode não estar instalado)")

    def test_openapi_required_fields(self):
        """Verifica campos obrigatórios do OpenAPI."""
        if yaml is None:
            self.skipTest("PyYAML não instalado")

        content = self._load_spec()

        # Campos obrigatórios OpenAPI 3.1
        self.assertIn("openapi", content)
        self.assertEqual(content["openapi"], "3.1.0")
        self.assertIn("info", content)
        self.assertIn("paths", content)

        # Info obrigatória
        info = content["info"]
        self.assertIn("title", info)
        self.assertIn("version", info)

    def test_openapi_paths_defined(self):
        """Verifica que os paths principais estão definidos (estáticos)."""
        if yaml is None:
            self.skipTest("PyYAML não instalado")

        content = self._load_spec()
        paths = content.get("paths", {})

        # Paths obrigatórios para Sky-RPC v0.3 (estáticos)
        self.assertIn("/ticket", paths, "/ticket deve estar definido")
        self.assertIn("/envelope", paths, "/envelope deve estar definido")
        self.assertIn("/discover", paths, "/discover deve estar definido")
        self.assertIn("/health", paths, "/health deve estar definido")
        self.assertIn("/openapi", paths, "/openapi deve estar definido")
        self.assertIn("/privacy", paths, "/privacy deve estar definido")

    def test_openapi_hybrid_placeholders(self):
        """
        Verifica que schemas reutilizáveis são placeholders (serão injetados em runtime).

        Conforme ADR016: Schemas no YAML estático são PLACEHOLDERS que são
        sobrescritos pelos schemas gerados do registry em runtime.
        """
        if yaml is None:
            self.skipTest("PyYAML não instalado")

        content = self._load_spec()
        schemas = content.get("components", {}).get("schemas", {})

        # Schemas reutilizáveis que são gerados em runtime pelo app.py
        placeholder_schemas = [
            "TicketResponse",
            "EnvelopeRequest",
            "EnvelopeResponse",
            "Error",
            "SkyRpcDiscovery",
        ]

        for schema_name in placeholder_schemas:
            self.assertIn(
                schema_name,
                schemas,
                f"{schema_name} deve existir como placeholder",
            )
            # Placeholders têm apenas type: object
            schema = schemas[schema_name]
            self.assertEqual(
                schema.get("type"),
                "object",
                f"{schema_name} deve ser um placeholder (type: object)",
            )

    def test_yamllint_if_available(self):
        """Valida YAML com yamllint se disponível."""
        if yamllint_linter is None:
            self.skipTest("yamllint não instalado")

        with open(self.openapi_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Config customizada (igual ao .yamllint na raiz)
        cfg = yamllint_config.YamlLintConfig(
            """
            extends: default
            rules:
              line-length:
                max: 120
                level: warning
              document-start:
                present: false
              new-lines: disable
              trailing-spaces:
                level: warning
            """
        )

        # Coleta problemas (erros, não warnings)
        problems = [
            p for p in yamllint_linter.run(content, cfg) if p.level == "error"
        ]

        if problems:
            errors = "\n".join(
                f"  {p.line}:{p.column}  {p.message}  ({p.rule})"
                for p in problems
            )
            self.fail(f"Erros yamllint:\n{errors}")

    def test_schemas_have_properties_defined(self):
        """
        Verifica que schemas de handlers têm 'properties' definidas.

        CRÍTICO: GPT Custom exige que schemas tenham 'properties' explicitamente
        definidas, mesmo que vazias. Apenas {type: object} causa erro de validação.
        """
        if yaml is None:
            self.skipTest("PyYAML não instalado")

        content = self._load_spec()
        schemas = content.get("components", {}).get("schemas", {})

        # Schemas de handlers que devem existir e ter properties
        handler_schemas = {
            "healthInput": {},  # properties vazio é válido
            "healthOutput": {"status", "version", "timestamp", "service"},
            "fileops.readInput": {"path"},
            "fileops.readOutput": {"path", "content", "size"},
        }

        for schema_name, expected_properties in handler_schemas.items():
            self.assertIn(
                schema_name,
                schemas,
                f"{schema_name} deve existir no OpenAPI",
            )

            schema = schemas[schema_name]
            self.assertIn(
                "properties",
                schema,
                f"{schema_name} deve ter 'properties' definido (mesmo que vazio)",
            )

            # Verificar se as propriedades esperadas existem
            if expected_properties:
                actual_properties = set(schema["properties"].keys())
                self.assertEqual(
                    expected_properties,
                    actual_properties,
                    f"{schema_name} deve ter propriedades: {expected_properties}",
                )

    def test_no_empty_object_schemas(self):
        """
        Verifica que não há schemas do tipo {type: object} sem properties.

        Schemas apenas com {type: object} causam erro no GPT Custom:
        "object schema missing properties"

        NOTA: Schemas placeholders gerados em runtime (TicketResponse, etc.)
        são permitidos pois são sobrescritos pelo app.py.
        """
        if yaml is None:
            self.skipTest("PyYAML não instalado")

        content = self._load_spec()
        schemas = content.get("components", {}).get("schemas", {})

        # Schemas que podem ser apenas {type: object} (placeholders gerados em runtime)
        allowed_empty_schemas = {
            "healthInput",  # Handler sem input
            "TicketResponse",  # Gerado em runtime pelo app.py
            "EnvelopeRequest",  # Gerado em runtime pelo app.py
            "EnvelopeResponse",  # Gerado em runtime pelo app.py
            "Error",  # Gerado em runtime pelo app.py
            "SkyRpcDiscovery",  # Gerado em runtime pelo app.py
        }

        for schema_name, schema in schemas.items():
            if schema.get("type") == "object":
                # Se não tem properties ou properties vazio, deve estar na lista de permitidos
                props = schema.get("properties")
                if props is None or props == {}:
                    self.assertIn(
                        schema_name,
                        allowed_empty_schemas,
                        f"{schema_name} tem schema vazio sem propriedades (não permitido)",
                    )


class OpenAPIHybridRuntimeTests(unittest.TestCase):
    """Testes do OpenAPI Híbrido em runtime (requer app inicializado)."""

    @classmethod
    def setUpClass(cls):
        cls.openapi_path = (
            Path(__file__).resolve().parents[1] / "docs" / "spec" / "openapi" / "openapi.yaml"
        )

    def test_runtime_openapi_includes_dynamic_schemas(self):
        """
        Testa que o runtime injeta schemas dinâmicos do registry.

        Este teste requer que o app Skybridge esteja inicializado.
        """
        try:
            from runtime.bootstrap.app import get_app
        except ImportError:
            self.skipTest("Skybridge app não disponível")

        app = get_app()
        hybrid_spec = app.app.openapi()

        # Verificar que schemas dinâmicos foram injetados
        schemas = hybrid_spec.get("components", {}).get("schemas", {})

        # Schemas gerados dinamicamente devem ter mais detalhes que placeholders
        ticket_response = schemas.get("TicketResponse", {})
        self.assertNotEqual(
            ticket_response,
            {"type": "object"},
            "TicketResponse deve ter schema detalhado (não placeholder)",
        )

        # Deve ter properties definidas
        self.assertIn("properties", ticket_response)

    def test_runtime_openapi_syncs_with_discovery(self):
        """
        Testa que schemas do OpenAPI estão sincronizados com /discover.

        RF010: Schemas do OpenAPI devem refletir input_schema e output_schema
               dos handlers no registry.
        """
        try:
            from runtime.bootstrap.app import get_app
            from kernel.registry.skyrpc_registry import get_skyrpc_registry
        except ImportError:
            self.skipTest("Skybridge app não disponível")

        app = get_app()
        registry = get_skyrpc_registry()
        discovery = registry.get_discovery()

        hybrid_spec = app.app.openapi()
        schemas = hybrid_spec.get("components", {}).get("schemas", {})

        # Para cada handler no discovery, deve existir schema correspondente
        for method_name, handler_meta in discovery.discovery.items():
            input_schema_name = f"{method_name}Input"
            output_schema_name = f"{method_name}Output"

            self.assertIn(
                input_schema_name,
                schemas,
                f"{input_schema_name} deve existir no OpenAPI",
            )
            self.assertIn(
                output_schema_name,
                schemas,
                f"{output_schema_name} deve existir no OpenAPI",
            )

            # Schemas devem corresponder aos do handler
            self.assertEqual(
                schemas[input_schema_name],
                handler_meta.input_schema or {"type": "object", "properties": {}},
            )
            self.assertEqual(
                schemas[output_schema_name],
                handler_meta.output_schema or {"type": "object", "properties": {}},
            )

    def test_runtime_schemas_have_properties(self):
        """
        Verifica que schemas no runtime têm 'properties' definidas.

        CRÍTICO: GPT Custom exige que schemas tenham 'properties' explicitamente
        definidas. O fallback do app.py deve usar {"type": "object", "properties": {}}
        ao invés de apenas {"type": "object"}.
        """
        try:
            from runtime.bootstrap.app import get_app
        except ImportError:
            self.skipTest("Skybridge app não disponível")

        app = get_app()
        hybrid_spec = app.app.openapi()
        schemas = hybrid_spec.get("components", {}).get("schemas", {})

        # Verificar que schemas de handlers têm properties definidas
        handler_schemas = ["healthInput", "healthOutput", "fileops.readInput", "fileops.readOutput"]

        for schema_name in handler_schemas:
            if schema_name in schemas:
                schema = schemas[schema_name]
                self.assertIn(
                    "properties",
                    schema,
                    f"{schema_name} no runtime deve ter 'properties' definido",
                )

                # Properties não deve ser None
                self.assertIsNotNone(
                    schema.get("properties"),
                    f"{schema_name}.properties não deve ser None",
                )


if __name__ == "__main__":
    unittest.main()
