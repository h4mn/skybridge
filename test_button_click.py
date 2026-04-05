"""
Teste automatizado para debug de clique de botão Discord MCP.

Objetivo: Simular clique e verificar se notificação chega.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from discord import ButtonStyle
from discord.ui import Button, View


async def test_view_callback():
    """Testa se callback de View funciona corretamente."""

    # Track if callback was called
    callback_called = False
    callback_data = {}

    class TestView(View):
        async def button_clicked(self, interaction):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = {
                "custom_id": interaction.data.custom_id if interaction.data else None,
                "user": interaction.user.name if interaction.user else None,
            }
            print(f"[TEST] Callback chamado! custom_id={callback_data['custom_id']}")
            await interaction.response.defer()

    view = TestView(timeout=None)

    # Create button
    button = Button(style=ButtonStyle.primary, label="Test Button", custom_id="test_btn")
    button.callback = view.button_clicked
    view.add_item(button)

    # Find the button in the view
    print(f"[TEST] View criada com {len(view.children)} itens")
    for item in view.children:
        print(f"[TEST] Item: {item.type} - custom_id={item.custom_id}")
        print(f"[TEST] Callback definido? {item.callback is not None}")
        print(f"[TEST] Callback: {item.callback}")

    # Simulate Discord calling the callback
    # We need to create a mock interaction
    print("\n[TEST] Criando mock interaction...")

    from unittest.mock import Mock, AsyncMock
    mock_interaction = Mock()
    mock_interaction.data = Mock()
    mock_interaction.data.custom_id = "test_btn"
    mock_interaction.user = Mock()
    mock_interaction.user.name = "TestUser"
    mock_interaction.response = Mock()
    mock_interaction.response.defer = AsyncMock()

    # Call the callback directly
    print("\n[TEST] Chamando callback diretamente...")
    try:
        await button.callback(mock_interaction)
        print(f"[TEST] Callback executado com sucesso!")
        print(f"[TEST] callback_called={callback_called}")
        print(f"[TEST] callback_data={callback_data}")
    except Exception as e:
        print(f"[TEST] ERRO no callback: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_view_callback())
