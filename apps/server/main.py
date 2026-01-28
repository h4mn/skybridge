# -*- coding: utf-8 -*-
"""
Skybridge Server — Servidor unificado (PRD022).

Ponto de entrada que combina:
- API FastAPI
- WebUI estático (/web)
- Logging unificado (estratégia híbrida LOG-001 + LOG-002)
- Ngrok integration
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Load .env
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from runtime.bootstrap.app import get_app
from runtime.config.config import get_config, load_ngrok_config
from runtime.observability.logger import (
    get_logger,
    print_banner,
    print_ngrok_urls,
    print_local_urls,
    print_separator,
    Colors,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from version import __version__


def get_log_config() -> dict:
    """
    Retorna configuração de logging do uvicorn.

    Usa ColorFormatter do Skybridge para formatação consistente.
    Desabilita uvicorn.access pois o RequestLoggingMiddleware cuida disso.
    """
    logs_dir = Path("workspace/skybridge/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "skybridge": {
                "()": "runtime.observability.logger.ColorFormatter",
            }
        },
        "handlers": {
            "console": {
                "formatter": "skybridge",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": [],  # ← DESABILITADO - RequestLoggingMiddleware cuida
                "level": "INFO",
                "propagate": False,
            },
        }
    }


class SkybridgeServer:
    """
    Servidor unificado Skybridge.

    Combina API FastAPI com WebUI estático.
    """

    def __init__(self):
        self.skybridge_app = get_app()
        self.app = self.skybridge_app.app
        self._setup_static_routes()

    def _setup_static_routes(self):
        """
        Configura rotas estáticas para WebUI.

        - / → redirect para /web/
        - /web/assets/* → assets estáticos
        - /web/* → SPA fallback (exceto /web/assets)
        - /web → redirect para /web/
        """
        web_dist = Path(__file__).parent.parent / "web" / "dist"

        # Redirect / → /web/
        @self.app.get("/")
        async def root_redirect():
            """Redireciona raiz para WebUI."""
            return RedirectResponse(url="/web/")

        # Redirect /web → /web/
        @self.app.get("/web")
        async def web_redirect():
            """Redireciona /web para /web/."""
            return RedirectResponse(url="/web/")

        # /web/ retorna 404 quando dist não existe, ou index.html quando existe
        @self.app.get("/web/")
        async def webui_index():
            """Retorna index.html ou 404."""
            web_dist = Path(__file__).parent.parent / "web" / "dist"
            if web_dist.exists():
                return FileResponse(web_dist / "index.html")
            # 404 se dist não existe
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=404,
                content={"detail": "WebUI not built. Run 'cd apps/web && npm run build'"}
            )

        # Assets estáticos - rota específica avaliada ANTES do SPA genérico
        @self.app.get("/web/assets/{path:path}")
        async def webui_assets(path: str):
            """Serve assets estáticos com MIME type correto."""
            web_dist = Path(__file__).parent.parent / "web" / "dist"
            assets_dir = web_dist / "assets"
            asset_path = assets_dir / path

            if asset_path.exists() and asset_path.is_file():
                # Define MIME type correto
                if path.endswith('.js') or path.endswith('.mjs'):
                    return FileResponse(asset_path, media_type='application/javascript; charset=utf-8')
                elif path.endswith('.css'):
                    return FileResponse(asset_path, media_type='text/css; charset=utf-8')
                else:
                    return FileResponse(asset_path)

            # 404 se asset não existe
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Asset not found"})

        # SPA fallback para outras rotas do React (NÃO inclui assets devido à rota acima)
        @self.app.get("/web/{path:path}")
        async def webui_spa(path: str):
            """Fallback para SPA - retorna index.html para rotas não-asset."""
            web_dist = Path(__file__).parent.parent / "web" / "dist"

            # Se for um arquivo que existe na raiz do dist, serve ele
            file_path = web_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)

            # Senão, retorna index.html (SPA fallback)
            if web_dist.exists():
                return FileResponse(web_dist / "index.html")

            # 404 se dist não existe
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=404,
                content={"detail": "WebUI not built. Run 'cd apps/web && npm run build'"}
            )

    def run(
        self,
        host: str,
        port: int,
        log_config: dict = None,
        access_log: bool = False,
    ):
        """
        Executa o servidor com uvicorn.

        Args:
            host: Host para bind
            port: Porta para listen
            log_config: Configuração de logging do uvicorn
            access_log: Desabilitado (middleware cuida)
        """
        uvicorn.run(
            app=self.app,
            host=host,
            port=port,
            log_config=log_config,
            access_log=access_log,
        )


def main():
    """Ponto de entrada do servidor unificado."""
    config = get_config()
    logger = get_logger(level=config.log_level)

    # Banner de entrada
    print_banner("Skybridge Server", __version__)
    logger.info(f"Iniciando Skybridge Server v{__version__}")

    # Ngrok integration
    ngrok_config = load_ngrok_config()
    tunnel_url = None

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
                tunnel_url = tunnel.public_url
                logger.info(f"Túnel Ngrok ativo com domínio reservado", extra={
                    "domain": ngrok_config.domain
                })
            else:
                tunnel = ngrok.connect(config.port)
                tunnel_url = tunnel.public_url
                logger.info(f"Túnel Ngrok ativo", extra={"public_url": tunnel_url})

            # Imprime URL colorida
            print_ngrok_urls(
                base_url=tunnel_url,
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

    # Cria e executa servidor unificado
    server = SkybridgeServer()

    # Imprime informações do WebUI
    web_dist = Path(__file__).parent.parent / "web" / "dist"
    if web_dist.exists():
        print_separator("─", 60)
        print(f"{Colors.CYAN}WebUI disponível em:{Colors.RESET}")
        if tunnel_url:
            print(f"  {Colors.CYAN}{tunnel_url}/web/{Colors.RESET}")
        else:
            print(f"  {Colors.CYAN}http://{config.host}:{config.port}/web/{Colors.RESET}")
        print_separator("─", 60)
        print()

    # Executa servidor
    server.run(
        host=config.host,
        port=config.port,
        log_config=get_log_config(),
        access_log=False,  # Desabilita uvicorn.access - middleware cuida
    )


if __name__ == "__main__":
    main()
