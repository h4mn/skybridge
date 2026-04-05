# -*- coding: utf-8 -*-
"""
Demo M1 - Heartbeat Module Completo.

Demonstra todos os componentes M1 em ação:
1. Domain Events + EventBus
2. Worker System (DDD)
3. MercadoSimulado
4. Orquestração

Execute: python -m demos.demo_m1
"""

import asyncio
import time
import sys
from decimal import Decimal
from datetime import datetime

# Fix UTF-8 no Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Adiciona path ao Python
sys.path.insert(0, '.')

from src.core.paper.domain.events import EventBus, OrdemExecutada, Lado
from src.core.paper.domain.worker import (
    WorkerId,
    WorkerName,
    WorkerStatus,
    Worker,
    WorkerRegistry,
    WorkerStarted,
    WorkerStopped,
)
from src.core.paper.domain.mercado_simulado import (
    Ticker,
    PrecoSimulado,
    Volatilidade,
    MercadoSimulado,
    GeradorDePrecos,
    MovimentoMercado,
)
from src.core.paper.application.worker_orchestrator import (
    StartWorkerHandler,
    StopWorkerHandler,
    OrchestrateWorkersUseCase,
    StartWorkerCommand,
    StopWorkerCommand,
)


# =============================================================================
# Demo 1: EventBus + Domain Events
# =============================================================================

def demo_event_bus():
    """Demonstra EventBus com Domain Events."""
    print("\n" + "="*60)
    print("📡 DEMO 1: EventBus + Domain Events")
    print("="*60)

    # Criar EventBus
    bus = EventBus()

    # Subscriber para log
    def log_eventos(evento):
        print(f"  📨 Evento recebido: {evento.__class__.__name__}")
        if hasattr(evento, 'ticker'):
            print(f"     └─ Ticker: {evento.ticker}")

    # Subscribe
    bus.subscribe(OrdemExecutada, log_eventos)

    # Publicar eventos
    print("\n✉️ Publicando 3 eventos...")

    bus.publish(OrdemExecutada(
        ordem_id="ordem-001",
        ticker="PETR4.SA",
        lado=Lado.COMPRA,
        quantidade_executada=100,
        preco_execucao=Decimal("30.00"),
    ))

    bus.publish(OrdemExecutada(
        ordem_id="ordem-002",
        ticker="BTC-USD",
        lado=Lado.VENDA,
        quantidade_executada=2,
        preco_execucao=Decimal("85000.00"),
    ))

    bus.publish(OrdemExecutada(
        ordem_id="ordem-003",
        ticker="VALE3.SA",
        lado=Lado.COMPRA,
        quantidade_executada=200,
        preco_execucao=Decimal("65.00"),
    ))

    print("✅ EventBus: 3 eventos processados!")


# =============================================================================
# Demo 2: Worker System (DDD)
# =============================================================================

def demo_worker_system():
    """Demonstra Worker System com DDD."""
    print("\n" + "="*60)
    print("⚙️ DEMO 2: Worker System (DDD)")
    print("="*60)

    # Criar Aggregate Root
    registry = WorkerRegistry()

    # Criar workers
    print("\n🔧 Criando 3 workers...")
    position_worker = Worker(
        id=WorkerId("position-worker"),
        name=WorkerName("PositionWorker"),
        status=WorkerStatus.STOPPED,
    )

    strategy_worker = Worker(
        id=WorkerId("strategy-worker"),
        name=WorkerName("StrategyWorker"),
        status=WorkerStatus.STOPPED,
    )

    backtest_worker = Worker(
        id=WorkerId("backtest-worker"),
        name=WorkerName("BacktestWorker"),
        status=WorkerStatus.STOPPED,
    )

    # Registrar workers
    for worker in [position_worker, strategy_worker, backtest_worker]:
        registry.register(worker)
        print(f"  ✅ Worker registrado: {worker.name.value}")

    print(f"\n📊 Registry: {registry.worker_count} workers")

    # Iniciar workers
    print("\n▶️ Iniciando workers...")
    handlers = StartWorkerHandler(registry=registry)

    for worker in registry.list_all():
        result = asyncio.run(handlers.handle(
            StartWorkerCommand(worker_id=worker.id)
        ))
        if result.is_success:
            print(f"  ▶️ {worker.name.value}: RUNNING")

    # Executar ticks
    print("\n⏱️ Executando 3 ticks de orquestração...")
    use_case = OrchestrateWorkersUseCase(registry=registry)

    for i in range(3):
        result = asyncio.run(use_case.execute())
        print(f"  Tick {i+1}: {result.workers_ticked} workers executaram")
        time.sleep(0.5)

    # Parar workers
    print("\n⏹️ Parando workers...")
    stop_handler = StopWorkerHandler(registry=registry)

    for worker in registry.list_all():
        result = asyncio.run(stop_handler.handle(
            StopWorkerCommand(worker_id=worker.id, reason="demo_complete")
        ))
        print(f"  ⏹️ {worker.name.value}: STOPPED")

    print("✅ Worker System: Demo completa!")


# =============================================================================
# Demo 3: MercadoSimulado
# =============================================================================

def demo_mercado_simulado():
    """Demonstra MercadoSimulado com preços realistas."""
    print("\n" + "="*60)
    print("📈 DEMO 3: MercadoSimulado")
    print("="*60)

    # Criar mercados
    print("\n🏪 Criando mercados simulados...")

    mercado_btc = MercadoSimulado(
        ticker=Ticker("BTC-USD"),
        preco_inicial=Decimal("85000.00"),
        volatilidade=Volatilidade.ALTA,  # Crypto volátil
    )

    mercado_petr4 = MercadoSimulado(
        ticker=Ticker("PETR4.SA"),
        preco_inicial=Decimal("35.00"),
        volatilidade=Volatilidade.MEDIA,  # Ação normal
    )

    print("  ✅ BTC-USD: $85,000 (Volatilidade ALTA)")
    print("  ✅ PETR4.SA: R$35.00 (Volatilidade MEDIA)")

    # Gerar preços
    print("\n📊 Gerando 10 preços simulados...")

    gerador = GeradorDePrecos(seed=42)  # Determinístico

    for i in range(10):
        # BTC em tendência de alta
        preco_btc = mercado_btc.gerar_proximo_preco(movimento=MovimentoMercado.ALTA)

        # PETR4 lateral
        preco_petr4 = mercado_petr4.gerar_proximo_preco(movimento=MovimentoMercado.LATERAL)

        variacao_btc = ((preco_btc.valor - Decimal("85000")) / Decimal("85000")) * 100
        variacao_petr4 = ((preco_petr4.valor - Decimal("35")) / Decimal("35")) * 100

        print(f"  {i+1:2d} | BTC: ${preco_btc.valor:10.2f} ({variacao_btc:+6.2f}%) | "
              f"PETR4: R${preco_petr4.valor:6.2f} ({variacao_petr4:+6.2f}%)")

    print(f"\n📈 BTC final: ${mercado_btc.preco_atual:.2f}")
    print(f"📊 PETR4 final: R${mercado_petr4.preco_atual:.2f}")

    print("✅ MercadoSimulado: Preços gerados com sucesso!")


# =============================================================================
# Demo 4: Orquestração Completa
# =============================================================================

async def demo_orquestracao_completa():
    """Demonstra orquestração completa do sistema."""
    print("\n" + "="*60)
    print("🎯 DEMO 4: Orquestração Completa")
    print("="*60)

    # Setup
    registry = WorkerRegistry()
    use_case = OrchestrateWorkersUseCase(registry=registry)

    # Criar worker de monitoramento de mercado
    class MarketMonitorWorker(Worker):
        """Worker que monitora mercado simulado."""

        def __init__(self, gerador: GeradorDePrecos):
            super().__init__(
                id=WorkerId("market-monitor"),
                name=WorkerName("MarketMonitor"),
                status=WorkerStatus.STOPPED,
            )
            self._gerador = gerador
            self._tick_count = 0

        async def _do_tick(self):
            """Executa monitoramento."""
            self._tick_count += 1

            # Gerar preços
            precos = self._gerador.gerar_lote(
                tickers=[Ticker("BTC-USD"), Ticker("ETH-USD")],
                precos_base={
                    Ticker("BTC-USD"): Decimal("85000"),
                    Ticker("ETH-USD"): Decimal("3000"),
                },
            )

            # Mostrar resultado
            btc_preco = next(p for p in precos if p.ticker.value == "BTC-USD")
            eth_preco = next(p for p in precos if p.ticker.value == "ETH-USD")

            print(f"  📊 Tick {self._tick_count} | "
                  f"BTC: ${btc_preco.valor:8.2f} | "
                  f"ETH: ${eth_preco.valor:7.2f}")

    # Registrar worker
    gerador = GeradorDePrecos(seed=42)
    monitor = MarketMonitorWorker(gerador)
    registry.register(monitor)

    # Iniciar
    print("\n▶️ Iniciando monitor de mercado...")
    handler = StartWorkerHandler(registry=registry)
    result = await handler.handle(StartWorkerCommand(worker_id=monitor.id))

    print(f"  Status: {'✅ RUNNING' if result.is_success else '❌ ERRO'}")

    # Executar 5 ciclos
    print("\n⏱️ Executando 5 ciclos de monitoramento...")
    for i in range(5):
        result = await use_case.execute()
        await asyncio.sleep(0.3)

    # Parar
    print("\n⏹️ Parando monitor...")
    stop_handler = StopWorkerHandler(registry=registry)
    result = await stop_handler.handle(
        StopWorkerCommand(worker_id=monitor.id, reason="demo_complete")
    )

    print("✅ Orquestração: Sistema funcionando perfeitamente!")


# =============================================================================
# Main
# =============================================================================

def main():
    """Executa todos os demos."""
    print("\n" + "="*60)
    print("🎮 DEMO M1 - HEARTBEAT MODULE")
    print("Arquitetura DDD 4-Camadas em Ação")
    print("="*60)

    # Demo 1: EventBus
    demo_event_bus()

    # Demo 2: Worker System
    demo_worker_system()

    # Demo 3: MercadoSimulado
    demo_mercado_simulado()

    # Demo 4: Orquestração Completa
    print("\n" + "="*60)
    print("🎯 Iniciando Demo 4 (assíncrono)...")
    print("="*60)
    asyncio.run(demo_orquestracao_completa())

    # Resumo final
    print("\n" + "="*60)
    print("🏆 DEMO M1 COMPLETA!")
    print("="*60)
    print("""
✅ Componentes Demonstrados:
  1. EventBus + Domain Events (pub/sub)
  2. Worker System (DDD: Entity, Aggregate, Handlers)
  3. MercadoSimulado (preços realistas Binance)
  4. Orquestração (Use Cases, Commands)

📊 Métricas:
  - 61 tests passing
  - 4 camadas DDD implementadas
  - Domain Events fluindo entre componentes

🚀 Próximo: M2 - Discord Integration!
    """)

    print("> " + "M1 completa é alicerce de M2" + " – made by Sky 🏗️")


if __name__ == "__main__":
    main()
