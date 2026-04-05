"""
Teste simplificado: apenas o callback do botão com mock MCP server.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from unittest.mock import Mock, AsyncMock
from discord import ButtonStyle
from discord.ui import Button, View


async def test_callback_with_server():
    """Testa callback com mock MCP server."""

    # Variável global simulada
    global_server = None

    # Mock write stream
    notifications = []

    class MockStream:
        async def send(self, data):
            notifications.append(data)
            print(f"[STREAM] Notificação enviada: {data}")

    # Setup callback
    class TestView(View):
        async def handle_click(self, interaction):
            print("\n[CALLBACK] === CALLBACK FOI CHAMADO! ===")
            print(f"[CALLBACK] global_server: {global_server}")

            await interaction.response.defer()

            if global_server:
                print(f"[CALLBACK] Enviando notificação...")
                await global_server.send_notification("test/event", {"test": "data"})
            else:
                print("[CALLBACK] ❌ global_server é None!")

    # Create view e button
    view = TestView(timeout=None)
    button = Button(style=ButtonStyle.primary, label="Test", custom_id="test")
    button.callback = view.handle_click
    view.add_item(button)

    print("[TEST] View criada, callback definido")
    print(f"[TEST] global_server inicial: {global_server}")

    # Create mock server
    mock_server = Mock()
    mock_stream = MockStream()
    mock_server._write_stream = mock_stream
    mock_server.send_notification = Mock(side_effect=lambda m, p: mock_stream.send({"method": m, "params": p}))

    # Update global (simulando set_mcp_server)
    print("\n[TEST] Definindo global_server...")
    global_server = mock_server
    print(f"[TEST] global_server agora: {global_server}")

    # Simulate click
    print("\n[TEST] Simulando clique...")
    mock_interaction = Mock()
    mock_interaction.response = Mock()
    mock_interaction.response.defer = AsyncMock()

    await button.callback(mock_interaction)

    print(f"\n[TEST] Notificações: {len(notifications)}")
    for n in notifications:
        print(f"  - {n}")

    if len(notifications) > 0:
        print("\n[TEST] ✅ SUCESSO! Notificação foi enviada!")
    else:
        print("\n[TEST] ❌ FALHOU! Nenhuma notificação enviada.")


if __name__ == "__main__":
    asyncio.run(test_callback_with_server())
