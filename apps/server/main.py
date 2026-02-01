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
import subprocess
import shutil
import signal
import asyncio

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
    from runtime.config.config import get_workspace_logs_dir
    logs_dir = get_workspace_logs_dir()
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


def ensure_webui_built() -> bool:
    """
    Verifica se o WebUI foi built, e tenta buildar se necessário.

    Returns:
        True se WebUI está pronto ou build foi bem-sucedido, False caso contrário
    """
    web_dist = Path(__file__).parent.parent / "web" / "dist"
    web_src = Path(__file__).parent.parent / "web"

    # Verifica se dist existe e tem index.html
    if web_dist.exists() and (web_dist / "index.html").exists():
        return True

    logger = get_logger()
    logger.info("WebUI não encontrado. Tentando build automático...")

    # Verifica se npm está disponível
    if not shutil.which("npm"):
        logger.warning("npm não encontrado. WebUI não será disponível.")
        return False

    # Verifica se o diretório web existe
    if not web_src.exists():
        logger.warning(f"Diretório {web_src} não encontrado.")
        return False

    try:
        # Executa npm run build no diretório web (usa shell=True para Windows)
        result = subprocess.run(
            "npm run build",
            cwd=web_src,
            capture_output=True,
            text=True,
            encoding='utf-8',  # UTF-8 para lidar com caracteres especiais
            errors='replace',  # Substitui caracteres inválidos em vez de falhar
            shell=True,  # Necessário no Windows para encontrar npm
            timeout=180  # 3 minutos max
        )

        if result.returncode == 0 and web_dist.exists():
            logger.info("WebUI build concluído com sucesso!")
            return True
        else:
            logger.warning(f"WebUI build falhou: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning("WebUI build expirou (timeout de 180s)")
        return False
    except Exception as e:
        logger.warning(f"Erro ao buildar WebUI: {e}")
        return False


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

        # Favicon Skybridge (ponte vermelha)
        @self.app.get("/favicon.svg")
        async def favicon():
            """Serve favicon SVG com a ponte vermelha."""
            web_dist = Path(__file__).parent.parent / "web" / "dist"
            favicon_path = web_dist / "favicon.svg"
            if favicon_path.exists():
                return FileResponse(favicon_path, media_type="image/svg+xml")
            # 404 se favicon não existe
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Favicon not found"})

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
            loop="asyncio",  # Força uso do asyncio event loop
            timeout_graceful_shutdown=10,  # Dá 10s para shutdown gracioso
        )


def main():
    """Ponto de entrada do servidor unificado."""
    config = get_config()
    logger = get_logger(level=config.log_level)

    # Banner de entrada
    print_banner("Skybridge Server", __version__)
    logger.info(f"Iniciando Skybridge Server v{__version__}")

    # Garante que WebUI está built (antes do Ngrok e servidor)
    webui_ready = ensure_webui_built()

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

    # Executa servidor
    server.run(
        host=config.host,
        port=config.port,
        log_config=get_log_config(),
        access_log=False,  # Desabilita uvicorn.access - middleware cuida
    )


if __name__ == "__main__":
    main()
