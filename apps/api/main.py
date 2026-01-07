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
from skybridge.platform.observability.logger import get_logger


def main():
    """Ponto de entrada."""
    config = get_config()
    logger = get_logger(level=config.log_level)

    logger.info(f"Starting {config.title} v{config.version}")

    # Check ngrok
    ngrok_config = load_ngrok_config()
    if ngrok_config.enabled:
        logger.info("Ngrok is enabled - starting tunnel...", extra={"enabled": True})
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
                logger.info(f"Ngrok tunnel active with reserved domain", extra={
                    "public_url": tunnel.public_url,
                    "domain": ngrok_config.domain
                })
            else:
                tunnel = ngrok.connect(config.port)
                logger.info(f"Ngrok tunnel active", extra={"public_url": tunnel.public_url})

            print(f"\n{'='*60}")
            print(f"  Ticket:     {tunnel.public_url}/ticket")
            print(f"  Envelope:   {tunnel.public_url}/envelope")
            print(f"  OpenAPI:    {tunnel.public_url}/openapi")
            print(f"  Docs:       {tunnel.public_url}{config.docs_url}")
            print(f"{'='*60}")
            if ngrok_config.domain:
                print(f"  Reserved domain: {ngrok_config.domain}")
                print(f"{'='*60}\n")
            else:
                print()
        except ImportError:
            logger.warning("pyngrok not installed - pip install pyngrok")
        except Exception as e:
            logger.error("Failed to start ngrok", extra={"error": str(e)})
    else:
        print(f"\n{'='*60}")
        print(f"  Ticket:   http://{config.host}:{config.port}/ticket")
        print(f"  Envelope: http://{config.host}:{config.port}/envelope")
        print(f"  OpenAPI:  http://{config.host}:{config.port}/openapi")
        print(f"  Docs:     http://{config.host}:{config.port}{config.docs_url}")
        print(f"{'='*60}\n")

    # Run app
    app = get_app()
    app.run()


if __name__ == "__main__":
    main()
