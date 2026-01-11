"""
API App — Thin adapter para interface HTTP.

Ponto de entrada da aplicação Skybridge API.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from skybridge.platform.bootstrap.app import get_app
from skybridge.platform.config.config import get_config, load_ngrok_config
from skybridge.platform.observability.logger import get_logger, print_banner, print_ngrok_urls, print_local_urls, print_separator
from skybridge import __version__


def main():
    """Ponto de entrada."""
    config = get_config()
    logger = get_logger(level=config.log_level)

    # Banner de entrada estilo Claude
    print_banner(f"{config.title}", __version__)

    logger.info(f"Iniciando {config.title} v{__version__}")

    # Check ngrok
    ngrok_config = load_ngrok_config()
    if ngrok_config.enabled:
        logger.info("Ngrok habilitado - iniciando túnel...", extra={"enabled": True})
        try:
            from pyngrok import ngrok

            if ngrok_config.auth_token:
                ngrok.set_auth_token(ngrok_config.auth_token)

            # Open tunnel to port (use reserved domain if available)
            if ngrok_config.domain:
                tunnel = ngrok.connect(
                    config.port,
                    domain=ngrok_config.domain,
                    bind_tls=True
                )
                logger.info(f"Túnel Ngrok ativo com domínio reservado", extra={
                    "domain": ngrok_config.domain
                })
            else:
                tunnel = ngrok.connect(config.port)
                logger.info(f"Túnel Ngrok ativo", extra={"public_url": tunnel.public_url})

            # Imprime URL colorida
            print_ngrok_urls(
                base_url=tunnel.public_url,
                docs_url=config.docs_url,
                reserved_domain=ngrok_config.domain if ngrok_config.domain else None
            )
        except ImportError:
            logger.warning("pyngrok não instalado - pip install pyngrok")
        except Exception as e:
            logger.error("Falha ao iniciar Ngrok", extra={"error": str(e)})
    else:
        # Imprime URLs locais coloridas
        print_local_urls(
            host=config.host,
            port=config.port,
            docs_url=config.docs_url
        )

    # Run app
    app = get_app()
    app.run()


if __name__ == "__main__":
    main()
