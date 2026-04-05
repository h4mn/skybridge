"""
Demo: EventBus Publish/Subscribe

Mostra como usar o sistema de eventos de domínio.
"""

import asyncio
import sys
from datetime import datetime

from src.core.paper.domain.events import (
    EventBus,
    OrdemCriada,
    OrdemExecutada,
    PosicaoAtualizada,
    Lado,
)


def main():
    """Executa demo do EventBus."""
    # Força UTF-8 no Windows
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

    print("=" * 60)
    print("📡 Demo: EventBus Publish/Subscribe")
    print("=" * 60)

    # Criar EventBus
    bus = EventBus()

    # === Handler 1: Logger de ordens ===
    def log_ordem(event: OrdemCriada):
        print(f"📝 [LOGGER] Ordem {event.ordem_id} criada:")
        print(f"   Ticker: {event.ticker}")
        print(f"   Lado: {event.lado}")
        print(f"   Qtd: {event.quantidade}")
        print(f"   Timestamp: {event.occurred_at.strftime('%H:%M:%S')}")

    # === Handler 2: Calculador de risco ===
    def calcular_risco(event: OrdemCriada):
        if event.lado == "compra":
            risco = event.quantidade * 0.01  # 1% da quantidade
            print(f"⚠️  [RISCO] Ordem {event.ordem_id} - Risco calculado: {risco}")

    # === Handler 3: Notificador Discord ===
    def notificar_discord(event: OrdemCriada):
        print(f"📢 [DISCORD] Notificação enviada: Nova ordem {event.ordem_id}")

    # Inscrever handlers
    bus.subscribe(OrdemCriada, log_ordem)
    bus.subscribe(OrdemCriada, calcular_risco)
    bus.subscribe(OrdemCriada, notificar_discord)

    print("\n✅ 3 Handlers inscritos para 'OrdemCriada'\n")

    # === Publicar eventos ===
    print("-" * 60)
    print("🚀 Publicando eventos...\n")

    # Evento 1: Compra PETR4
    evento1 = OrdemCriada(
        ordem_id="ordem-001",
        ticker="PETR4.SA",
        lado=Lado.COMPRA,
        quantidade=100,
        preco_limit=25.50,
    )
    bus.publish(evento1)

    print("\n" + "-" * 60 + "\n")

    # Evento 2: Venda BTC
    evento2 = OrdemCriada(
        ordem_id="ordem-002",
        ticker="BTC-USD",
        lado=Lado.VENDA,
        quantidade=1,
    )
    bus.publish(evento2)

    print("\n" + "=" * 60)
    print("✅ Demo concluída!")
    print("=" * 60)


if __name__ == "__main__":
    main()
