# -*- coding: utf-8 -*-
"""
Demonstrações de Integração Paper ↔ Discord.

Exemplos de como o Paper Trading notifica via Discord DDD.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from ...application.commands import SendEmbedCommand, SendButtonsCommand
from ...application.handlers import SendEmbedHandler, SendButtonsHandler
from ...domain.repositories import ChannelRepository


async def demo_portfolio_notification():
    """
    Demonstração: Notificação de Portfolio do Paper.

    Quando um portfolio é atualizado, envia notificação via Discord.
    """
    print("[DEMO] Integration: Portfolio Notification")
    print("-" * 60)
    print("CENARIO: Portfolio atualizado no Paper Trading")
    print()

    # Setup - mock do Discord
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock()
    mock_message_repo.save = AsyncMock()

    mock_event_publisher = AsyncMock()

    handler = SendEmbedHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
        event_publisher=mock_event_publisher,
    )

    # Simular dados do portfolio
    portfolio_data = {
        "saldo": 50000.00,
        "pnl": 3500.00,
        "pnl_percent": 7.5,
        "posicoes": [
            {"ticker": "PETR4", "qtd": 100, "preco_medio": 35.00, "atual": 38.50},
            {"ticker": "VALE3", "qtd": 200, "preco_medio": 68.00, "atual": 72.30},
        ],
    }

    # Calcular cor baseada em PnL
    cor = "verde" if portfolio_data["pnl"] >= 0 else "vermelho"

    # Criar embed de notificação
    command = SendEmbedCommand.create(
        channel_id="123456789",
        title=f"Portfolio Atualizado",
        description=f"Seu portfolio foi atualizado com novos precos.",
        color=cor,
        fields=[
            {"name": "Saldo", "value": f"R$ {portfolio_data['saldo']:,.2f}"},
            {"name": "PnL", "value": f"R$ {portfolio_data['pnl']:,.2f} ({portfolio_data['pnl_percent']:+.1f}%)"},
            {"name": "Posicoes", "value": f"{len(portfolio_data['posicoes'])} ativos"},
        ],
        footer="Paper Trading via Discord DDD",
    )

    result = await handler.handle(command)

    print("[OK] Notificacao enviada ao Discord!")
    print(f"   Embed: {command.embed.title}")
    print(f"   Cor: {cor} (PnL positivo)")
    print(f"   Message ID: {result.message_id}")
    print()


async def demo_ordem_confirmation():
    """
    Demonstração: Confirmação de Ordem do Paper.

    Quando uma ordem é iniciada, envia botões de confirmação.
    """
    print("[DEMO] Integration: Ordem Confirmation")
    print("-" * 60)
    print("CENARIO: Usuario iniciou ordem de compra")
    print()

    # Setup
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock()
    mock_message_repo.save = AsyncMock()

    mock_event_publisher = AsyncMock()

    handler = SendButtonsHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
        event_publisher=mock_event_publisher,
    )

    # Dados da ordem
    ordem = {
        "ticker": "PETR4",
        "lado": "COMPRA",
        "qtd": 100,
        "preco": 38.50,
        "total": 3850.00,
    }

    # Criar botões de confirmação
    command = SendButtonsCommand.create(
        channel_id="123456789",
        text=f"Confirmar ordem: {ordem['lado']} {ordem['qtd']}x {ordem['ticker']} @ R$ {ordem['preco']}",
        buttons=[
            {"id": "ordem_confirm", "label": "[OK] Confirmar", "style": "success"},
            {"id": "ordem_cancel", "label": "[X] Cancelar", "style": "danger"},
        ],
    )

    result = await handler.handle(command)

    print("[OK] Botões de confirmacao enviados!")
    print(f"   Ordem: {ordem['lado']} {ordem['qtd']}x {ordem['ticker']}")
    print(f"   Valor total: R$ {ordem['total']:,.2f}")
    print(f"   Message ID: {result.message_id}")
    print()


async def demo_ordem_executed():
    """
    Demonstração: Ordem Executada.

    Quando uma ordem é executada, envia notificação de sucesso.
    """
    print("[DEMO] Integration: Ordem Executada")
    print("-" * 60)
    print("CENARIO: Ordem executada com sucesso")
    print()

    # Setup
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock()
    mock_message_repo.save = AsyncMock()

    mock_event_publisher = AsyncMock()

    handler = SendEmbedHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
        event_publisher=mock_event_publisher,
    )

    # Dados da ordem executada
    ordem = {
        "ticker": "PETR4",
        "lado": "COMPRA",
        "qtd": 100,
        "preco": 38.50,
        "total": 3850.00,
    }

    command = SendEmbedCommand.create(
        channel_id="123456789",
        title="[OK] Ordem Executada",
        description=f"Ordem de {ordem['lado']} executada com sucesso.",
        color="verde",
        fields=[
            {"name": "Ativo", "value": ordem["ticker"]},
            {"name": "Quantidade", "value": str(ordem["qtd"])},
            {"name": "Preco", "value": f"R$ {ordem['preco']:.2f}"},
            {"name": "Total", "value": f"R$ {ordem['total']:,.2f}"},
        ],
        footer=f"ID: {ordem['ticker']}-{ordem['lado']}-{ordem['qtd']}@{ordem['preco']}",
    )

    result = await handler.handle(command)

    print("[OK] Notificacao de execucao enviada!")
    print(f"   Ordem: {ordem['lado']} {ordem['qtd']}x {ordem['ticker']}")
    print(f"   Status: EXECUTADA")
    print()


async def demo_risk_alert():
    """
    Demonstração: Alerta de Risco.

    Quando um limite de risco é atingido, envia alerta.
    """
    print("[DEMO] Integration: Risk Alert")
    print("-" * 60)
    print("CENARIO: Limite de risco atingido")
    print()

    # Setup
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock()
    mock_message_repo.save = AsyncMock()

    mock_event_publisher = AsyncMock()

    handler = SendEmbedHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
        event_publisher=mock_event_publisher,
    )

    # Dados do alerta
    alerta = {
        "tipo": "PERDA_MAXIMA_DIA",
        "perda_percent": -5.2,
        "perda_valor": -2500.00,
        "limite": -5.0,
    }

    command = SendEmbedCommand.create(
        channel_id="123456789",
        title="[!] ALERTA DE RISCO",
        description=f"Limite de perda maxima diaria atingido.",
        color="vermelho",
        fields=[
            {"name": "Tipo", "value": alerta["tipo"]},
            {"name": "Perda Dia", "value": f"{alerta['perda_percent']:.1f}%"},
            {"name": "Valor", "value": f"R$ {alerta['perda_valor']:,.2f}"},
            {"name": "Limite", "value": f"{alerta['limite']:.1f}%"},
        ],
        footer="Sistema de Gestao de Riscos",
    )

    result = await handler.handle(command)

    print("[OK] Alerta de risco enviado!")
    print(f"   Tipo: {alerta['tipo']}")
    print(f"   Perda: {alerta['perda_percent']:.1f}%")
    print(f"   Cor: vermelho (alerta)")
    print()


async def run_integration_demos():
    """
    Executa todas as demonstracoes de integracao.
    """
    print("\n" + "=" * 60)
    print("DISCORD DDD - INTEGRATION DEMONSTRATIONS")
    print("Paper Trading <-> Discord")
    print("=" * 60)
    print()

    await demo_portfolio_notification()
    await demo_ordem_confirmation()
    await demo_ordem_executed()
    await demo_risk_alert()

    print("=" * 60)
    print("TODAS AS DEMONSTRACOES DE INTEGRACAO CONCLUIDAS!")
    print("=" * 60)
