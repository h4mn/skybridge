"""YouTube Copilot Discord Commands.

Apresentação Discord para YouTube Copilot CQRS Commands.

Comandos disponíveis:
- /youtube-sync - Sincroniza playlists
- /youtube-status - Mostra pendentes
- /youtube-stats - Estatísticas
- /youtube-list-playlists - Lista playlists
- /youtube-list <playlist> - Lista vídeos
"""

import os
from typing import Optional

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv

from src.core.youtube.application.youtube_commands import (
    YouTubeCommandHandler,
    YouTubeQueryHandler,
    SyncResult,
    StatusResult,
    StatsResult,
    PlaylistListResult,
    VideoListResult
)

load_dotenv()


class YouTubeCopilotCommands(commands.Cog):
    """Comandos Discord do YouTube Copilot."""

    def __init__(self, bot: commands.Bot):
        """Inicializa comandos.

        Args:
            bot: Bot Discord
        """
        self.bot = bot
        self.commands = YouTubeCommandHandler()
        self.queries = YouTubeQueryHandler()

    # =========================================================================
    # COMANDO: /youtube-sync
    # =========================================================================

    @commands.command(
        name="youtube-sync",
        brief="Sincroniza playlists com YouTube API",
        help="""
        Sincroniza suas playlists do YouTube com o banco local.

        Busca vídeos novos/atualizados e atualiza o estado.
        Use após adicionar vídeos às suas playlists.
        """
    )
    async def youtube_sync(self, ctx: commands.Context, playlist_id: str = "LL"):
        """Sincroniza playlist com YouTube API.

        Args:
            ctx: Contexto Discord
            playlist_id: ID da playlist (LL=favoritos, WL=watch later, ou ID custom)
        """
        # EMBED VERMELHO = em andamento
        embed = Embed(
            title="🔄 Sincronizando YouTube...",
            description=f"Buscando playlist `{playlist_id}`...",
            color=0xFF6B6B  # Vermelho
        )
        message = await ctx.send(embed=embed)

        # Executa Command
        result: SyncResult = self.commands.sync_playlist(playlist_id)

        if result.error:
            # EMBED VERMELHO = erro
            embed = Embed(
                title="❌ Erro na Sincronização",
                description=f"**Playlist:** `{result.playlist_id}`\n"
                            f"**Erro:** `{result.error}`",
                color=0xFF6B6B
            )
            await message.edit(embed=embed)
            return

        # EMBED VERDE = sucesso
        embed = Embed(
            title="✅ Sincronização Concluída",
            description=f"Playlist `{result.playlist_id}` sincronizada!",
            color=0x51CF66  # Verde
        )

        embed.add_field(
            name="📊 Estatísticas",
            value=f"**Total:** {result.total_videos} vídeos\n"
                  f"**Novos:** {result.new_videos} vídeos\n"
                  f"**Atualizados:** {result.updated_videos} vídeos",
            inline=False
        )

        if result.new_videos > 0:
            embed.add_field(
                name="🎯 Vídeos Novos",
                value=f"Você adicionou {result.new_videos} vídeo(s) desde a última sync!",
                inline=False
            )

        await message.edit(embed=embed)

    # =========================================================================
    # COMANDO: /youtube-status
    # =========================================================================

    @commands.command(
        name="youtube-status",
        brief="Mostra vídeos pendentes de notificação",
        help="""
        Mostra vídeos que ainda não foram notificados.

        Útil para ver o que precisa da sua atenção.
        """
    )
    async def youtube_status(self, ctx: commands.Context, playlist_id: str = "LL"):
        """Mostra vídeos pendentes de notificação.

        Args:
            ctx: Contexto Discord
            playlist_id: ID da playlist (padrão: LL)
        """
        # EMBED VERMELHO = carregando
        embed = Embed(
            title="🔍 Verificando Status...",
            description=f"Buscando vídeos pendentes em `{playlist_id}`...",
            color=0xFF6B6B  # Vermelho
        )
        message = await ctx.send(embed=embed)

        # Executa Query
        result: StatusResult = self.queries.get_status(playlist_id)

        if result.pending_notification == 0:
            # EMBED VERDE = tudo limpo
            embed = Embed(
                title="✅ Tudo em Dia!",
                description=f"Nenhum vídeo pendente em `{playlist_id}`",
                color=0x51CF66  # Verde
            )

            embed.add_field(
                name="📊 Estatísticas",
                value=f"**Total:** {result.total_videos} vídeos\n"
                      f"**Notificados:** {result.notified} vídeos\n"
                      f"**Transcritos:** {result.transcribed} vídeos",
                inline=False
            )
        else:
            # EMBED AMARELO = tem pendentes
            embed = Embed(
                title="⚠️ Vídeos Pendentes",
                description=f"Encontrados {result.pending_notification} vídeo(s) não notificado(s)",
                color=0xFFD93D  # Amarelo
            )

            for i, video in enumerate(result.pending_videos[:5], 1):
                duration = video.duration_seconds
                minutes = duration // 60
                seconds = duration % 60

                embed.add_field(
                    name=f"{i}. {video.title}",
                    value=f"Canal: {video.channel}\n"
                          f"Duração: {minutes}min {seconds}s\n"
                          f"Adicionado: {video.added_at.strftime('%d/%m %H:%M')}",
                    inline=False
                )

            if len(result.pending_videos) > 5:
                embed.add_field(
                    name="...",
                    value=f"E mais {len(result.pending_videos) - 5} vídeo(s)",
                    inline=False
                )

            embed.add_field(
                name="📊 Resumo",
                value=f"**Total:** {result.total_videos} vídeos\n"
                      f"**Pendentes:** {result.pending_notification} vídeos\n"
                      f"**Notificados:** {result.notified} vídeos",
                inline=False
            )

        await message.edit(embed=embed)

    # =========================================================================
    # COMANDO: /youtube-stats
    # =========================================================================

    @commands.command(
        name="youtube-stats",
        brief="Estatísticas das playlists",
        help="""
        Mostra estatísticas detalhadas das suas playlists.

        Inclui total de vídeos, pendentes, notificados, etc.
        """
    )
    async def youtube_stats(self, ctx: commands.Context):
        """Mostra estatísticas de todas as playlists.

        Args:
            ctx: Contexto Discord
        """
        embed = Embed(
            title="📊 Carregando Estatísticas...",
            color=0xFF6B6B
        )
        message = await ctx.send(embed=embed)

        # Executa Query
        result: StatsResult = self.queries.get_stats()

        # EMBED VERDE
        embed = Embed(
            title="📊 Estatísticas YouTube Copilot",
            description=f"Monitorando {result.total_playlists} playlists",
            color=0x51CF66
        )

        for stats in result.playlists[:10]:
            playlist_id = stats["playlist_id"]
            total = stats.get("total_videos", 0)
            notified = stats.get("notified", 0)

            # Barra de progresso
            if total > 0:
                progress = int((notified / total) * 10)
                bar = "🟩" * progress + "⬜" * (10 - progress)
            else:
                bar = "⬜" * 10

            embed.add_field(
                name=playlist_id,
                value=f"{bar}\n**{notified}/{total}** notificados",
                inline=True
            )

        if result.total_playlists > 10:
            embed.add_field(
                name="...",
                value=f"E mais {result.total_playlists - 10} playlists",
                inline=False
            )

        embed.add_field(
            name="🎯 Resumo",
            value=f"**Playlists:** {result.total_playlists}\n"
                  f"**Vídeos:** {result.total_videos}\n"
                  f"**Pendentes:** {result.total_pending}",
            inline=False
        )

        await message.edit(embed=embed)

    # =========================================================================
    # COMANDO: /youtube-list-playlists
    # =========================================================================

    @commands.command(
        name="youtube-list-playlists",
        brief="Lista todas as playlists",
        help="""
        Lista todas as playlists do seu YouTube.

        Mostra nome, ID e quantidade de vídeos.
        """
    )
    async def youtube_list_playlists(self, ctx: commands.Context):
        """Lista todas as playlists.

        Args:
            ctx: Contexto Discord
        """
        embed = Embed(
            title="📋 Carregando Playlists...",
            color=0xFF6B6B
        )
        message = await ctx.send(embed=embed)

        # Executa Query
        result: PlaylistListResult = self.queries.list_playlists()

        # EMBED VERDE
        embed = Embed(
            title="📋 Suas Playlists",
            description=f"Encontradas {result.total} playlists",
            color=0x51CF66
        )

        for i, playlist in enumerate(result.playlists[:15], 1):
            embed.add_field(
                name=f"{i}. {playlist['title']}",
                value=f"**ID:** `{playlist['id']}`\n"
                      f"**Vídeos:** {playlist['item_count']}",
                inline=False
            )

        if result.total > 15:
            embed.add_field(
                name="...",
                value=f"E mais {result.total - 15} playlists",
                inline=False
            )

        embed.add_field(
            name="💡 Dica",
            value=f"Use `/youtube-list <ID>` para ver os vídeos de uma playlist",
            inline=False
        )

        await message.edit(embed=embed)

    # =========================================================================
    # COMANDO: /youtube-list
    # =========================================================================

    @commands.command(
        name="youtube-list",
        brief="Lista vídeos de uma playlist",
        help="""
        Lista os vídeos de uma playlist específica.

        Mostra título, canal, duração e status.
        """
    )
    async def youtube_list(
        self,
        ctx: commands.Context,
        playlist_id: str
    ):
        """Lista vídeos de uma playlist.

        Args:
            ctx: Contexto Discord
            playlist_id: ID da playlist (ou LL para favoritos, WL para watch later)
        """
        embed = Embed(
            title=f"📺 Carregando vídeos de `{playlist_id}`...",
            color=0xFF6B6B
        )
        message = await ctx.send(embed=embed)

        # Executa Query
        result: VideoListResult = self.queries.list_videos(playlist_id)

        if result.total == 0:
            # EMBED AMARELO = playlist não syncada
            embed = Embed(
                title="⚠️ Playlist Não Sincronizada",
                description=f"A playlist `{playlist_id}` ainda não foi sincronizada.\n\n"
                            f"Use `/youtube-sync {playlist_id}` para sincronizar pela primeira vez.",
                color=0xFFD93D
            )
            await message.edit(embed=embed)
            return

        # EMBED VERDE
        embed = Embed(
            title=f"📺 {playlist_id}",
            description=f"Mostrando {result.total} vídeo(s) (primeiros 20)",
            color=0x51CF66
        )

        for i, video in enumerate(result.videos[:10], 1):
            duration = video.duration_seconds
            minutes = duration // 60
            seconds = duration % 60

            # Status emoji
            status_emoji = {
                "pending": "⏳",
                "synced": "✅",
                "notified": "🔔",
                "transcribed": "📝"
            }.get(video.status, "❓")

            embed.add_field(
                name=f"{i}. {video.title}",
                value=f"{status_emoji} {video.status}\n"
                      f"Canal: {video.channel}\n"
                      f"Duração: {minutes}min {seconds}s\n"
                      f"Sync: {video.synced_at.strftime('%d/%m %H:%M') if video.synced_at else 'Nunca'}",
                inline=False
            )

        if result.total > 10:
            embed.add_field(
                name="...",
                value=f"E mais {result.total - 10} vídeos",
                inline=False
            )

        await message.edit(embed=embed)


# Setup function para registrar no bot
async def setup(bot: commands.Bot):
    """Registra os comandos no bot.

    Args:
        bot: Bot Discord
    """
    await bot.add_cog(YouTubeCopilotCommands(bot))
