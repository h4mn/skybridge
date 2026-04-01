"""Bot Discord mínimo para monitorar canal específico."""
import os
from pathlib import Path
from typing import Optional
from enum import Enum, auto
from dataclasses import dataclass

import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import ButtonStyle

from dotenv import load_dotenv

# Carrega .env do diretório de trabalho atual (raiz do projeto)
load_dotenv(Path.cwd() / ".env")


class PaperBot:
    """Bot Discord para monitorar canal específico com arquitetura orientada a objetos."""

    # ID do canal a monitorar
    CHANNEL_ID = 1488702077747068959
    CHANNEL_LOG_ID = 1488739437251793078

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

            # Embed bonito para estado MAIN
            embed = discord.Embed(
                title="📊 Painel de Portfólio",
                description="Bem-vindo ao simulador de trading Paper",
                color=0x2ECC71  # Verde
            )
            embed.add_field(name="💵 Saldo Disponível", value="$500.00 USDT", inline=True)
            embed.add_field(name="📈 PnL Total", value="+$191.34 (+6.01%)", inline=True)
            embed.add_field(name="🔄 Status", value="✅ Online", inline=True)
            embed.set_footer(text="Paper Trading Sandbox • Use os botões abaixo para navegar")

            msg = await panel_msg.edit(embed=embed, view=view)
            print(f"[DEBUG] Mensagem enviada. ID: {msg.id}")

            # Enviar log para canal de logs
            log_channel = self._bot.get_channel(self.CHANNEL_LOG_ID)
            if log_channel:
                await log_channel.send(
                    f"📢 **Painel Criado**\n"
                    f"**Usuário:** {ctx.author.display_name}\n"
                    f"**Thread ID:** {thread.id}\n"
                    f"**Message ID:** {msg.id}"
                )


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
        if message.channel.id != self.CHANNEL_ID or message.author.bot:
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
        home_btn = Button(label="🏠 Home", style=ButtonStyle.primary, custom_id="home")
        home_btn.callback = self._on_home
        self.add_item(home_btn)

        back_btn = Button(label="⬅️ Voltar", style=ButtonStyle.secondary, custom_id="back")
        back_btn.callback = self._on_back
        self.add_item(back_btn)

        chart_btn = Button(label="📈 Gráfico", style=ButtonStyle.success, custom_id="asset_chart")
        chart_btn.callback = self._on_asset_chart
        self.add_item(chart_btn)
        print(f"[DEBUG] Botões 'home', 'back', 'asset_chart' adicionados")

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

        # Cria embed bonito com lista de ativos
        embed = discord.Embed(
            title="💰 Ativos no Portfólio",
            description="Selecione um ativo para ver detalhes",
            color=0xF39C12  # Dourado
        )
        embed.add_field(name="🪙 Bitcoin", value="`0.01234 BTC`\n`$1,234.56 USD`", inline=True)
        embed.add_field(name="🔷 Ethereum", value="`0.45678 ETH`\n`$1,456.78 USD`", inline=True)
        embed.add_field(name="💵 USDT", value="`500.00 USDT`\n`$500.00 USD`", inline=True)
        embed.set_footer(text="Dados mockados (sandbox) • Paper Trading")

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

            # Embed para estado EXPANDED
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
        self._send_to_log_channel(f"📢 Botão 'back' clicado por {interaction.user.display_name} - Novo estado: {new_state}")

    async def _on_asset_chart(self, interaction: discord.Interaction):
        """Callback do botão Gráfico - mostra placeholder."""
        print(f"[DEBUG] Botão 'asset_chart' clicado por {interaction.user.display_name}")

        # Embed bonito para gráfico (placeholder)
        embed = discord.Embed(
            title="📈 Gráfico de Ativo",
            description="Funcionalidade em desenvolvimento",
            color=0xE74C3C  # Vermelho
        )
        embed.add_field(name="Status", value="🔧 Em desenvolvimento", inline=False)
        embed.add_field(name="Planejamento", value="Candlestick charts com matplotlib", inline=False)
        embed.set_footer(text="Paper Trading Sandbox • Em breve")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        self._send_to_log_channel(f"📢 Botão 'asset_chart' clicado por {interaction.user.display_name}")


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
