"""
Teste se send_notification do DiscordMCPServer funciona.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_mcp_server_send_notification():
    """Testa se o método send_notification funciona."""

    # Import server
    from src.core.discord.server import DiscordMCPServer

    # Create server instance
    server = DiscordMCPServer()

    print("[TEST] DiscordMCPServer criado")
    print(f"[TEST] _write_stream inicial: {server._write_stream}")

    # Test send_notification without write_stream
    print("\n[TEST] Testando send_notification SEM write_stream...")
    await server.send_notification("test/method", {"test": "data"})

    # Mock write_stream
    from unittest.mock import Mock, AsyncMock

    mock_stream = Mock()
    mock_stream.send = AsyncMock()

    server._write_stream = mock_stream
    print(f"[TEST] _write_stream definido: {server._write_stream}")

    # Test send_notification with write_stream
    print("\n[TEST] Testando send_notification COM write_stream...")
    await server.send_notification("notifications/claude/button_clicked", {"button_id": "test"})

    # Check if send was called
    if mock_stream.send.called:
        print(f"[TEST] ✅ mock_stream.send foi chamado!")
        print(f"[TEST] Chamadas: {mock_stream.send.call_count}")
        for call in mock_stream.send.call_args_list:
            print(f"[TEST]   Argumentos: {call}")
    else:
        print(f"[TEST] ❌ mock_stream.send NÃO foi chamado!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server_send_notification())
