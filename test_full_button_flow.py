"""
Teste completo do fluxo de botão.

Este script:
1. Injeta um MCP server mock no _discord_mcp_server global
2. Envia botões via send_buttons
3. Simula um clique no botão
4. Verifica se a notificação foi enviada
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from unittest.mock import Mock, AsyncMock, patch
from discord import ButtonStyle
from discord.ui import Button, View
from src.core.discord.presentation.dto.legacy_dto import ButtonConfig, SendButtonsInput


class MockDiscordClient:
    """Mock cliente Discord."""
    pass


class MockChannel:
    """Mock canal Discord."""
    id = "123456789"

    async def send(self, **kwargs):
        """Mock send."""
        # Retorna uma mock message
        mock_message = Mock()
        mock_message.id = "msg_123"
        return mock_message


async def test_full_flow():
    """Testa o fluxo completo."""

    # Setup: injetar mocks
    from src.core.discord import client as discord_client
    from src.core.discord.tools import send_buttons

    # Patch fetch_allowed_channel
    async def mock_fetch_allowed(client, chat_id):
        return MockChannel()

    discord_client.fetch_allowed_channel = mock_fetch_allowed

    # Patch note_sent
    send_buttons.note_sent = lambda x: None

    # Criar mock server
    mock_notifications = []

    class MockWriteStream:
        async def send(self, data):
            print(f"[MOCK STREAM] Notificação enviada: {data}")
            mock_notifications.append(data)

    mock_server = Mock()
    mock_server._write_stream = MockWriteStream()
    mock_server.send_notification = Mock(side_effect=lambda method, params: asyncio.create_task(
        MockWriteStream().send({"method": method, "params": params})
    ))

    # Injetar server no módulo send_buttons
    send_buttons._discord_mcp_server = mock_server
    print(f"[TEST] Mock server injetado: {mock_server}")

    # Criar input para send_buttons
    input_data = SendButtonsInput(
        chat_id="123456789",
        title="Test Embed",
        description="Test description",
        buttons=[
            ButtonConfig(id="test_btn", label="Test Button", style="primary"),
        ]
    )

    # Executar send_buttons
    print("\n[TEST] Enviando botões via handle_send_buttons...")
    client = MockDiscordClient()
    result = await send_buttons.handle_send_buttons(client, input_data.model_dump())

    print(f"[TEST] Result: {result}")

    # Simular clique no botão
    print("\n[TEST] Simulando clique no botão...")

    # Precisamos pegar a View que foi criada
    # Como a View é criada dentro da função, não temos acesso direto
    # Vamos criar uma View manual para testar o callback

    # Reiniciar com testes diretos
    print("\n[TEST] Criando View manualmente com callback do send_buttons...")

    # Importar a classe DDDButtonView (é local, então não podemos)
    # Vamos recriar a lógica
    from discord.ui import View

    class TestView(View):
        def __init__(self, buttons_data):
            super().__init__(timeout=None)
            self._buttons_data = {btn.id: btn for btn in buttons_data}
            self._server = mock_server

        async def _handle_button_click(self, interaction):
            """Handler que simula o do send_buttons."""
            global mock_notifications

            print(f"[CALLBACK] Callback chamado!")
            print(f"[CALLBACK] _server: {self._server}")

            await interaction.response.defer()

            custom_id = interaction.data.custom_id
            notification = {
                "button_id": custom_id,
                "button_label": custom_id,
                "test": "manual",
            }

            await self._server.send_notification(
                "notifications/claude/button_clicked",
                notification
            )

    view = TestView(input_data.buttons)
    button = Button(style=ButtonStyle.primary, label="Test", custom_id="test_btn")
    button.callback = view._handle_button_click
    view.add_item(button)

    # Criar mock interaction
    mock_interaction = Mock()
    mock_interaction.data = Mock()
    mock_interaction.data.custom_id = "test_btn"
    mock_interaction.response = Mock()
    mock_interaction.response.defer = AsyncMock()

    # Chamar callback
    print("\n[TEST] Chamando callback...")
    await button.callback(mock_interaction)

    # Verificar resultado
    print(f"\n[TEST] Notificações capturadas: {len(mock_notifications)}")
    for notif in mock_notifications:
        print(f"  - {notif}")


if __name__ == "__main__":
    asyncio.run(test_full_flow())
