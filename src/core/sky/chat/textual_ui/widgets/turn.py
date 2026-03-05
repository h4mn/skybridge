# coding: utf-8
"""
Turn - Entidade de turno da conversa.

Um turno representa a unidade atômica da conversa:
  TurnSeparator (se não for o primeiro turno)
  UserBubble    (pergunta do usuário)
  ThinkingIndicator (enquanto processa)
  ThinkingPanel (painel de pensamento colapsável - PRD019 Fase 2)
  ToolFeedback  (opcional, montado dinamicamente)
  SkyBubble     (resposta final, atualizado incrementalmente com streaming)

O ChatScroll gerencia a lista de Turn. O ChatScreen
abre um turno e o fecha ao receber a resposta.

Streaming (PRD019 Fase 1):
- append_response() adiciona texto incrementalmente ao SkyBubble
- SkyBubble é criado preguiçosamente no primeiro append_response()
- watch_content do Textual atualiza automaticamente

Thinking UI (PRD019 Fase 2):
- ThinkingPanel mostra processo de pensamento da Sky
- add_thinking_entry() adiciona entradas ao ThinkingPanel
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING

from textual.message import Message

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from core.sky.chat.textual_ui.widgets.bubbles import SkyBubble, UserBubble
from core.sky.chat.textual_ui.widgets.thinking import ThinkingIndicator, ThinkingPanel, ToolCallWidget

# Type hints
if TYPE_CHECKING:
    pass  # type: ignore


# =============================================================================
# Evento Personalizado: ChatRetry
# =============================================================================

class ChatRetry(Message):
    """
    Evento disparado quando o usuário clica no botão Retry.

    Contém a mensagem original do usuário para reprocessamento.

    O Textual automaticamente chama o handler on_chat_retry no ChatScreen.
    """
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message


@dataclass
class ThinkingEntry:
    """
    Entrada de pensamento para ThinkingPanel.

    Attributes:
        type: Tipo de entrada (thought, tool_start, tool_result, error).
        timestamp: Quando a entrada foi criada.
        content: Conteúdo da entrada.
        metadata: Metadados adicionais (nome da ferramenta, status, etc).
    """
    type: str  # "thought", "tool_start", "tool_result", "error"
    timestamp: datetime
    content: str
    metadata: dict | None = None


class TurnState(Enum):
    """Estado do ciclo de vida de um turno."""
    PENDING    = auto()   # UserBubble adicionado, aguardando resposta
    THINKING   = auto()   # Worker rodando (ThinkingIndicator visível)
    DONE       = auto()   # SkyBubble adicionado com sucesso
    ERROR      = auto()   # SkyBubble adicionado com mensagem de erro
    CANCELLED  = auto()   # PRD-REACT-001: Turno interrompido pelo usuário


class TurnSeparator(Static):
    """
    Separador visual entre turnos consecutivos.

    Linha pontilhada sutil que delimita onde
    termina um turno e começa o próximo.
    """

    DEFAULT_CSS = """
    TurnSeparator {
        height: 1;
        width: 100%;
        color: $text-muted;
        text-align: center;
        margin: 0 2;
        padding: 0;
    }
    """

    def __init__(self) -> None:
        # "╌" × 60 — visível mas não intrusivo
        super().__init__("╌" * 60)


class Turn(Widget):
    """
    Unidade atômica da conversa: pergunta + resposta.

    Ciclo de vida:
      1. Criado com a mensagem do usuário (PENDING)
      2. ChatScreen chama set_thinking() ao iniciar worker (THINKING)
      3. ChatScreen chama set_response() ao receber resposta (DONE)
         ou set_error() se o worker falhar (ERROR)

    Separador só aparece a partir do segundo turno.
    """

    DEFAULT_CSS = """
    Turn {
        height: auto;
        width: 100%;
        padding: 0;
        margin: 0;
    }
    """

    def __init__(self, user_message: str, turn_number: int) -> None:
        """
        Inicializa Turn.

        Args:
            user_message: Texto enviado pelo usuário.
            turn_number:  Índice 1-based do turno na sessão.
        """
        super().__init__()
        self._user_message = user_message
        self._turn_number  = turn_number
        self._state        = TurnState.PENDING

        # Streaming: SkyBubble criado preguiçosamente no primeiro append_response
        self._sky_bubble: SkyBubble | None = None

        # Thinking UI: ThinkingPanel criado em start_thinking()
        self._thinking_panel: ThinkingPanel | None = None
        self._thinking_entries: list[ThinkingEntry] = []

        # PRD-REACT-001: AgenticLoopPanel para padrão ReAct
        self._agentic_loop_panel = None  # type: ignore

    # ------------------------------------------------------------------
    # Composição
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        """
        Estrutura inicial do turno.

        Sem separador - UserBubble já tem visual interessante para separar turnos.
        ThinkingIndicator já montado mas oculto — fica visível
        em on_mount, quando o DOM já está pronto.
        """
        yield UserBubble(self._user_message)
        yield ThinkingIndicator()   # oculto por padrão (display=False)

    def on_mount(self) -> None:
        """DOM pronto — ativa o ThinkingIndicator imediatamente."""
        self._state = TurnState.THINKING
        # Proteção: ThinkingIndicator pode não estar pronto ainda
        try:
            self.query_one(ThinkingIndicator).show()
        except Exception:
            pass  # Será ativado em set_thinking() se necessário

    # ------------------------------------------------------------------
    # API pública — chamada pelo ChatScreen
    # ------------------------------------------------------------------

    def set_thinking(self) -> None:
        """
        Torna o ThinkingIndicator visível.

        Mantido para chamada explícita externa se necessário.
        No fluxo normal, on_mount já faz isso automaticamente.
        """
        self._state = TurnState.THINKING
        self.query_one(ThinkingIndicator).show()

    def set_response(self, text: str) -> None:
        """
        Remove o ThinkingIndicator e adiciona a resposta da Sky.

        Args:
            text: Texto de resposta gerado pelo Claude.
        """
        self._state = TurnState.DONE
        # Remove ThinkingIndicator se ainda presente
        try:
            self.query_one(ThinkingIndicator).remove()
        except Exception:
            pass  # Já foi removido no append_response
        self.mount(SkyBubble(text))

    def set_error(self, error: str) -> None:
        """
        Remove o ThinkingIndicator e adiciona bubble de erro.

        Args:
            error: Mensagem de erro amigável.
        """
        self._state = TurnState.ERROR
        # Remove ThinkingIndicator se ainda presente
        try:
            self.query_one(ThinkingIndicator).remove()
        except Exception:
            pass  # Já foi removido no append_response

        self.mount(SkyBubble(f"❌ {error}"))

    def set_cancelled(self) -> None:
        """
        PRD-REACT-001: Marca o turno como cancelado pelo usuário.

        Remove ThinkingIndicator e congela AgenticLoopPanel se existir.
        UserBubble é preservado no histórico.
        """
        self._state = TurnState.CANCELLED

        # Remove ThinkingIndicator se ainda presente
        try:
            self.query_one(ThinkingIndicator).remove()
        except Exception:
            pass

        # Congela ThinkingPanel se existir (compatibilidade)
        if self._thinking_panel is not None:
            self._thinking_panel.collapse_done()

        # PRD-REACT-001: Congela AgenticLoopPanel se existir
        if hasattr(self, "_agentic_loop_panel") and self._agentic_loop_panel is not None:
            self._agentic_loop_panel.freeze()

    # ------------------------------------------------------------------
    # API de Streaming (PRD019 Fase 1)
    # ------------------------------------------------------------------

    async def append_response(self, text: str) -> None:
        """
        Adiciona texto incrementalmente ao SkyBubble durante streaming.

        Cria o SkyBubble preguiçosamente no primeiro chamado.
        O watch_content do Textual atualiza automaticamente a UI.

        Args:
            text: Chunk de texto para adicionar à resposta.
        """
        # Cria SkyBubble preguiçosamente no primeiro chunk
        if self._sky_bubble is None:
            # Remove ThinkingIndicator se ainda presente
            try:
                self.query_one(ThinkingIndicator).remove()
            except Exception:
                pass  # Já foi removido

            # PRD-REACT-001: NÃO colapsa mais - deixa expandido para visualização
            # Comentado para papai ver como está ficando
            # if hasattr(self, "_agentic_loop_panel") and self._agentic_loop_panel is not None:
            #     self._agentic_loop_panel.collapse_done()

            # Passa o AgenticLoopPanel para dentro do SkyBubble
            self._sky_bubble = SkyBubble(
                "",
                agentic_panel=self._agentic_loop_panel,
                parent_turn=self
            )
            self.mount(self._sky_bubble)

        # Adiciona texto ao conteúdo existente
        # O reactive em SkyBubble.content aciona watch_content automaticamente
        # que dispara scroll no ChatScroll
        self._sky_bubble.content += text

    # ------------------------------------------------------------------
    # PRD-REACT-001: API de Agentic Loop (ReAct)
    # ------------------------------------------------------------------

    def start_agentic_loop(self) -> None:
        """
        PRD-REACT-001: Inicia o painel AgenticLoopPanel.

        Substitui ThinkingPanel pelo novo AgenticLoopPanel que agrupa Steps.
        Remove ThinkingIndicator do Turn pois o painel tem seu próprio indicador.

        IMPORTANTE: O painel é montado imediatamente para que add_step() funcione.
        Depois ele é movido para dentro do SkyBubble via compose().
        """
        # Se já existe AgenticLoopPanel, não recria
        if hasattr(self, "_agentic_loop_panel") and self._agentic_loop_panel is not None:
            return

        from core.sky.chat.textual_ui.widgets.thinking import AgenticLoopPanel

        # Remove ThinkingIndicator do Turn - o AgenticLoopPanel tem o seu próprio
        try:
            self.query_one(ThinkingIndicator).remove()
        except Exception:
            pass  # Já foi removido ou não existe

        # Cria e monta o AgenticLoopPanel imediatamente
        # Isso permite que add_step() funcione via query_one()
        self._agentic_loop_panel = AgenticLoopPanel(parent_turn=self)
        self.mount(self._agentic_loop_panel)

    async def add_thought(self, thought_text: str) -> None:
        """
        PRD-REACT-001: Adiciona um Step com Thought ao AgenticLoopPanel.

        Args:
            thought_text: Texto de pensamento (intenção antes da ação).
        """
        if hasattr(self, "_agentic_loop_panel") and self._agentic_loop_panel is not None:
            await self._agentic_loop_panel.add_step(thought=thought_text)

    async def add_action(self, tool_name: str, param: str, input_json: str = "") -> None:
        """
        PRD-REACT-001: Adiciona uma Action ao último Step pendente.

        Args:
            tool_name: Nome da ferramenta.
            param: Parâmetro principal.
            input_json: JSON de input completo da tool (para extrair diff).
        """
        if hasattr(self, "_agentic_loop_panel") and self._agentic_loop_panel is not None:
            # Obtém o último Step pendente
            step = self._agentic_loop_panel.get_last_pending_step()
            if step is None:
                # Se não há Step pendente, cria um sem Thought
                step = await self._agentic_loop_panel.add_step()

            if step:
                step.set_action(tool_name, param)

                # Monta DiffWidget se a tool for Edit/Write e tiver old/new
                if tool_name in ("Edit", "Write", "str_replace") and input_json:
                    import json
                    try:
                        data = json.loads(input_json)
                        old = data.get("old_string") or data.get("old_content", "")
                        new = data.get("new_string") or data.get("new_content", "")
                        file_path = (
                            data.get("path")
                            or data.get("file_path")
                            or data.get("file", "")
                        )
                        if old or new:  # Write pode não ter old
                            step.set_diff(old, new, file_path)
                    except Exception:
                        pass  # JSON inválido — ignora silenciosamente

    def resolve_action(
        self,
        result_summary: str,
        full_output: str = "",
        exit_code: int | None = None,
        command: str = "",
    ) -> None:
        """
        PRD-REACT-001: Resolve a última Action pendente com resultado.

        Args:
            result_summary: Resumo curto para a ActionLine.
            full_output:    Output completo do Bash (para BashResultWidget).
            exit_code:      Código de saída do Bash.
            command:        Comando executado.
        """
        if hasattr(self, "_agentic_loop_panel") and self._agentic_loop_panel is not None:
            step = self._agentic_loop_panel.get_last_pending_step()
            if step:
                step.set_result(
                    result_summary,
                    full_output=full_output,
                    exit_code=exit_code,
                    command=command,
                )
                self.trigger_scroll()

    def finalize_agentic_loop(self) -> None:
        """
        PRD-REACT-001: Finaliza o AgenticLoopPanel ao receber resposta final.

        NÃO colapsa mais - deixa expandido para papai ver como está ficando.
        """
        # Comentado para papai visualizar
        # if hasattr(self, "_agentic_loop_panel") and self._agentic_loop_panel is not None:
        #     self._agentic_loop_panel.collapse_done()
        pass

    def trigger_scroll(self) -> None:
        """
        Dispara scroll automático no ChatScroll pai.

        Chamado pelo AgenticLoopPanel quando há atualizações
        (Steps adicionados, ActionLines atualizadas).
        """
        try:
            # Busca o ChatScroll pai
            chat_scroll = self.query_one("#container", ChatScroll)
            # Usa call_later para evitar problemas de threading
            chat_scroll.call_later(chat_scroll.scroll_end)
        except Exception:
            # ChatScroll não encontrado ou não disponível
            pass

    def show_retry_action(self) -> None:
        """
        PRD-REACT-001: Mostra ActionBar com botão Retry associada ao SkyBubble.

        A ActionBar fica FORA do SkyBubble, logo após ele.
        """
        if self._sky_bubble is not None:
            # Cria callback de retry que reenvia a mensagem do usuário
            def retry_callback() -> None:
                # Dispara evento ChatRetry que o ChatScreen vai tratar
                # Usa self.post_message para permitir bubbling até o ChatScreen
                self.post_message(ChatRetry(self._user_message))

            # Monta aActionBar FORA do SkyBubble, logo após ele
            from core.sky.chat.textual_ui.widgets.bubbles import ActionBar
            self.mount(ActionBar(on_copy=None, on_retry=retry_callback, retry_enabled=True))

    # ------------------------------------------------------------------
    # API de Thinking UI (PRD019 Fase 2)
    # ------------------------------------------------------------------

    async def add_thinking_entry(self, entry: ThinkingEntry) -> None:
        """
        Adiciona ou resolve entrada no ThinkingPanel.

        Lógica de pareamento:
          - tool_start  → cria ToolCallWidget pendente
          - tool_result → resolve o último widget pendente com esse nome
          - thought/error → cria SimpleEntryWidget

        Args:
            entry: ThinkingEntry com conteúdo da entrada.
        """
        # Armazena entrada
        self._thinking_entries.append(entry)

        if self._thinking_panel is None:
            return

        if entry.type == "tool_start":
            # Extrai tool_name do metadata (ou do content como fallback)
            tool_name = (entry.metadata or {}).get("tool", "tool")
            # param é o que vem depois de "ToolName: " no content
            param = entry.content
            if ": " in entry.content:
                param = entry.content.split(": ", 1)[1]
            await self._thinking_panel.add_tool_call(tool_name, param, entry.timestamp)

        elif entry.type == "tool_result":
            # Resolve o widget pendente correspondente
            tool_name = (entry.metadata or {}).get("tool", "")
            result_summary = entry.content
            if not self._thinking_panel.resolve_tool(tool_name, result_summary):
                # Fallback: adiciona como linha simples se não encontrou pair
                await self._thinking_panel.add_simple_entry("thought", result_summary)

        else:
            # thought ou error — linha simples
            await self._thinking_panel.add_simple_entry(entry.type, entry.content)

    def start_thinking(self) -> None:
        """
        Inicia o painel de pensamento (Fase 2).

        Cria o ThinkingPanel expandido por padrão.
        """
        # Se já existe, não recria
        if self._thinking_panel is not None:
            return

        # Cria o ThinkingPanel
        self._thinking_panel = ThinkingPanel()
        self.mount(self._thinking_panel)

        # Adiciona entradas já coletadas (se houver)
        for entry in self._thinking_entries:
            self.call_from_thread(
                lambda e=entry: self._thinking_panel.add_entry(e)  # type: ignore
            )

    def finalize_thinking(self) -> None:
        """
        Finaliza o painel de pensamento ao completar resposta.

        Colapsa o painel e atualiza o título com o total de ações.
        Permanece acessível para o usuário expandir manualmente.
        """
        if self._thinking_panel is not None:
            self._thinking_panel.collapse_done()

    # ------------------------------------------------------------------
    # Propriedades
    # ------------------------------------------------------------------

    @property
    def state(self) -> TurnState:
        """Estado atual do turno."""
        return self._state

    @property
    def turn_number(self) -> int:
        """Número do turno (1-based)."""
        return self._turn_number

    @property
    def user_message(self) -> str:
        """Mensagem original do usuário."""
        return self._user_message

    @property
    def is_cancelled(self) -> bool:
        """PRD-REACT-001: Retorna True se o turno foi cancelado."""
        return self._state == TurnState.CANCELLED


__all__ = [
    "Turn",
    "TurnState",
    "TurnSeparator",
    "ThinkingEntry",
    "ChatRetry",  # PRD-REACT-001: Evento de retry
]
