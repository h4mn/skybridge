#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo Visual: PortfolioUIHandler e OrdemUIHandler.

Mostra exemplos práticos de uso dos handlers da Integration Layer.
"""
import asyncio
import sys
import io
from decimal import Decimal

# Força UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.core.integrations.discord_paper.handlers.portfolio_ui_handler import PortfolioUIHandler
from src.core.integrations.discord_paper.handlers.ordem_ui_handler import OrdemUIHandler


# Mock DiscordService para demo
class MockDiscordService:
    """Mock que mostra o que seria enviado ao Discord."""

    def __init__(self):
        self.messages = []

    async def send_embed(self, channel_id, title, color=None, description="", fields=None, **kwargs):
        """Mock send_embed."""
        msg = {
            "type": "embed",
            "channel_id": channel_id,
            "title": title,
            "color": color,
            "description": description,
            "fields": fields or []
        }
        self.messages.append(msg)
        print(f"\n{'='*60}")
        print(f"📨 EMBED ENVIADO PARA #{channel_id}")
        print(f"{'='*60}")
        print(f"Título: {title}")
        if description:
            print(f"Descrição: {description}")
        if color:
            emoji = "🟢" if color == 3066993 else "🔴" if color == 15158332 else "🔵"
            print(f"Cor: {emoji} {color}")
        if fields:
            print(f"Campos:")
            for f in fields:
                print(f"  • {f['name']}: {f['value']}")
        print(f"{'='*60}\n")

        class MockMsg:
            id = "msg_" + str(len(self.messages))

        return MockMsg()

    async def send_buttons(self, channel_id, title, buttons, description="", embed_data=None, **kwargs):
        """Mock send_buttons."""
        msg = {
            "type": "buttons",
            "channel_id": channel_id,
            "title": title,
            "description": description,
            "buttons": [b.label for b in buttons],
            "embed_data": embed_data
        }
        self.messages.append(msg)
        print(f"\n{'='*60}")
        print(f"🎮 BOTÕES ENVIADOS PARA #{channel_id}")
        print(f"{'='*60}")
        print(f"Título: {title}")
        if description:
            print(f"Descrição: {description}")
        if embed_data and embed_data.get("fields"):
            print(f"Info:")
            for f in embed_data["fields"]:
                print(f"  • {f['name']}: {f['value']}")
        print(f"Botões:")
        for b in buttons:
            print(f"  [{b.style.upper()}] {b.label} (id: {b.custom_id})")
        print(f"{'='*60}\n")

        class MockMsg:
            id = "msg_" + str(len(self.messages))

        return MockMsg()

    async def send_message(self, channel_id, content, **kwargs):
        """Mock send_message."""
        msg = {
            "type": "message",
            "channel_id": channel_id,
            "content": content
        }
        self.messages.append(msg)
        print(f"\n{'='*60}")
        print(f"💬 MENSAGEM ENVIADA PARA #{channel_id}")
        print(f"{'='*60}")
        print(f"{content}")
        print(f"{'='*60}\n")

    async def send_progress(self, channel_id, title, current, total, status, tracking_id=None, **kwargs):
        """Mock send_progress."""
        print(f"\n{'='*60}")
        print(f"⏳ PROGRESSO: {current}/{total} - {status}")
        print(f"{'='*60}")
        print(f"Tracking ID: {tracking_id}")
        print(f"{'='*60}\n")

    async def edit_message(self, channel_id, message_id, content=None, **kwargs):
        """Mock edit_message."""
        print(f"\n{'='*60}")
        print(f"✏️  MENSAGEM EDITADA: {message_id}")
        print(f"{'='*60}")
        if content:
            print(f"Novo conteúdo: {content}")
        print(f"{'='*60}\n")


async def demo_portfolio_ui_handler():
    """
    Demo 1: PortfolioUIHandler.

    Cenário: Usuário solicita visualização do portfolio.
    """
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  📊 DEMO 1: PortfolioUIHandler".center(56) + "  █")
    print("█" + " "*58 + "█")
    print("█"*60 + "\n")

    # Setup
    mock_discord = MockDiscordService()
    handler = PortfolioUIHandler(discord_service=mock_discord)

    # Cenário 1: Portfolio com lucro
    print("\n📈 CENÁRIO 1: Portfolio com lucro (P&L +15.5%)")
    print("-" * 60)

    await handler.send_portfolio_embed(
        channel_id="1487929503073173727",
        balance_btc=1.5,
        balance_usd=50000.0,
        positions=[
            {"symbol": "BTC", "quantity": 0.5, "avg_price": 45000},
            {"symbol": "ETH", "quantity": 5.0, "avg_price": 2800}
        ],
        pnl_percent=15.5
    )

    # Cenário 2: Portfolio com prejuízo
    print("\n📉 CENÁRIO 2: Portfolio com prejuízo (P&L -5.0%)")
    print("-" * 60)

    await handler.send_portfolio_embed(
        channel_id="1487929503073173727",
        balance_btc=1.0,
        balance_usd=45000.0,
        positions=[],
        pnl_percent=-5.0
    )

    # Cenário 3: Menu de opções (com posições)
    print("\n🎯 CENÁRIO 3: Menu de opções (com posições abertas)")
    print("-" * 60)

    await handler.send_portfolio_menu(
        channel_id="1487929503073173727",
        has_positions=True
    )

    # Cenário 4: Menu de opções (sem posições)
    print("\n🎯 CENÁRIO 4: Menu de opções (sem posições)")
    print("-" * 60)

    await handler.send_portfolio_menu(
        channel_id="1487929503073173727",
        has_positions=False
    )

    # Cenário 5: Barra de progresso
    print("\n⏳ CENÁRIO 5: Barra de progresso (atualizando portfolio)")
    print("-" * 60)

    await handler.update_portfolio_progress(
        channel_id="1487929503073173727",
        tracking_id="portfolio_update_001",
        current=25,
        total=100,
        status="Buscando cotações..."
    )

    await handler.update_portfolio_progress(
        channel_id="1487929503073173727",
        tracking_id="portfolio_update_001",
        current=75,
        total=100,
        status="Calculando P&L..."
    )

    # Cenário 6: Handler de seleções
    print("\n🔄 CENÁRIO 6: Usuário seleciona opção do menu")
    print("-" * 60)

    print("\nUsuário clica em '📊 Resumo'")
    await handler.handle_portfolio_selection(
        selection="portfolio_summary",
        channel_id="1487929503073173727"
    )

    print("\nUsuário clica em '📋 Posições'")
    await handler.handle_portfolio_selection(
        selection="portfolio_positions",
        channel_id="1487929503073173727"
    )


async def demo_ordem_ui_handler():
    """
    Demo 2: OrdemUIHandler.

    Cenário: Usuário cria ordem de compra.
    """
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  💰 DEMO 2: OrdemUIHandler".center(56) + "  █")
    print("█" + " "*58 + "█")
    print("█"*60 + "\n")

    # Setup
    mock_discord = MockDiscordService()
    handler = OrdemUIHandler(discord_service=mock_discord)

    # Cenário 1: Confirmação de ordem limitada
    print("\n📋 CENÁRIO 1: Confirmação de ordem limitada")
    print("-" * 60)

    await handler.send_ordem_confirmacao(
        channel_id="1487929503073173727",
        symbol="BTCUSD",
        side="buy",
        quantity=0.5,
        price=50000.0,
        order_id="ord_001"
    )

    # Verifica ordem pendente
    pending = handler.get_pending_confirmation("ord_001")
    print(f"\n✅ Ordem pendente armazenada:")
    print(f"   • Symbol: {pending['symbol']}")
    print(f"   • Side: {pending['side']}")
    print(f"   • Quantity: {pending['quantity']}")
    print(f"   • Price: ${pending['price']:,.2f}")

    # Cenário 2: Confirmação de ordem a mercado
    print("\n📋 CENÁRIO 2: Confirmação de ordem a mercado")
    print("-" * 60)

    await handler.send_ordem_confirmacao(
        channel_id="1487929503073173727",
        symbol="ETHUSD",
        side="sell",
        quantity=2.0,
        price=None,  # Ordem a mercado
        order_id="ord_002"
    )

    # Cenário 3: Usuário confirma ordem
    print("\n✅ CENÁRIO 3: Usuário confirma ordem")
    print("-" * 60)

    await handler.handle_ordem_confirmation(
        custom_id="confirm_order_ord_001",
        confirmed=True
    )

    # Verifica que pendente foi removido
    pending_after = handler.get_pending_confirmation("ord_001")
    print(f"\n✅ Pendente removido após confirmação: {pending_after is None}")

    # Cenário 4: Usuário cancela ordem
    print("\n❌ CENÁRIO 4: Usuário clica em cancelar")
    print("-" * 60)

    await handler.handle_ordem_confirmation(
        custom_id="cancel_order_ord_002",
        confirmed=False
    )

    # Cenário 5: Ordem executada
    print("\n🎯 CENÁRIO 5: Ordem executada (bypass confirmation)")
    print("-" * 60)

    await handler.send_ordem_executada(
        channel_id="1487929503073173727",
        symbol="BTCUSD",
        side="buy",
        quantity=0.5,
        price=49850.0,
        order_id="ord_003"
    )

    # Cenário 6: Ordem cancelada (externamente)
    print("\n⚠️  CENÁRIO 6: Ordem cancelada pelo sistema")
    print("-" * 60)

    await handler.send_ordem_cancelada(
        channel_id="1487929503073173727",
        order_id="ord_004",
        reason="Saldo insuficiente"
    )

    # Cenário 7: Custom ID inválido
    print("\n⚠️  CENÁRIO 7: Custom ID inválido (error handling)")
    print("-" * 60)

    await handler.handle_ordem_confirmation(
        custom_id="invalid_id",
        confirmed=True
    )

    print("✅ Nenhum erro - custom_id inválido é ignorado com grace")


async def main():
    """Executa todos os demos."""
    print("\n" + "="*60)
    print("  INTEGRATION LAYER - DEMO VISUAL".center(60))
    print("  PortfolioUIHandler + OrdemUIHandler".center(60))
    print("="*60)

    await demo_portfolio_ui_handler()
    await demo_ordem_ui_handler()

    print("\n" + "="*60)
    print("  ✅ DEMO COMPLETO".center(60))
    print("="*60)
    print("\n📖 RESUMO:")
    print("  • PortfolioUIHandler: UI completa de portfolio")
    print("    - Embed com saldos e P&L")
    print("    - Menu de opções")
    print("    - Barra de progresso")
    print("    - Roteamento de seleções")
    print()
    print("  • OrdemUIHandler: UI completa de ordens")
    print("    - Confirmação de ordens (limitada/mercado)")
    print("    - Notificação de execução")
    print("    - Notificação de cancelamento")
    print("    - Armazenamento de pendentes")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
