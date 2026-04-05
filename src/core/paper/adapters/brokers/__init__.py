"""
Brokers Adapters - Paper Trading
Implementações concretas em BrokerPort para diferentes brokers.
Adapters planejados:
- PaperBroker: Simula execução de ordens (sem broker real)
- BinanceAdapter: Integração com Binance
- XPAdapter: Integração com XP Investimentos
- ClearAdapter: Integração com Clear Corretora
Exemplo de uso:
    from src.core.paper.adapters.brokers import PaperBroker
    broker = PaperBroker()
    await broker.conectar()
    ordem_id = await broker.enviar_ordem("PETR4", "COMPRA", 100)
"""
from .paper_broker import PaperBroker, SaldoInsuficienteError, OrdemNaoEncontradaError
from .json_file_broker import JsonFilePaperBroker
__all__ = [
    "PaperBroker",
    "JsonFilePaperBroker",
    "SaldoInsuficienteError",
    "OrdemNaoEncontradaError",
]
