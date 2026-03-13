# coding: utf-8
"""
Script de inicialização do Sky Chat com bootstrap.

Orquestra o carregamento com barra de progresso visual.
"""

import os
import sys
import io
from pathlib import Path

# ========== CONFIGURAÇÃO UTF-8 ==========
# Forçar UTF-8 no stdout para emojis e acentos no Windows
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'
# ========================================

# Adiciona src ao path
project_root = Path(__file__).parent.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

# Configura variáveis de ambiente (antes de qualquer import do Sky)
os.environ["USE_RAG_MEMORY"] = "true"
os.environ["USE_CLAUDE_CHAT"] = "true"
os.environ["USE_TEXTUAL_UI"] = "true"

# Carrega .env se existir
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


def main():
    """Ponto de entrada principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Sky Chat com bootstrap")
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Pular barra de progresso (modo original)"
    )

    # Passa através argumentos desconhecidos para SkyApp
    args, unknown = parser.parse_known_args()

    if args.no_bootstrap or "--no-bootstrap" in unknown:
        # Modo bypass: carrega SkyApp diretamente
        from core.sky.chat.textual_ui import SkyApp
        app = SkyApp()
        app.run()
    else:
        # Modo com bootstrap
        from core.sky.bootstrap import run

        try:
            app = run()
            app.run()
        except KeyboardInterrupt:
            from rich.console import Console
            console = Console()
            console.print("\n[yellow]Bootstrap cancelado pelo usuário.[/yellow]")
            sys.exit(130)


if __name__ == "__main__":
    main()
