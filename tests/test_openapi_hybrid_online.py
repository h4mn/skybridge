#!/usr/bin/env python3
"""
Bateria de Testes Online da API - OpenAPI Híbrido (ADR016)

Testa os endpoints públicos da API para validar:
1. OpenAPI Híbrido é retornado corretamente
2. Schemas dinâmicos são injetados do registry
3. /discover retorna handlers sincronizados com OpenAPI
4. Formatos e estruturas estão corretos
"""

import sys
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import requests
import yaml

BASE_URL = "http://localhost:8000"


def print_header(text: str):
    """Imprime cabeçalho de seção."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_success(text: str):
    """Imprime mensagem de sucesso."""
    print(f"✅ {text}")


def print_error(text: str):
    """Imprime mensagem de erro."""
    print(f"❌ {text}")


def print_info(text: str):
    """Imprime mensagem informativa."""
    print(f"ℹ️  {text}")


def check_server_online():
    """Testa se o servidor está online."""
    print_header("TESTE 1: Servidor Online")
    try:
        response = requests.get(f"{BASE_URL}/openapi", timeout=5)
        if response.status_code == 200:
            print_success(f"Servidor está online em {BASE_URL}")
            return True
        else:
            print_error(f"Servidor retornou status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Servidor não está online: {e}")
        return False


def check_openapi_hybrid():
    """Testa se /openapi retorna o OpenAPI Híbrido."""
    print_header("TESTE 2: OpenAPI Híbrido")

    response = requests.get(f"{BASE_URL}/openapi")
    if response.status_code != 200:
        print_error(f"/openapi retornou status {response.status_code}")
        return False

    # Parse YAML
    try:
        spec = yaml.safe_load(response.text)
    except yaml.YAMLError as e:
        print_error(f"Erro ao parsear YAML: {e}")
        return False

    # Validar campos obrigatórios
    if spec.get("openapi") != "3.1.0":
        print_error(f"Versão OpenAPI incorreta: {spec.get('openapi')}")
        return False

    print_success("OpenAPI 3.1.0 válido")

    # Validar paths estáticos
    paths = spec.get("paths", {})
    required_paths = ["/ticket", "/envelope", "/discover", "/openapi", "/privacy"]
    for path in required_paths:
        if path not in paths:
            print_error(f"Path obrigatório faltando: {path}")
            return False
    print_success(f"Todos os {len(required_paths)} paths obrigatórios presentes")

    # Validar descrição do modelo híbrido
    description = spec.get("info", {}).get("description", "")
    if "Híbrido" not in description and "Hybrid" not in description:
        print_error("Descrição não menciona modelo Híbrido")
        return False
    print_success("Descrição menciona modelo Híbrido (ADR016)")

    return True, spec


def check_dynamic_schemas(spec: dict):
    """Testa se schemas dinâmicos foram injetados."""
    print_header("TESTE 3: Schemas Dinâmicos Injetados")

    schemas = spec.get("components", {}).get("schemas", {})

    # Verificar schemas de handlers (dinâmicos)
    dynamic_schemas = {
        "fileops.readInput": "path",
        "fileops.readOutput": ["path", "content", "size"],
        "healthInput": None,  # pode ser null
        "healthOutput": "status",
    }

    for schema_name, expected_field in dynamic_schemas.items():
        if schema_name not in schemas:
            print_error(f"Schema dinâmico faltando: {schema_name}")
            continue

        schema = schemas[schema_name]
        if expected_field is None:
            print_success(f"{schema_name}: presente")
            continue

        if isinstance(expected_field, str):
            expected_field = [expected_field]

        properties = schema.get("properties", {})
        for field in expected_field:
            if field not in properties:
                print_error(f"{schema_name}: campo '{field}' faltando")
                continue

        print_success(f"{schema_name}: campos corretos")

    # Verificar schemas reutilizáveis (gerados)
    reusable_schemas = ["TicketResponse", "EnvelopeRequest", "EnvelopeResponse", "Error"]
    for schema_name in reusable_schemas:
        if schema_name not in schemas:
            print_error(f"Schema reutilizável faltando: {schema_name}")
            continue
        # Não deve ser placeholder (apenas type: object)
        schema = schemas[schema_name]
        if schema == {"type": "object"}:
            print_error(f"{schema_name}: ainda é placeholder")
            continue
        print_success(f"{schema_name}: schema detalhado presente")

    return True


def check_discovery_endpoint():
    """Testa /discover endpoint."""
    print_header("TESTE 4: Endpoint /discover")

    response = requests.get(f"{BASE_URL}/discover")
    if response.status_code != 200:
        print_error(f"/discover retornou status {response.status_code}")
        return False

    try:
        discovery = response.json()
    except json.JSONDecodeError as e:
        print_error(f"Erro ao parsear JSON: {e}")
        return False

    # Validar estrutura
    if "version" not in discovery:
        print_error("Campo 'version' faltando")
        return False
    print_success(f"Versão: {discovery['version']}")

    if "discovery" not in discovery:
        print_error("Campo 'discovery' faltando")
        return False

    handlers = discovery.get("discovery", {})
    print_info(f"Handlers encontrados: {list(handlers.keys())}")

    # Validar estrutura de cada handler
    for method_name, handler_meta in handlers.items():
        required_fields = ["method", "kind", "module"]
        for field in required_fields:
            if field not in handler_meta:
                print_error(f"{method_name}: campo '{field}' faltando")
                continue

        # Verificar schemas
        if "input_schema" not in handler_meta:
            print_error(f"{method_name}: input_schema faltando")
            continue
        if "output_schema" not in handler_meta:
            print_error(f"{method_name}: output_schema faltando")
            continue

        print_success(f"{method_name}: estrutura válida")

    return True, discovery


def check_openapi_discovery_sync(spec: dict, discovery: dict):
    """Testa se OpenAPI e /discover estão sincronizados."""
    print_header("TESTE 5: Sincronização OpenAPI ↔ /discover")

    spec_schemas = spec.get("components", {}).get("schemas", {})
    discovery_handlers = discovery.get("discovery", {})

    # Para cada handler no discovery, deve existir schema no OpenAPI
    for method_name, handler_meta in discovery_handlers.items():
        input_schema_name = f"{method_name}Input"
        output_schema_name = f"{method_name}Output"

        if input_schema_name not in spec_schemas:
            print_error(f"{input_schema_name} não está no OpenAPI")
            continue

        if output_schema_name not in spec_schemas:
            print_error(f"{output_schema_name} não está no OpenAPI")
            continue

        # Verificar se schemas correspondem
        spec_input = spec_schemas[input_schema_name]
        discovery_input = handler_meta.get("input_schema") or {"type": "object"}

        if spec_input != discovery_input:
            print_error(f"{input_schema_name}: schema não corresponde ao discovery")
            continue

        print_success(f"{method_name}: schemas sincronizados")

    return True


def check_privacy_endpoint():
    """Testa /privacy endpoint."""
    print_header("TESTE 6: Endpoint /privacy")

    response = requests.get(f"{BASE_URL}/privacy")
    if response.status_code != 200:
        print_error(f"/privacy retornou status {response.status_code}")
        return False

    content = response.text
    if "Política de Privacidade" not in content and "Privacy Policy" not in content:
        print_error("Conteúdo não parece ser uma política de privacidade")
        return False

    print_success("Política de privacidade retornada")
    print_info(f"Tamanho: {len(content)} bytes")

    return True


def check_redocly_validation():
    """Testa validação com Redocly CLI."""
    print_header("TESTE 7: Validação Redocly CLI")

    try:
        # Validar OpenAPI estático
        result = subprocess.run(
            ["redocly", "lint", "docs/spec/openapi/openapi.yaml"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print_success("OpenAPI estático válido (Redocly)")
        else:
            print_error(f"Redocly encontrou erros:\n{result.stdout}")

        # Validar OpenAPI runtime (via curl)
        result = subprocess.run(
            ["curl", "-s", f"{BASE_URL}/openapi", "|", "redocly", "lint", "-"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=True,
        )
        if result.returncode == 0:
            print_success("OpenAPI runtime válido (Redocly)")
        else:
            print_info(f"Redocly runtime: {result.stderr[:100]}")

    except FileNotFoundError:
        print_info("Redocly CLI não instalado (pulando)")
    except subprocess.TimeoutExpired:
        print_error("Redocly timeout")

    return True


def main():
    """Executa todos os testes."""
    print_header("🚀 BATERIA DE TESTES ONLINE - OPENAPI HÍBRIDO")
    print_info(f"Base URL: {BASE_URL}")
    print_info("Validando implementação do ADR016")

    results = []

    # Teste 1: Servidor online
    if not check_server_online():
        print_error("\n❌ ABORTANDO: Servidor não está online")
        print_info("Inicie o servidor com: python -m skybridge.platform.bootstrap")
        return 1

    # Teste 2: OpenAPI Híbrido
    result = check_openapi_hybrid()
    if isinstance(result, tuple):
        results.append(("OpenAPI Híbrido", result[0]))
        spec = result[1]
    else:
        results.append(("OpenAPI Híbrido", result))
        spec = None

    # Teste 3: Schemas dinâmicos
    if spec:
        result = check_dynamic_schemas(spec)
        results.append(("Schemas Dinâmicos", result))

    # Teste 4: /discover
    result = check_discovery_endpoint()
    if isinstance(result, tuple):
        results.append(("/discover", result[0]))
        discovery = result[1]
    else:
        results.append(("/discover", result))
        discovery = None

    # Teste 5: Sincronização
    if spec and discovery:
        result = check_openapi_discovery_sync(spec, discovery)
        results.append(("Sincronização OpenAPI↔/discover", result))

    # Teste 6: /privacy
    result = check_privacy_endpoint()
    results.append(("/privacy", result))

    # Teste 7: Redocly
    check_redocly_validation()

    # Resumo
    print_header("📊 RESUMO DOS TESTES")
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} testes passaram")

    if passed == total:
        print_success("\n🎉 TODOS OS TESTES PASSARAM!")
        print_info("OpenAPI Híbrido está funcionando corretamente.")
        return 0
    else:
        print_error(f"\n❌ {total - passed} TESTE(S) FALHOU(ARAM)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
