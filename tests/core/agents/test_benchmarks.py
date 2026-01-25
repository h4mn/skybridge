# -*- coding: utf-8 -*-
"""
Benchmarks de Performance - ClaudeSDKAdapter vs ClaudeCodeAdapter.

PRD019: Benchmarks para validar melhoria de performance esperada (4-5x).

Estes benchmarks medem:
- Latência de inicialização do adapter
- Latência de extração de resultado
- Latência de parsing (SDK usa tipos nativos vs subprocess usa regex)

NOTA: Benchmarks reais de execução de agente requerem ambiente
de trabalho com Claude Code CLI instalado. Estes benchmarks medem
apenas a sobrecarga do próprio adapter, sem incluir a latência do CLI.
"""
from __future__ import annotations

import json
import time
from typing import List, Dict, Any
from unittest.mock import Mock

import pytest


def create_benchmark_result(
    name: str,
    iterations: int,
    total_time: float,
    unit: str = "ms"
) -> Dict[str, Any]:
    """Cria dict com resultado do benchmark."""
    avg = total_time / iterations
    return {
        "name": name,
        "iterations": iterations,
        "total_time": total_time,
        "unit": unit,
        "avg": avg,
        "avg_display": f"{avg * 1000:.3f}ms" if unit == "s" else f"{avg:.3f}{unit}",
    }


# =============================================================================
# BENCHMARKS: SDK vs Subprocess
# =============================================================================

@pytest.mark.benchmark
def test_benchmark_adapter_initialization():
    """
    Benchmark: Inicialização dos adapters.

    Mede o tempo para instanciar cada adapter.

    Esperado: Ambos devem ser rápidos (são apenas criação de objetos).
    """
    from core.webhooks.infrastructure.agents.claude_agent import ClaudeCodeAdapter
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    iterations = 10000

    # Benchmark subprocess adapter
    start = time.perf_counter()
    for _ in range(iterations):
        adapter = ClaudeCodeAdapter()
    subprocess_time = time.perf_counter() - start

    # Benchmark SDK adapter
    start = time.perf_counter()
    for _ in range(iterations):
        adapter = ClaudeSDKAdapter()
    sdk_time = time.perf_counter() - start

    subprocess_result = create_benchmark_result(
        "ClaudeCodeAdapter initialization",
        iterations,
        subprocess_time,
        "s"
    )
    sdk_result = create_benchmark_result(
        "ClaudeSDKAdapter initialization",
        iterations,
        sdk_time,
        "s"
    )

    print(f"\n{subprocess_result['name']}:")
    print(f"  Total: {subprocess_result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {subprocess_result['avg_display']}")

    print(f"\n{sdk_result['name']}:")
    print(f"  Total: {sdk_result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {sdk_result['avg_display']}")

    # Ambos devem ser muito rápidos (< 1ms por operação)
    assert subprocess_result['avg'] < 0.001
    assert sdk_result['avg'] < 0.001


@pytest.mark.benchmark
def test_benchmark_result_extraction():
    """
    Benchmark: Extração de resultado do SDK.

    Mede o tempo para converter ResultMessage em AgentResult.

    Esperado: SDK deve ser muito rápido (tipos nativos).
    """
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    adapter = ClaudeSDKAdapter()

    # Cria mock de ResultMessage complexo
    def create_mock_result():
        mock = Mock()
        mock.is_error = False
        mock.result = json.dumps({
            "success": True,
            "files_created": ["file1.py", "file2.py", "file3.py"],
            "files_modified": ["main.py", "utils.py"],
            "commit_hash": "abc123",
            "pr_url": "https://github.com/test/test/pull/1",
        })
        mock.duration_ms = 1500
        return mock

    iterations = 10000

    # Benchmark _extract_result
    start = time.perf_counter()
    for _ in range(iterations):
        result_msg = create_mock_result()
        agent_result = adapter._extract_result(result_msg)
    total_time = time.perf_counter() - start

    result = create_benchmark_result(
        "ClaudeSDKAdapter._extract_result()",
        iterations,
        total_time,
        "s"
    )

    print(f"\n{result['name']}:")
    print(f"  Total: {result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {result['avg_display']}")

    # Deve ser muito rápido (< 1ms por operação)
    assert result['avg'] < 0.001, f"Too slow: {result['avg_display']}"


@pytest.mark.benchmark
def test_benchmark_json_parsing_sdk_vs_regex():
    """
    Benchmark: Parsing JSON - SDK (tipado) vs Subprocess (regex).

    Compara parsing de JSON usando tipos nativos vs regex.

    Esperado: SDK é 100% confiável e mais rápido que regex.
    """
    # Simula parsing do SDK (tipado - direto)
    def sdk_parse(json_str: str) -> dict:
        return json.loads(json_str)

    # Simula parsing do subprocess (com regex - simulado)
    def subprocess_parse(json_str: str) -> dict:
        import re
        # Extrai JSON usando regex (similar ao _try_recover_json)
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_str)
        if match:
            json_str = match.group(0)
        return json.loads(json_str)

    # JSON de teste (complexo)
    test_json = json.dumps({
        "success": True,
        "files_created": ["file1.py", "file2.py", "file3.py"],
        "files_modified": ["main.py", "utils.py"],
        "commit_hash": "abc123",
    })

    iterations = 10000

    # Benchmark SDK parse
    start = time.perf_counter()
    for _ in range(iterations):
        result = sdk_parse(test_json)
    sdk_time = time.perf_counter() - start

    # Benchmark subprocess parse (com regex)
    start = time.perf_counter()
    for _ in range(iterations):
        result = subprocess_parse(test_json)
    subprocess_time = time.perf_counter() - start

    sdk_result = create_benchmark_result(
        "SDK parsing (json.loads)",
        iterations,
        sdk_time,
        "s"
    )
    subprocess_result = create_benchmark_result(
        "Subprocess parsing (regex + json.loads)",
        iterations,
        subprocess_time,
        "s"
    )

    print(f"\n{sdk_result['name']}:")
    print(f"  Total: {sdk_result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {sdk_result['avg_display']}")

    print(f"\n{subprocess_result['name']}:")
    print(f"  Total: {subprocess_result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {subprocess_result['avg_display']}")

    # SDK deve ser mais rápido (sem overhead de regex)
    speedup = subprocess_time / sdk_time if sdk_time > 0 else 1.0
    print(f"\nSpeedup: {speedup:.2f}x")

    # Ambos devem ser rápidos, mas SDK tende a ser mais rápido
    assert sdk_result['avg'] < subprocess_result['avg'], \
        f"SDK should be faster: SDK={sdk_result['avg_display']}, Subprocess={subprocess_result['avg_display']}"


@pytest.mark.benchmark
def test_benchmark_feature_flags_parsing():
    """
    Benchmark: Parsing de feature flags.

    Mede performance do helper _env_bool.

    Esperado: Deve ser extremamente rápido (< 0.001ms).
    """
    from runtime.config.feature_flags import _env_bool

    iterations = 100000

    # Benchmark parsing de "true"
    start = time.perf_counter()
    for _ in range(iterations):
        result = _env_bool("TEST_VAR", "true")
    true_time = time.perf_counter() - start

    # Benchmark parsing de "false"
    start = time.perf_counter()
    for _ in range(iterations):
        result = _env_bool("TEST_VAR", "false")
    false_time = time.perf_counter() - start

    true_result = create_benchmark_result(
        "_env_bool('true')",
        iterations,
        true_time,
        "s"
    )
    false_result = create_benchmark_result(
        "_env_bool('false')",
        iterations,
        false_time,
        "s"
    )

    print(f"\n{true_result['name']}:")
    print(f"  Total: {true_result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {true_result['avg_display']}")

    print(f"\n{false_result['name']}:")
    print(f"  Total: {false_result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {false_result['avg_display']}")

    # Deve ser extremamente rápido (< 0.001ms por operação)
    assert true_result['avg'] < 0.00001
    assert false_result['avg'] < 0.00001


# =============================================================================
# BENCHMARKS: WebSocket Console
# =============================================================================

@pytest.mark.benchmark
def test_benchmark_console_message_serialization():
    """
    Benchmark: Serialização de ConsoleMessage para WebSocket.

    Mede tempo para converter ConsoleMessage para JSON string.

    Esperado: Deve ser rápido (< 0.1ms).
    """
    from runtime.delivery.websocket import ConsoleMessage
    from datetime import datetime

    iterations = 10000

    msg = ConsoleMessage(
        timestamp=datetime.now().isoformat(),
        job_id="test-job-123",
        level="info",
        message="Test message",
        metadata={"key": "value"},
    )

    # Benchmark model_dump_json
    start = time.perf_counter()
    for _ in range(iterations):
        json_str = msg.model_dump_json()
    total_time = time.perf_counter() - start

    result = create_benchmark_result(
        "ConsoleMessage.model_dump_json()",
        iterations,
        total_time,
        "s"
    )

    print(f"\n{result['name']}:")
    print(f"  Total: {result['total_time'] * 1000:.2f}ms")
    print(f"  Average: {result['avg_display']}")

    # Deve ser rápido (< 0.1ms por operação)
    assert result['avg'] < 0.0001, f"Too slow: {result['avg_display']}"


# =============================================================================
# BENCHMARKS: Custom Tools
# =============================================================================

@pytest.mark.benchmark
def test_benchmark_skybridge_tools():
    """
    Benchmark: Execução de custom tools do Skybridge.

    Mede latência das custom tools (log, progress, checkpoint).

    Nota: As funções helper (send_log, send_progress, create_checkpoint)
    são síncronas e imprimem no stderr. Este benchmark mede a latência
    dessas funções helper que são usadas internamente.
    """
    from core.webhooks.infrastructure.agents.skybridge_tools import (
        send_log,
        send_progress,
        create_checkpoint,
    )

    iterations = 10000

    # Benchmark send_log (função helper síncrona)
    start = time.perf_counter()
    for _ in range(iterations):
        send_log(
            level="info",
            message="Test log message",
            metadata={"key": "value"},
        )
    log_time = time.perf_counter() - start

    # Benchmark send_progress (função helper síncrona)
    start = time.perf_counter()
    for _ in range(iterations):
        send_progress(
            percent=50,
            message="50% complete",
        )
    progress_time = time.perf_counter() - start

    # Benchmark create_checkpoint (função helper síncrona)
    start = time.perf_counter()
    for _ in range(iterations):
        create_checkpoint(
            label="checkpoint-1",
            description="Test checkpoint",
        )
    checkpoint_time = time.perf_counter() - start

    log_result = create_benchmark_result("send_log()", iterations, log_time, "s")
    progress_result = create_benchmark_result("send_progress()", iterations, progress_time, "s")
    checkpoint_result = create_benchmark_result("create_checkpoint()", iterations, checkpoint_time, "s")

    print(f"\n{log_result['name']}:")
    print(f"  Average: {log_result['avg_display']}")

    print(f"\n{progress_result['name']}:")
    print(f"  Average: {progress_result['avg_display']}")

    print(f"\n{checkpoint_result['name']}:")
    print(f"  Average: {checkpoint_result['avg_display']}")

    # Todas devem ser muito rápidas (< 0.001ms por operação)
    assert log_result['avg'] < 0.001
    assert progress_result['avg'] < 0.001
    assert checkpoint_result['avg'] < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
