"""
WebUI App — Thin adapter para interface web.

Ponto de entrada da aplicação Skybridge WebUI (Dashboard).
Executa o Vite dev server em processo independente.
"""

import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from runtime.config.config import get_config
from runtime.observability.logger import get_logger, print_banner, Colors
from version import __version__


def main():
    """Ponto de entrada do WebUI."""
    config = get_config()

    # Logger dedicado com prefixo [WEBUI]
    logger = get_logger(level="DEBUG")  # Sempre DEBUG em desenvolvimento

    # Banner específico
    print_banner("Skybridge WebUI", __version__)
    print()
    logger.info(f"Iniciando {Colors.WHITE}WebUI{Colors.RESET} em modo DEBUG")
    logger.info(f"WebUI URL: {Colors.CYAN}http://localhost:5173/web/{Colors.RESET}")
    logger.info(f"API URL: {Colors.CYAN}http://{config.host}:{config.port}{Colors.RESET}")
    print()

    # Executa Vite dev server
    frontend_dir = Path(__file__).parent
    vite_cmd = "npm run dev"

    logger.debug(f"Executando Vite: {vite_cmd}", extra={
        "cwd": str(frontend_dir),
        "port": 5173
    })

    try:
        # No Windows, usa shell=True para encontrar npm no PATH
        # check=False para não lançar exceção em códigos de saída != 0
        result = subprocess.run(vite_cmd, cwd=frontend_dir, shell=True, check=False)
        # Exit code 143 (SIGTERM) é normal quando encerrado por timeout/externo
        if result.returncode not in (0, 143):
            logger.error(f"Vite terminou com código inesperado: {result.returncode}")
    except KeyboardInterrupt:
        logger.info(f"{Colors.WHITE}WebUI{Colors.RESET} encerrado pelo usuário")


if __name__ == "__main__":
    main()
