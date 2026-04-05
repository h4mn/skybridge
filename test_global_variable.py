"""
Teste se variável global é lida dinamicamente no callback.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from discord import ButtonStyle
from discord.ui import Button, View


# Variável global (simulando _discord_mcp_server)
_global_server = None


class TestView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_click(self, interaction):
        global _global_server
        print(f"[CALLBACK] _global_server no momento do clique: {_global_server}")
        await interaction.response.defer()


async def test_global_closure():
    """Testa se callback lê variável global dinamicamente."""
    global _global_server

    print("[TEST] Início - _global_server =", _global_server)

    # Create view e botão
    view = TestView()
    button = Button(style=ButtonStyle.primary, label="Test", custom_id="test")
    button.callback = view.handle_click
    view.add_item(button)

    print("[TEST] View criada - _global_server ainda =", _global_server)

    # Mudar a variável global
    print("\n[TEST] Mudando _global_server para 'SERVER_OBJECT'...")
    _global_server = "SERVER_OBJECT"
    print("[TEST] _global_server agora =", _global_server)

    # Simular clique
    print("\n[TEST] Simulando clique...")
    from unittest.mock import Mock, AsyncMock
    mock_interaction = Mock()
    mock_interaction.response = Mock()
    mock_interaction.response.defer = AsyncMock()

    await button.callback(mock_interaction)

    print("\n[TEST] Se o callback imprimir 'SERVER_OBJECT', a leitura é dinâmica!")


if __name__ == "__main__":
    asyncio.run(test_global_closure())
