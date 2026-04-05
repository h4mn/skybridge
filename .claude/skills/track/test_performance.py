#!/usr/bin/env python3
"""
Test Suite de Performance /track

Mede tempo real das operações para comparar verify-first vs optimistic-start.
"""

import time
import json
import sys
from pathlib import Path
from datetime import datetime

# Adicionar path do orchestrator
sys.path.insert(0, str(Path(__file__).parent))

# Mock MCP calls para testes isolados
class MockTogglMCP:
    """Mock MCP Toggl para testes de performance."""

    def __init__(self, latency_ms=100):
        self.latency_ms = latency_ms
        self.calls = []

    def get_current_entry(self):
        """Simula get_current_entry com latência."""
        start = time.perf_counter()
        time.sleep(self.latency_ms / 1000)
        self.calls.append({
            "method": "get_current_entry",
            "latency_ms": self.latency_ms,
            "timestamp": datetime.now().isoformat()
        })
        return {"running": False}

    def start_timer(self, params):
        """Simula start_timer com latência."""
        start = time.perf_counter()
        # Simular latência de rede real (25s médio atual)
        time.sleep(self.latency_ms / 1000)
        self.calls.append({
            "method": "start_timer",
            "latency_ms": self.latency_ms,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })
        return {
            "id": 12345,
            "start": datetime.now().isoformat(),
            "description": params.get("description", "Test")
        }


def measure_verify_first_approach(mock_mcp):
    """
    Mede abordagem atual: verify-first.
    1. get_current_entry()
    2. Decisão
    3. start_timer()
    """
    start_total = time.perf_counter()

    # Step 1: Verify (get_current_entry)
    t1 = time.perf_counter()
    current = mock_mcp.get_current_entry()
    verify_time = (time.perf_counter() - t1) * 1000

    # Step 2: Decision (instantâneo)
    t2 = time.perf_counter()
    decision = {"action": "start"}  # Simplificado
    decision_time = (time.perf_counter() - t2) * 1000

    # Step 3: Start timer
    t3 = time.perf_counter()
    result = mock_mcp.start_timer({"description": "Test verify-first"})
    start_time = (time.perf_counter() - t3) * 1000

    total_time = (time.perf_counter() - start_total) * 1000

    return {
        "approach": "verify_first",
        "verify_time_ms": round(verify_time, 2),
        "decision_time_ms": round(decision_time, 2),
        "start_time_ms": round(start_time, 2),
        "total_time_ms": round(total_time, 2),
        "calls": mock_mcp.calls
    }


def measure_optimistic_approach(mock_mcp):
    """
    Mede abordagem otimista: optimistic-start.
    1. start_timer() (fire-and-forget)
    2. Verify em background (não medido para perceived)
    """
    start_total = time.perf_counter()

    # Step 1: Start IMMEDIATE (perceived time)
    t1 = time.perf_counter()
    result = mock_mcp.start_timer({"description": "Test optimistic"})
    start_time = (time.perf_counter() - t1) * 1000

    # Perceived time encerra aqui (usuário vê resposta)
    perceived_time = start_time

    # Step 2: Background verification (não afeta perceived)
    t2 = time.perf_counter()
    current = mock_mcp.get_current_entry()
    verify_time = (time.perf_counter() - t2) * 1000

    total_time = (time.perf_counter() - start_total) * 1000

    return {
        "approach": "optimistic_start",
        "start_time_ms": round(start_time, 2),
        "verify_time_ms": round(verify_time, 2),
        "perceived_time_ms": round(perceived_time, 2),
        "total_time_ms": round(total_time, 2),
        "calls": mock_mcp.calls
    }


def run_comparison(mcp_latency_ms=100):
    """Roda comparação entre abordagens."""
    print(f"\n{'='*60}")
    print(f"Test Suite: /track Performance Comparison")
    print(f"MCP Latency: {mcp_latency_ms}ms (simulado)")
    print(f"{'='*60}\n")

    # Test 1: Verify-first (atual)
    mock1 = MockTogglMCP(latency_ms=mcp_latency_ms)
    result_verify = measure_verify_first_approach(mock1)

    # Test 2: Optimistic-start (proposta)
    mock2 = MockTogglMCP(latency_ms=mcp_latency_ms)
    result_optimistic = measure_optimistic_approach(mock2)

    # Results
    print("VERIFY-FIRST (atual):")
    print(f"  Verify:     {result_verify['verify_time_ms']}ms")
    print(f"  Decision:   {result_verify['decision_time_ms']}ms")
    print(f"  Start:      {result_verify['start_time_ms']}ms")
    print(f"  ─────────────────────────────────")
    print(f"  TOTAL:      {result_verify['total_time_ms']}ms")

    print("\nOPTIMISTIC-START (proposta):")
    print(f"  Start:      {result_optimistic['start_time_ms']}ms ← PERCEIVED")
    print(f"  Verify:     {result_optimistic['verify_time_ms']}ms ← background")
    print(f"  ─────────────────────────────────")
    print(f"  TOTAL:      {result_optimistic['total_time_ms']}ms")
    print(f"  PERCEIVED:  {result_optimistic['perceived_time_ms']}ms")

    # Comparison
    improvement = result_verify['total_time_ms'] - result_optimistic['perceived_time_ms']
    improvement_pct = (improvement / result_verify['total_time_ms']) * 100

    print(f"\n{'='*60}")
    print(f"MELHORIA PERCEBIDA: {improvement}ms ({improvement_pct:.1f}% mais rápido)")
    print(f"{'='*60}\n")

    return result_verify, result_optimistic


def test_real_mcp_calls():
    """Teste com chamadas MCP reais (não mock)."""
    print("\n" + "="*60)
    print("TESTE REAL: Chamadas MCP Toggl")
    print("="*60 + "\n")

    # Teste real com MCP
    try:
        from mcp_toggl import toggl_get_current_entry, toggl_start_timer

        # Test 1: get_current_entry
        print("1. Testando get_current_entry()...")
        t1 = time.perf_counter()
        current = toggl_get_current_entry()
        t1_elapsed = (time.perf_counter() - t1) * 1000
        print(f"   Resultado: {current}")
        print(f"   Tempo: {t1_elapsed:.0f}ms")

        # Test 2: start_timer
        print("\n2. Testando start_timer()...")
        t2 = time.perf_counter()
        result = toggl_start_timer(
            description="Teste performance /track",
            project_id=219139925,
            tags=["test"],
            workspace_id=20989145
        )
        t2_elapsed = (time.perf_counter() - t2) * 1000
        print(f"   Resultado: entry_id={result.get('entry', {}).get('id')}")
        print(f"   Tempo: {t2_elapsed:.0f}ms")

        print(f"\nTempo total sequencial: {t1_elapsed + t2_elapsed:.0f}ms")

        return {
            "get_current_entry_ms": t1_elapsed,
            "start_timer_ms": t2_elapsed,
            "total_ms": t1_elapsed + t2_elapsed
        }

    except ImportError as e:
        print(f"   MCP não disponível: {e}")
        return None
    except Exception as e:
        print(f"   Erro: {e}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test suite performance /track")
    parser.add_argument("--mode", choices=["mock", "real", "both"], default="mock",
                       help="Modo de teste: mock (simulado), real (MCP), both")
    parser.add_argument("--latency", type=int, default=100,
                       help="Latência simulada em ms (para modo mock)")

    args = parser.parse_args()

    if args.mode in ["mock", "both"]:
        # Testes mockados
        run_comparison(mcp_latency_ms=args.latency)

    if args.mode in ["real", "both"]:
        # Teste real com MCP
        test_real_mcp_calls()
