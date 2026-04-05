"""Bot Discord mínimo para monitorar canal específico."""
import os
import asyncio
from pathlib import Path
from typing import Optional
from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import ButtonStyle
import requests

from dotenv import load_dotenv

# Carrega .env do diretório de trabalho atual (raiz do projeto)
load_dotenv(Path.cwd() / ".env")


# =============================================================================
# BINANCE PUBLIC FEED - Dados de mercado em tempo real (sem token)
# =============================================================================

class BinancePublicFeed:
    """Feed de dados públicos da Binance - sem autenticação."""

    BASE_URL = "https://api.binance.com"

    @classmethod
    def get_ticker(cls, symbol: str) -> dict:
        """Retorna ticker de 24h para um par."""
        response = requests.get(f"{cls.BASE_URL}/api/v3/ticker/24hr?symbol={symbol.upper()}")
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_price(cls, symbol: str) -> float:
        """Retorna preço atual de um par."""
        response = requests.get(f"{cls.BASE_URL}/api/v3/ticker/price?symbol={symbol.upper()}")
        response.raise_for_status()
        data = response.json()
        return float(data.get("price", 0))

    @classmethod
    def get_klines(cls, symbol: str, interval: str = "1h", limit: int = 24) -> list:
        """Retorna candles (klines) para um par."""
        response = requests.get(
            f"{cls.BASE_URL}/api/v3/klines",
            params={"symbol": symbol.upper(), "interval": interval, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_portfolio_value(cls, holdings: dict[str, float]) -> dict:
        """Calcula valor total do portfólio em tempo real."""
        total_value = 0.0
        details = {}

        for asset, quantity in holdings.items():
            if asset == "USDT":
                value = quantity
            else:
                # Busca preço em USDT (ex: BTCUSDT, ETHUSDT)
                try:
                    price = cls.get_price(f"{asset}USDT")
                    value = price * quantity
                except Exception:
                    value = 0

            details[asset] = {
                "quantity": quantity,
                "value_usdt": value,
                "price_usdt": value / quantity if quantity > 0 else 0
            }
            total_value += value

        return {
            "total_value_usdt": total_value,
            "details": details
        }


# =============================================================================
# MODELOS DE DADOS - Portfólio e Ativos
# =============================================================================

@dataclass
class AssetData:
    """Dados de um ativo no portfólio."""
    symbol: str
    quantity: float
    value_usdt: float
    price_usdt: float
    pnl_24h_percent: float = 0.0


@dataclass
class PortfolioData:
    """Dados completos do portfólio."""
    total_value_usdt: float
    pnl_24h_usdt: float
    pnl_24h_percent: float
    assets: list[AssetData]
    last_update: datetime


class PaperBot:
    """Bot Discord para monitorar canal específico com arquitetura orientada a objetos."""

    # ID do canal a monitorar
    CHANNEL_ID = 1488702077747068959
    CHANNEL_LOG_ID = 1488739437251793078
    ALLOWED_CHANNELS = [1488702077747068959, 1488599448882909204]  # Teste-01 e canal adicional

    def __init__(self, token: Optional[str] = None) -> None:
        """Inicializa o bot Discord.

        Args:
            token: Token do bot Discord. Se não fornecido, será lido da variável de ambiente.
        """
        self._token = token or os.getenv("DISCORD_PAPER_BOT_TOKEN")
        self._intents = self._configure_intents()
        self._bot = commands.Bot(command_prefix="!", intents=self._intents)
        self._state_machine = PortfolioStateMachine()  # Máquina de estados para o painel de portfólio
        self._setup_events()
        self._setup_commands()
        

    @staticmethod
    def _configure_intents() -> discord.Intents:
        """Configura os intents necessários para o bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        return intents

    def _setup_events(self) -> None:
        """Configura os event handlers do bot."""
        self._bot.event(self._on_ready)
        self._bot.event(self._on_message)
        self._bot.event(self._on_interaction)

    def _setup_commands(self) -> None:
        """Configura os comandos do bot."""

        ## !PAPER COMMAND ##
        ####################
        @self._bot.command(name="paper")
        async def _paper(ctx: commands.Context) -> None:
            """Responde com o identificador do painel de portfólio."""
            try:
                # DEBUG: Log comando recebido
                print(f"[DEBUG] Comando !paper recebido de {ctx.author.display_name}")
                print(f"[DEBUG] Message ID: {ctx.message.id}")
                print(f"[DEBUG] Channel ID: {ctx.message.channel.id}")

                ts = ctx.message.created_at.timestamp()

                # Remove threads existentes associadas a esta mensagem
                print(f"[DEBUG] Verificando threads existentes...")
                for existing_thread in ctx.channel.threads:
                    if existing_thread.owner_id == ctx.message.id:
                        print(f"[DEBUG] Apagando thread existente: {existing_thread.id}")
                        await existing_thread.delete()

                # Cria nova thread
                print(f"[DEBUG] Criando nova thread...")
                thread = await ctx.message.create_thread(
                    name=f"Thread {ts} de {ctx.author.display_name}",
                    auto_archive_duration=60,
                )
                print(f"[DEBUG] Thread criada: {thread.id}")

                # Envia mensagem inicial na thread
                panel_msg = await thread.send(f"📊 **Painel de Portfólio**")

                print(f"[DEBUG] Thread criada: {thread.id}")

                # Registra a view na máquina de estados
                print(f"[DEBUG] Registrando view na state machine...")
                view_ctx = self._state_machine.register(
                    message_id=panel_msg.id,
                    channel_id=thread.id,
                    user_id=ctx.message.author.id
                )
                print(f"[DEBUG] View registrada. Estado: {view_ctx.state}")

                # Cria a View com os botões
                print(f"[DEBUG] Criando PortfolioPanelView...")
                view = PortfolioPanelView(
                    bot=self._bot,
                    state_machine=self._state_machine,
                    ctx=view_ctx
                )
                print(f"[DEBUG] View criada. Itens: {len(view.children)}")

                # DEBUG: Verificando itens da view
                for i, item in enumerate(view.children):
                    print(f"[DEBUG]   Item {i}: {item.label} (custom_id={item.custom_id})")

                # Envia a mensagem inicial com a view
                print(f"[DEBUG] Enviando mensagem com view...")

                # Embed com dados reais da Binance
                # Busca dados em tempo real
                print(f"[DEBUG] Buscando dados da Binance...")
                try:
                    btc_ticker = BinancePublicFeed.get_ticker("BTCUSDT")
                    eth_ticker = BinancePublicFeed.get_ticker("ETHUSDT")
                    print(f"[DEBUG] Dados Binance recebidos: BTC=${btc_ticker.get('lastPrice', 0)}, ETH=${eth_ticker.get('lastPrice', 0)}")
    
                    btc_price = float(btc_ticker.get("lastPrice", 0))
                    eth_price = float(eth_ticker.get("lastPrice", 0))
                    btc_change = float(btc_ticker.get("priceChangePercent", 0))
                    eth_change = float(eth_ticker.get("priceChangePercent", 0))
    
                    # Portfólio mockado
                    holdings = {"BTC": 0.01234, "ETH": 0.45678, "USDT": 500.00}
                    portfolio = BinancePublicFeed.get_portfolio_value(holdings)
    
                    embed = discord.Embed(
                        title="📊 Painel de Portfólio",
                        description="Simulador de Trading com dados em tempo real",
                        color=0x2ECC71  # Verde
                    )
    
                    embed.add_field(
                        name="💰 Valor Total",
                        value=f"${portfolio['total_value_usdt']:,.2f} USDT",
                        inline=True
                    )
    
                    embed.add_field(
                        name="📊 Mercado BTC",
                        value=f"${btc_price:,.2f}\n({btc_change:+.2f}%)",
                        inline=True
                    )
    
                    embed.add_field(
                        name="📊 Mercado ETH",
                        value=f"${eth_price:,.2f}\n({eth_change:+.2f}%)",
                        inline=True
                    )
    
                    embed.add_field(
                        name="🪙 BTC",
                        value=f"{holdings['BTC']} BTC\n${portfolio['details']['BTC']['value_usdt']:,.2f}",
                        inline=True
                    )
    
                    embed.add_field(
                        name="🔷 ETH",
                        value=f"{holdings['ETH']} ETH\n${portfolio['details']['ETH']['value_usdt']:,.2f}",
                        inline=True
                    )
    
                    embed.add_field(
                        name="💵 USDT",
                        value=f"{holdings['USDT']} USDT\n${portfolio['details']['USDT']['value_usdt']:,.2f}",
                        inline=True
                    )
    
                    embed.set_footer(text="Dados Binance API Pública • Atualizado agora")
                    # embed.set_timestamp()  # Não disponível no discord.py 2.7.1
                    print(f"[DEBUG] Embed criado com sucesso. Título: {embed.title}")
    
                except Exception as e:
                    print(f"[DEBUG] ERRO ao buscar dados Binance: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback para dados mockados se Binance falhar
                    embed = discord.Embed(
                        title="📊 Painel de Portfólio",
                        description="Simulador de Trading (modo offline)",
                        color=0xE74C3C  # Vermelho
                    )
                    embed.add_field(name="💵 Saldo", value="$500.00 USDT (offline)", inline=True)
                    embed.add_field(name="📈 PnL", value="+$191.34 (+6.01%)", inline=True)
                    embed.set_footer(text=f"Erro Binance: {e}\nDados mockados")
    
                print(f"[DEBUG] Chamando panel_msg.edit()...")
                msg = await panel_msg.edit(content=None, embed=embed, view=view)
                print(f"[DEBUG] Mensagem editada. ID: {msg.id}, Embed: {msg.embeds}, View: {len(msg.components)} componentes")
    
                # Enviar log para canal de logs
                log_channel = self._bot.get_channel(self.CHANNEL_LOG_ID)
                if log_channel:
                    await log_channel.send(
                        f"📢 **Painel Criado**\n"
                        f"**Usuário:** {ctx.author.display_name}\n"
                        f"**Thread ID:** {thread.id}\n"
                        f"**Message ID:** {msg.id}"
                    )
            except Exception as e:
                print(f"[ERROR] Erro no comando !paper: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                await ctx.send(f"❌ Erro: {e}")

        ## !HEARTBEAT COMMAND ##
        #########################
        @self._bot.command(name="heartbeat")
        async def _heartbeat(ctx: commands.Context) -> None:
            """Mostra pulsação do sistema e dados em tempo real da Binance."""
            print(f"[DEBUG] Comando !heartbeat recebido de {ctx.author.display_name}")

            # Busca dados reais da Binance
            try:
                btc_ticker = BinancePublicFeed.get_ticker("BTCUSDT")
                eth_ticker = BinancePublicFeed.get_ticker("ETHUSDT")

                btc_price = float(btc_ticker.get("lastPrice", 0))
                eth_price = float(eth_ticker.get("lastPrice", 0))
                btc_change = float(btc_ticker.get("priceChangePercent", 0))
                eth_change = float(eth_ticker.get("priceChangePercent", 0))

                # Calcula portfólio mockado
                holdings = {"BTC": 0.01234, "ETH": 0.45678, "USDT": 500.00}
                portfolio = BinancePublicFeed.get_portfolio_value(holdings)

                embed = discord.Embed(
                    title="💓 Heartbeat - Paper Trading",
                    description=f"Sistema operacional em {datetime.now().strftime('%H:%M:%S')}",
                    color=0x2ECC71  # Verde
                )

                embed.add_field(
                    name="📊 Mercado (Binance)",
                    value=f"BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)\nETH: ${eth_price:,.2f} ({eth_change:+.2f}%)",
                    inline=False
                )

                embed.add_field(
                    name="💰 Portfólio (Sandbox)",
                    value=f"Total: ${portfolio['total_value_usdt']:,.2f} USDT\n\n"
                          f"BTC: {holdings['BTC']} BTC = ${portfolio['details']['BTC']['value_usdt']:,.2f}\n"
                          f"ETH: {holdings['ETH']} ETH = ${portfolio['details']['ETH']['value_usdt']:,.2f}\n"
                          f"USDT: {holdings['USDT']} USDT",
                    inline=False
                )

                embed.add_field(
                    name="⚡ Latência",
                    value=f"{int(ctx.bot.latency)}ms",
                    inline=True
                )

                embed.add_field(
                    name="🔄 Status",
                    value="✅ Online",
                    inline=True
                )

                embed.set_footer(text="Dados Binance API Pública • Paper Trading Sandbox")
                # embed.set_timestamp()  # Não disponível no discord.py 2.7.1

                await ctx.send(embed=embed)

            except Exception as e:
                await ctx.send(f"❌ Erro ao buscar dados da Binance: {e}")
            except Exception as e:
                await ctx.send(f"❌ Erro no heartbeat: {e}")

    async def _on_ready(self) -> None:
        """Log quando o bot estiver pronto."""
        channel = self._bot.get_channel(self.CHANNEL_ID)
        nome = getattr(channel, "name", "desconhecido")
        print(f"✅ Bot conectado! Monitorando canal: {nome}")

    async def _on_message(self, message: discord.Message) -> None:
        """Processa mensagens do canal monitorado.

        Args:
            message: Mensagem recebida do Discord.
        """
        # Enviar log para canal de logs
        log_channel = self._bot.get_channel(self.CHANNEL_LOG_ID)
        if log_channel:
            await log_channel.send(
                f"📢 **Mensagem Recebida**\n"
                f"**Canal:** {message.channel.name if message.channel else 'desconecido'}\n"
                f"**Usuário:** {message.author.display_name}\n"
                f"**Conteúdo:** {message.content}"
            )

        # Ignora mensagens de outros canais e do próprio bot
        if message.channel.id not in self.ALLOWED_CHANNELS or message.author.bot:
            return

        print(f"[{message.author.display_name}] {message.content}")
        await self._bot.process_commands(message)

    async def _on_interaction(self, interaction: discord.Interaction) -> None:
        """Log todas as interações para debug."""
        print(f"[DEBUG] Interação recebida!")
        print(f"[DEBUG]   Type: {interaction.type}")
        print(f"[DEBUG]   User: {interaction.user.display_name}")
        if interaction.type == discord.InteractionType.component:
            print(f"[DEBUG]   Custom ID: {interaction.data.get('custom_id')}")

        # Enviar log para canal de logs
        log_channel = self._bot.get_channel(self.CHANNEL_LOG_ID)
        if log_channel:
            await log_channel.send(
                f"📢 **Interação Recebida**\n"
                f"**Tipo:** {interaction.type}\n"
                f"**Usuário:** {interaction.user.display_name}\n"
                f"**Custom ID:** {interaction.data.get('custom_id') if interaction.data else 'N/A'}"
            )

    def run(self) -> None:
        """Inicia o bot Discord."""
        if not self._token:
            raise RuntimeError("Defina DISCORD_BOT_TOKEN nas variáveis de ambiente")
        self._bot.run(self._token)

    @property
    def bot(self) -> commands.Bot:
        """Retorna a instância do bot Discord."""
        return self._bot


class ViewState(Enum):
    """Estados possíveis para as views do painel."""
    MAIN = auto()
    EXPANDED = auto()
    ASSET_DETAIL = auto()


@dataclass
class ViewContext:
    """Contexto para renderização de views do painel."""
    state: ViewState
    message_id: int
    channel_id: int
    user_id: int
    selected_asset: str | None = None


class PortfolioStateMachine:
    """Máquina de estados para o painel de portfólio.

    Gerencia os estados do painel e as transições entre eles.
    """

    def __init__(self):
        self.state = "MAIN"  # Estado inicial
        self._views: dict[int, ViewContext] = {}  # message_id -> context
        self._transitions = self._define_transitions()

    def _define_transitions(self) -> dict[tuple[ViewState, str], ViewState]:
        """Define as transições de estado para cada ação."""
        return {
            # (estado_atual, ação): próximo_estado
            (ViewState.MAIN, "expand"): ViewState.EXPANDED,
            (ViewState.MAIN, "assets"): ViewState.EXPANDED,
            (ViewState.EXPANDED, "collapse"): ViewState.MAIN,
            (ViewState.EXPANDED, "charts"): ViewState.EXPANDED,
            (ViewState.ASSET_DETAIL, "back"): ViewState.MAIN,
            (ViewState.ASSET_DETAIL, "asset_chart"): ViewState.ASSET_DETAIL,
        }
    
    def transition(self, ctx: ViewContext, action: str) -> ViewState | None:
        """Realiza a transição de estado com base na ação.

        Args:
            ctx: Contexto da view atual.
            action: Ação que desencadeia a transição.

        Returns:
            O próximo estado após a transição, ou None se a transição for inválida.
        """
        key = (ctx.state, action)
        new_state = self._transitions.get(key)
        if new_state:
            ctx.state = new_state  # Atualiza o estado no contexto
        
        return new_state
    
    def register(self, message_id: int, channel_id: int, user_id: int) -> ViewContext:
        """Registra uma nova view e retorna seu contexto."""
        ctx = ViewContext(
            state=ViewState.MAIN,
            message_id=message_id,
            channel_id=channel_id,
            user_id=user_id
        )
        self._views[message_id] = ctx
        return ctx
    
    def get(self, message_id: int) -> ViewContext | None:
        """Recupera o contexto de uma view pelo ID da mensagem."""
        return self._views.get(message_id)


class PortfolioPanelView(View):
    """View Discord com botões de navegação do painel.

    Factory method que retorna a view correta para cada estado.
    """

    def __init__(self, bot, state_machine: PortfolioStateMachine, ctx: ViewContext):
        super().__init__(timeout=None)
        self.bot = bot
        self.sm = state_machine
        self.ctx = ctx
        print(f"[DEBUG] PortfolioPanelView criada. Estado: {ctx.state}")

        # Adiciona botões baseado no estado
        if ctx.state == ViewState.MAIN:
            self._add_main_buttons()
        elif ctx.state == ViewState.EXPANDED:
            self._add_expanded_buttons()
        elif ctx.state == ViewState.ASSET_DETAIL:
            self._add_asset_detail_buttons()

    def _add_main_buttons(self):
        """Adiciona botões do estado MAIN."""
        expand_btn = Button(label="📊 Expandir", style=ButtonStyle.primary, custom_id="expand")
        expand_btn.callback = self._on_expand
        self.add_item(expand_btn)
        print(f"[DEBUG] Botão 'expand' adicionado")

    def _add_expanded_buttons(self):
        """Adiciona botões do estado EXPANDED."""
        collapse_btn = Button(label="⬅️ Voltar", style=ButtonStyle.secondary, custom_id="collapse")
        collapse_btn.callback = self._on_collapse
        self.add_item(collapse_btn)

        assets_btn = Button(label="💰 Ativos", style=ButtonStyle.secondary, custom_id="assets")
        assets_btn.callback = self._on_assets
        self.add_item(assets_btn)
        print(f"[DEBUG] Botões 'collapse' e 'assets' adicionados")

    def _add_asset_detail_buttons(self):
        """Adiciona botões do estado ASSET_DETAIL."""
        # Se um ativo está selecionado, mostra botão de gráfico específico
        if self.ctx.selected_asset:
            chart_btn = Button(label=f"📈 Gráfico {self.ctx.selected_asset}", style=ButtonStyle.success, custom_id="asset_chart")
            chart_btn.callback = self._on_asset_chart
            self.add_item(chart_btn)

            back_btn = Button(label="⬅️ Voltar", style=ButtonStyle.secondary, custom_id="back_to_assets")
            back_btn.callback = self._on_back_to_assets
            self.add_item(back_btn)
        else:
            # Botões para selecionar cada ativo
            btc_btn = Button(label="🪙 Bitcoin", style=ButtonStyle.primary, custom_id="select_btc")
            btc_btn.callback = self._on_select_asset
            self.add_item(btc_btn)

            eth_btn = Button(label="🔷 Ethereum", style=ButtonStyle.primary, custom_id="select_eth")
            eth_btn.callback = self._on_select_asset
            self.add_item(eth_btn)

            home_btn = Button(label="🏠 Home", style=ButtonStyle.secondary, custom_id="home")
            home_btn.callback = self._on_home
            self.add_item(home_btn)

        print(f"[DEBUG] Botões ASSET_DETAIL adicionados. selected_asset={self.ctx.selected_asset}")

    def _send_to_log_channel(self, message: str):
        """Envia uma mensagem para o canal de logs."""
        log_channel = self.bot.get_channel(PaperBot.CHANNEL_LOG_ID)
        if log_channel:
            self.bot.loop.create_task(log_channel.send(message))

    # ==================== CALLBACKS DOS BOTÕES ====================

    async def _on_expand(self, interaction: discord.Interaction):
        """Callback do botão Expandir."""
        print(f"[DEBUG] Botão 'expand' clicado por {interaction.user.display_name}")
        new_state = self.sm.transition(self.ctx, "expand")
        if new_state:
            new_view = PortfolioPanelView(self.bot, self.sm, self.ctx)

            # Embed bonito para estado EXPANDED
            embed = discord.Embed(
                title="📊 Painel de Portfólio - Expandido",
                description="Visão detalhada do seu portfólio",
                color=0x3498DB  # Azul
            )
            embed.add_field(name="💰 Saldo Total", value="$3,191.34 USD", inline=True)
            embed.add_field(name="📈 PnL 24h", value="+2.34%", inline=True)
            embed.add_field(name="🔄 Operações", value="127 trades", inline=True)
            embed.set_footer(text="Paper Trading Sandbox • Dados mockados")

            await interaction.response.edit_message(embed=embed, view=new_view)
        self._send_to_log_channel(f"📢 Botão 'expand' clicado por {interaction.user.display_name} - Novo estado: {new_state}")

    async def _on_collapse(self, interaction: discord.Interaction):
        """Callback do botão Voltar (collapse)."""
        print(f"[DEBUG] Botão 'collapse' clicado por {interaction.user.display_name}")
        new_state = self.sm.transition(self.ctx, "collapse")
        if new_state:
            new_view = PortfolioPanelView(self.bot, self.sm, self.ctx)

            # Embed para voltar ao MAIN
            embed = discord.Embed(
                title="📊 Painel de Portfólio",
                description="Bem-vindo ao simulador de trading Paper",
                color=0x2ECC71  # Verde
            )
            embed.add_field(name="💵 Saldo Disponível", value="$500.00 USDT", inline=True)
            embed.add_field(name="📈 PnL Total", value="+$191.34 (+6.01%)", inline=True)
            embed.add_field(name="🔄 Status", value="✅ Online", inline=True)
            embed.set_footer(text="Paper Trading Sandbox • Use os botões abaixo para navegar")

            await interaction.response.edit_message(embed=embed, view=new_view)
        self._send_to_log_channel(f"📢 Botão 'collapse' clicado por {interaction.user.display_name} - Novo estado: {new_state}")

    async def _on_assets(self, interaction: discord.Interaction):
        """Callback do botão Ativos - transiciona para ASSET_DETAIL."""
        print(f"[DEBUG] Botão 'assets' clicado por {interaction.user.display_name}")

        # Transiciona para estado ASSET_DETAIL
        self.ctx.state = ViewState.ASSET_DETAIL
        self.ctx.selected_asset = None  # Reset seleção de ativo

        new_view = PortfolioPanelView(self.bot, self.sm, self.ctx)

        # Busca dados reais da Binance
        try:
            holdings = {"BTC": 0.01234, "ETH": 0.45678, "USDT": 500.00}
            portfolio = BinancePublicFeed.get_portfolio_value(holdings)

            # Busca ticker 24h para cada ativo
            btc_24h = BinancePublicFeed.get_ticker("BTCUSDT")
            eth_24h = BinancePublicFeed.get_ticker("ETHUSDT")

            btc_price = float(btc_24h.get("lastPrice", 0))
            eth_price = float(eth_24h.get("lastPrice", 0))
            btc_change = float(btc_24h.get("priceChangePercent", 0))
            eth_change = float(eth_24h.get("priceChangePercent", 0))
            btc_vol = float(btc_24h.get("volume", 0))
            eth_vol = float(eth_24h.get("volume", 0))

            # Embed com dados reais
            embed = discord.Embed(
                title="💰 Ativos no Portfólio",
                description="Dados em tempo real da Binance",
                color=0xF39C12  # Dourado
            )

            # Bitcoin com dados reais
            btc_value = portfolio['details']['BTC']['value_usdt']
            embed.add_field(
                name="🪙 Bitcoin",
                value=f"`{holdings['BTC']} BTC`\n"
                      f"`${btc_value:,.2f} USD`\n"
                      f"`{btc_change:+.2f}%` (24h)\n"
                      f"`Vol: ${btc_vol:,.0f}`",
                inline=True
            )

            # Ethereum com dados reais
            eth_value = portfolio['details']['ETH']['value_usdt']
            embed.add_field(
                name="🔷 Ethereum",
                value=f"`{holdings['ETH']} ETH`\n"
                      f"`${eth_value:,.2f} USD`\n"
                      f"`{eth_change:+.2f}%` (24h)\n"
                      f"`Vol: ${eth_vol:,.0f}`",
                inline=True
            )

            # USDT
            usdt_value = portfolio['details']['USDT']['value_usdt']
            embed.add_field(
                name="💵 USDT",
                value=f"`{holdings['USDT']} USDT`\n"
                      f"`${usdt_value:,.2f} USD`\n"
                      f"`Estável`",
                inline=True
            )

            embed.add_field(
                name="💰 Total",
                value=f"`${portfolio['total_value_usdt']:,.2f} USDT`",
                inline=False
            )

            embed.set_footer(text="Dados Binance API Pública • Atualizado agora")
            # embed.set_timestamp()  # Não disponível no discord.py 2.7.1

        except Exception as e:
            # Fallback para dados mockados
            embed = discord.Embed(
                title="💰 Ativos no Portfólio",
                description="Selecione um ativo para ver detalhes",
                color=0xF39C12  # Dourado
            )
            embed.add_field(name="🪙 Bitcoin", value="`0.01234 BTC`\n`$1,234.56 USD`", inline=True)
            embed.add_field(name="🔷 Ethereum", value="`0.45678 ETH`\n`$1,456.78 USD`", inline=True)
            embed.add_field(name="💵 USDT", value="`500.00 USDT`\n`$500.00 USD`", inline=True)
            embed.set_footer(text=f"Erro: {e}\nDados mockados (sandbox)")

        await interaction.response.edit_message(embed=embed, view=new_view)
        self._send_to_log_channel(f"📢 Botão 'assets' clicado por {interaction.user.display_name} - Estado: ASSET_DETAIL")

    async def _on_home(self, interaction: discord.Interaction):
        """Callback do botão Home - volta diretamente ao MAIN."""
        print(f"[DEBUG] Botão 'home' clicado por {interaction.user.display_name}")
        self.ctx.state = ViewState.MAIN
        new_view = PortfolioPanelView(self.bot, self.sm, self.ctx)

        # Embed para voltar ao MAIN
        embed = discord.Embed(
            title="📊 Painel de Portfólio",
            description="Bem-vindo ao simulador de trading Paper",
            color=0x2ECC71  # Verde
        )
        embed.add_field(name="💵 Saldo Disponível", value="$500.00 USDT", inline=True)
        embed.add_field(name="📈 PnL Total", value="+$191.34 (+6.01%)", inline=True)
        embed.add_field(name="🔄 Status", value="✅ Online", inline=True)
        embed.set_footer(text="Paper Trading Sandbox • Use os botões abaixo para navegar")

        await interaction.response.edit_message(embed=embed, view=new_view)
        self._send_to_log_channel(f"📢 Botão 'home' clicado por {interaction.user.display_name} - Voltando para estado MAIN")

    async def _on_back(self, interaction: discord.Interaction):
        """Callback do botão Voltar - volta para EXPANDED."""
        print(f"[DEBUG] Botão 'back' clicado por {interaction.user.display_name}")
        new_state = self.sm.transition(self.ctx, "back")
        if new_state:
            new_view = PortfolioPanelView(self.bot, self.sm, self.ctx)

            # Embed para estado EXPANDED com dados reais
            try:
                holdings = {"BTC": 0.01234, "ETH": 0.45678, "USDT": 500.00}
                portfolio = BinancePublicFeed.get_portfolio_value(holdings)
                btc_ticker = BinancePublicFeed.get_ticker("BTCUSDT")
                btc_change = float(btc_ticker.get("priceChangePercent", 0))

                embed = discord.Embed(
                    title="📊 Painel de Portfólio - Expandido",
                    description="Visão detalhada com dados em tempo real",
                    color=0x3498DB  # Azul
                )

                embed.add_field(
                    name="💰 Saldo Total",
                    value=f"${portfolio['total_value_usdt']:,.2f} USDT",
                    inline=True
                )

                embed.add_field(
                    name="📈 PnL BTC 24h",
                    value=f"{btc_change:+.2f}%",
                    inline=True
                )

                embed.add_field(
                    name="🔄 Ativos",
                    value=f"{len(holdings)} ativos",
                    inline=True
                )

                # Detalhes dos ativos
                assets_text = ""
                for asset, data in portfolio['details'].items():
                    assets_text += f"**{asset}**: {data['quantity']} @ ${data['price_usdt']:,.2f}\n"

                embed.add_field(
                    name="📋 Posições",
                    value=assets_text or "Nenhum ativo",
                    inline=False
                )

                embed.set_footer(text="Dados Binance API Pública • Paper Trading Sandbox")
                # embed.set_timestamp()  # Não disponível no discord.py 2.7.1

            except Exception as e:
                # Fallback
                embed = discord.Embed(
                    title="📊 Painel de Portfólio - Expandido",
                    description="Visão detalhada do seu portfólio",
                    color=0x3498DB
                )
                embed.add_field(name="💰 Saldo Total", value="$3,191.34 USD", inline=True)
                embed.add_field(name="📈 PnL 24h", value="+2.34%", inline=True)
                embed.add_field(name="🔄 Operações", value="127 trades", inline=True)
                embed.set_footer(text="Modo offline • Dados mockados")

            await interaction.response.edit_message(embed=embed, view=new_view)
        self._send_to_log_channel(f"📢 Botão 'back' clicado por {interaction.user.display_name} - Novo estado: {new_state}")

    async def _on_select_asset(self, interaction: discord.Interaction):
        """Callback do botão de selecionar ativo (BTC/ETH)."""
        print(f"[DEBUG] Botão de select_asset clicado. Custom ID: {interaction.data.get('custom_id')}")

        # Determina qual ativo foi selecionado baseado no custom_id
        custom_id = interaction.data.get('custom_id', '')
        if custom_id == "select_btc":
            self.ctx.selected_asset = "BTC"
        elif custom_id == "select_eth":
            self.ctx.selected_asset = "ETH"
        else:
            self.ctx.selected_asset = None

        print(f"[DEBUG] Ativo selecionado: {self.ctx.selected_asset}")

        # Recria a view com o ativo selecionado
        new_view = PortfolioPanelView(self.bot, self.sm, self.ctx)

        # Busca dados específicos do ativo selecionado
        embed = None  # Inicializa para evitar UnboundLocalError
        try:
            if self.ctx.selected_asset == "BTC":
                ticker = BinancePublicFeed.get_ticker("BTCUSDT")
                klines = BinancePublicFeed.get_klines("BTCUSDT", "1h", 24)
                emoji = "🪙"
                name = "Bitcoin"
            elif self.ctx.selected_asset == "ETH":
                ticker = BinancePublicFeed.get_ticker("ETHUSDT")
                klines = BinancePublicFeed.get_klines("ETHUSDT", "1h", 24)
                emoji = "🔷"
                name = "Ethereum"
            else:
                raise ValueError("Ativo inválido")

            price = float(ticker.get("lastPrice", 0))
            change = float(ticker.get("priceChangePercent", 0))
            volume = float(ticker.get("volume", 0))
            high = float(ticker.get("highPrice", 0))
            low = float(ticker.get("lowPrice", 0))

            embed = discord.Embed(
                title=f"{emoji} {name} - Detalhes",
                description=f"Dados em tempo real da Binance",
                color=0xF39C12
            )

            embed.add_field(name="💰 Preço", value=f"${price:,.2f} USDT", inline=True)
            embed.add_field(name="📈 Variação 24h", value=f"{change:+.2f}%", inline=True)
            embed.add_field(name="📊 Volume", value=f"${volume:,.0f}", inline=True)
            embed.add_field(name="⬆️ Máxima 24h", value=f"${high:,.2f}", inline=True)
            embed.add_field(name="⬇️ Mínima 24h", value=f"${low:,.2f}", inline=True)
            embed.add_field(name="🕯️ Candles", value=f"{len(klines)} candles (1h)", inline=True)

            embed.set_footer(text=f"Dados Binance API • Clique em 'Gráfico {self.ctx.selected_asset}' para ver o candlestick")
            # embed.set_timestamp()  # Não disponível no discord.py 2.7.1

        except Exception as e:
            print(f"[DEBUG] Erro ao buscar dados do ativo: {e}")
            import traceback
            traceback.print_exc()
            embed = discord.Embed(
                title=f"❌ Erro",
                description=f"Não foi possível buscar dados de {self.ctx.selected_asset}",
                color=0xE74C3C
            )
            embed.add_field(name="Exception", value=f"`{type(e).__name__}`", inline=True)
            embed.add_field(name="Message", value=f"```{str(e)[:200]}```", inline=False)
            embed.set_footer(text=f"Erro: {e}")
            # embed.set_timestamp()  # Não disponível no discord.py 2.7.1

        await interaction.response.edit_message(embed=embed, view=new_view)
        self._send_to_log_channel(f"📢 Ativo {self.ctx.selected_asset} selecionado")

    async def _on_back_to_assets(self, interaction: discord.Interaction):
        """Callback do botão Voltar (da seleção de ativo para a lista)."""
        print(f"[DEBUG] Botão 'back_to_assets' clicado")

        # Reseta a seleção de ativo
        self.ctx.selected_asset = None

        # Volta para o estado ASSET_DETAIL sem seleção
        new_view = PortfolioPanelView(self.bot, self.sm, self.ctx)

        # Reusa o callback _on_assets para mostrar a lista de ativos
        # Cria um interaction mock ou chama diretamente a lógica
        await self._on_assets(interaction)

    async def _on_asset_chart(self, interaction: discord.Interaction):
        """Callback do botão Gráfico - mostra candlestick do ativo selecionado."""
        print(f"[DEBUG] Botão 'asset_chart' clicado para {self.ctx.selected_asset}")

        asset = self.ctx.selected_asset
        if not asset:
            await interaction.response.send_message("❌ Nenhum ativo selecionado", ephemeral=True)
            return

        await interaction.response.defer()  # Defer pois pode demorar para gerar o gráfico

        try:
            # Busca klines da Binance
            symbol = f"{asset}USDT"
            klines = BinancePublicFeed.get_klines(symbol, "1h", 24)

            # Formata dados para o gráfico
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []

            for k in klines:
                # kline format: [time, open, high, low, close, volume, ...]
                dates.append(int(k[0]))  # timestamp
                opens.append(float(k[1]))
                highs.append(float(k[2]))
                lows.append(float(k[3]))
                closes.append(float(k[4]))

            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime

            # Cria o gráfico candlestick manual
            fig, ax = plt.subplots(figsize=(12, 6))

            # Plota as velas (verde para alta, vermelho para baixa)
            for i, (date, open_p, high, low, close) in enumerate(zip(dates, opens, highs, lows, closes)):
                dt = datetime.fromtimestamp(date / 1000)
                color = 'green' if close >= open_p else 'red'

                # Linha vertical (high-low)
                ax.plot([dt, dt], [low, high], color=color, linewidth=1)

                # Retângulo (open-close)
                height = abs(close - open_p)
                bottom = min(open_p, close)
                ax.bar(dt, height, bottom=bottom, width=0.02, color=color, edgecolor='black', linewidth=0.5)

            ax.set_title(f'{asset}USDT - Últimas 24 horas (Candles de 1h)', fontsize=14, fontweight='bold')
            ax.set_xlabel('Hora', fontsize=12)
            ax.set_ylabel('Preço (USDT)', fontsize=12)
            ax.grid(True, alpha=0.3)

            # Formata o eixo X para mostrar horas
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            fig.autofmt_xdate()

            # Adiciona preço atual
            current_price = closes[-1]
            change_pct = ((closes[-1] - opens[0]) / opens[0]) * 100
            change_color = 'green' if change_pct >= 0 else 'red'
            ax.text(0.02, 0.98, f'${current_price:,.2f} ({change_pct:+.2f}%)',
                   transform=ax.transAxes, fontsize=12, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor=change_color, alpha=0.3))

            plt.tight_layout()

            # Salva para BytesIO
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close()

            # Envia a imagem para o Discord
            file = discord.File(buf, filename=f'{asset}_chart.png')

            embed = discord.Embed(
                title=f"📈 Gráfico {asset}USDT",
                description=f"Candlestick das últimas 24 horas\nVariação: {change_pct:+.2f}%",
                color=0x2ECC71 if change_pct >= 0 else 0xE74C3C
            )
            embed.set_image(url=f"attachment://{asset}_chart.png")
            embed.set_footer(text="Dados Binance API • Paper Trading Sandbox")
            # embed.set_timestamp()  # Não disponível no discord.py 2.7.1

            await interaction.followup.send(embed=embed, file=file)
            self._send_to_log_channel(f"📢 Gráfico {asset} gerado com sucesso")

        except Exception as e:
            print(f"[DEBUG] Erro ao gerar gráfico: {e}")
            import traceback
            traceback.print_exc()

            embed = discord.Embed(
                title="❌ Erro ao Gerar Gráfico",
                description=f"Não foi possível gerar o candlestick de {asset}",
                color=0xE74C3C
            )
            embed.add_field(name="Erro", value=f"`{type(e).__name__}: {e}`", inline=False)
            await interaction.followup.send(embed=embed)


class PaperAppHelloWorld:
    """Aplicação principal do bot Paper."""

    def __init__(self) -> None:
        """Inicializa a aplicação com o bot."""
        self._paper_bot = PaperBot()

    def run(self) -> None:
        """Executa a aplicação."""
        self._paper_bot.run()


if __name__ == "__main__":
    app = PaperAppHelloWorld()
    app.run()
