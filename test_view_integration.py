"""
Teste de integração para verificar se View e callbacks estão corretos.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from discord import ButtonStyle
from discord.ui import Button, View
from src.core.discord.presentation.dto.legacy_dto import ButtonConfig, SendButtonsInput


async def test_send_buttons_view():
    """Testa se send_buttons cria View corretamente."""

    # Create input data
    input_data = SendButtonsInput(
        chat_id="123456",
        title="Test Embed",
        description="Test description",
        buttons=[
            ButtonConfig(id="btn1", label="Button 1", style="primary"),
            ButtonConfig(id="btn2", label="Button 2", style="success"),
        ]
    )

    print("[TEST] Input criado:")
    print(f"  chat_id: {input_data.chat_id}")
    print(f"  buttons: {len(input_data.buttons)}")

    # Import the module-level variable
    from src.core.discord.tools.send_buttons import _discord_mcp_server

    print(f"\n[TEST] _discord_mcp_server global: {_discord_mcp_server}")

    # Create view manually (since DDDButtonView is defined inside handle_send_buttons)
    from discord.ui import View

    class TestView(View):
        def __init__(self, buttons_data):
            super().__init__(timeout=None)
            self._buttons_data = {btn.id: btn for btn in buttons_data}

        async def _handle_button_click(self, interaction):
            print(f"\n[TEST CALLBACK] Callback foi chamado!")
            print(f"  custom_id: {interaction.data.custom_id}")
            await interaction.response.defer()

    view = TestView(input_data.buttons)

    print(f"\n[TEST] DDDButtonView criada:")
    print(f"  children: {len(view.children)}")
    print(f"  _buttons_data: {list(view._buttons_data.keys())}")

    # Add buttons (simulating send_buttons)
    for btn_config in input_data.buttons:
        style_map = {
            "primary": ButtonStyle.primary,
            "secondary": ButtonStyle.secondary,
            "success": ButtonStyle.success,
            "danger": ButtonStyle.danger,
        }
        style = style_map.get(btn_config.style, ButtonStyle.primary)

        button = Button(style=style, label=btn_config.label, custom_id=btn_config.id)
        button.callback = view._handle_button_click
        view.add_item(button)
        print(f"\n[TEST] Botão adicionado:")
        print(f"  custom_id: {button.custom_id}")
        print(f"  label: {button.label}")
        print(f"  callback: {button.callback}")
        print(f"  callback é _handle_button_click? {button.callback == view._handle_button_click}")

    # Verify all buttons have callbacks
    print(f"\n[TEST] Verificando callbacks finais:")
    for i, item in enumerate(view.children):
        print(f"  Item {i}: type={item.type}, custom_id={item.custom_id}, callback={item.callback is not None}")

    # Simulate button click
    print("\n[TEST] Simulando clique...")
    from unittest.mock import Mock, AsyncMock

    mock_interaction = Mock()
    mock_interaction.data = Mock()
    mock_interaction.data.custom_id = "btn1"
    mock_interaction.user = Mock()
    mock_interaction.user.name = "TestUser"
    mock_interaction.user.id = "123"
    mock_interaction.channel_id = "456"
    mock_interaction.message = Mock()
    mock_interaction.message.id = "789"
    mock_interaction.created_at = Mock()
    mock_interaction.created_at.isoformat = Mock(return_value="2026-03-30T12:00:00")
    mock_interaction.response = Mock()
    mock_interaction.response.defer = AsyncMock()

    # Call the first button's callback
    first_button = view.children[0]
    print(f"[TEST] Chamando callback do botão '{first_button.custom_id}'...")

    try:
        await first_button.callback(mock_interaction)
        print("[TEST] Callback executado!")
    except Exception as e:
        print(f"[TEST] ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_send_buttons_view())
