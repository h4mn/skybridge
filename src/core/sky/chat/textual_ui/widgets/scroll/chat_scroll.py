# coding: utf-8
"""
ChatScroll - VerticalScroll que gerencia Turns da conversa.

Responsabilidades:
- Abrir novo Turn via iniciar_turno()
- Delegar set_response / set_error ao Turn ativo
- Scroll automático ao final após cada atualização
- Limpar todos os Turns via limpar()

O método legado adicionar_mensagem() é mantido para
compatibilidade com código de teste, mas não cria Turn.
"""

from textual.containers import VerticalScroll
from textual.widgets import Static

from core.sky.chat.textual_ui.widgets.content.turn import Turn


class ChatScroll(VerticalScroll):
    """VerticalScroll que gerencia o histórico de turnos do chat."""

    # ------------------------------------------------------------------
    # API principal — usada pelo ChatScreen
    # ------------------------------------------------------------------

    def iniciar_turno(self, user_message: str) -> Turn:
        """
        Abre um novo turno com a mensagem do usuário.

        Calcula o número do turno contando os Turns existentes,
        monta o widget e ativa o ThinkingIndicator.

        Args:
            user_message: Texto enviado pelo usuário.

        Returns:
            Turn recém-montado (ainda sem resposta).
        """
        turn_number = len(self.query(Turn)) + 1
        turn = Turn(user_message, turn_number)
        self.mount(turn)
        self.call_later(self.scroll_end)
        return turn

    # ------------------------------------------------------------------
    # Métodos legados — mantidos para compatibilidade
    # ------------------------------------------------------------------

    def adicionar_mensagem_usuario(self, texto: str) -> None:
        """
        [LEGADO] Adiciona mensagem do usuário sem criar Turn completo.

        Prefer: iniciar_turno() para o fluxo novo.
        """
        from core.sky.chat.textual_ui.widgets.bubbles.user_bubble import UserBubble
        bubble = UserBubble(texto)
        self.mount(bubble)
        self.call_later(self.scroll_end)

    def adicionar_mensagem_sky(self, texto: str) -> None:
        """
        [LEGADO] Adiciona mensagem da Sky sem fechar um Turn.

        Prefer: turn.set_response() para o fluxo novo.
        """
        from core.sky.chat.textual_ui.widgets.bubbles.sky_bubble import SkyBubble
        bubble = SkyBubble(texto)
        self.mount(bubble)
        self.call_later(self.scroll_end)

    def adicionar_mensagem(self, texto: str) -> None:
        """[LEGADO] Mensagem simples sem bubble."""
        self.mount(Static(texto))
        self.call_later(self.scroll_end)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def limpar(self) -> None:
        """Remove todos os widgets filhos (limpa a sessão)."""
        self.remove_children()

    @property
    def turn_count(self) -> int:
        """Número de turnos na sessão atual."""
        return len(self.query(Turn))


__all__ = ["ChatScroll"]
