# coding: utf-8
"""
Widgets customizados para a UI Textual.

Nova estrutura organizada:
- header/: Componentes do header (título, contexto, métricas)
- bubbles/: Bolhas de mensagem (SkyBubble, UserBubble)
- content/: Conteúdo principal (thinking, turn)
- content/agentic_loop/: Componentes do loop agentic ReAct
- common/: Widgets genéricos (toast, modal, overlay, log)
- scroll/: Containers de scroll customizados
- chat_text_area.py: Widget de input (único na raiz)
- recording_mixin.py: Mixin de gravação
"""

# =============================================================================
# Header
# =============================================================================
from core.sky.chat.textual_ui.widgets.header import ChatHeader
from core.sky.chat.textual_ui.widgets.header.title import AnimatedTitle, TitleStatic
from core.sky.chat.textual_ui.widgets.header.title.history import TitleHistory, TitleEntry
from core.sky.chat.textual_ui.widgets.header.title.history_dialog import TitleHistoryDialog, HistoryEntryItem
from core.sky.chat.textual_ui.widgets.header.animated_verb import (
    EstadoLLM,
    AnimatedVerb,
    EstadoModal,
)
from core.sky.chat.textual_ui.widgets.header.context_bar import ContextBar

# =============================================================================
# Bubbles
# =============================================================================
from core.sky.chat.textual_ui.widgets.bubbles.sky_bubble import SkyBubble, ActionBar
from core.sky.chat.textual_ui.widgets.bubbles.user_bubble import UserBubble
from core.sky.chat.textual_ui.widgets.bubbles.bubble_separator import TurnSeparator

# =============================================================================
# Content - Thinking
# =============================================================================
from core.sky.chat.textual_ui.widgets.content.thinking import (
    ThinkingIndicator,
    ThinkingPanel,
)

# =============================================================================
# Content - AgenticLoop (ReAct)
# =============================================================================
from core.sky.chat.textual_ui.widgets.content.agentic_loop.panel import AgenticLoopPanel
from core.sky.chat.textual_ui.widgets.content.agentic_loop.step import StepWidget
from core.sky.chat.textual_ui.widgets.content.agentic_loop.thought import ThoughtLine, ThoughtLineMarkdown
from core.sky.chat.textual_ui.widgets.content.agentic_loop.action import ActionLine
from core.sky.chat.textual_ui.widgets.content.agentic_loop.tool_call import ToolCallWidget, SimpleEntryWidget
from core.sky.chat.textual_ui.widgets.content.agentic_loop.tool_feedback import (
    ToolFeedback,
    ToolStatus,
    ToolInfo,
)

# =============================================================================
# Content - Turn
# =============================================================================
from core.sky.chat.textual_ui.widgets.content.turn import (
    Turn,
    TurnState,
    ThinkingEntry,
)

# =============================================================================
# Common
# =============================================================================
from core.sky.chat.textual_ui.widgets.common.toast import ToastNotification
from core.sky.chat.textual_ui.widgets.common.modal import ConfirmModal
from core.sky.chat.textual_ui.widgets.common.overlay import OverlayContainer
from core.sky.chat.textual_ui.widgets.common.log import ChatLog

# =============================================================================
# Scroll
# =============================================================================
from core.sky.chat.textual_ui.widgets.scroll.chat_scroll import ChatScroll

# =============================================================================
# Raiz (widgets únicos)
# =============================================================================
from core.sky.chat.textual_ui.widgets.chat_text_area import ChatTextArea
from core.sky.chat.textual_ui.widgets.recording_mixin import RecordingToggleMixin

__all__ = [
    # Header
    "ChatHeader",
    "AnimatedTitle",
    "TitleStatic",
    "TitleHistory",
    "TitleEntry",
    "TitleHistoryDialog",
    "HistoryEntryItem",
    "EstadoLLM",
    "AnimatedVerb",
    "EstadoModal",
    "ContextBar",
    # Bubbles
    "SkyBubble",
    "ActionBar",
    "UserBubble",
    "TurnSeparator",
    # Content - Thinking
    "ThinkingIndicator",
    "ThinkingPanel",
    # Content - AgenticLoop
    "AgenticLoopPanel",
    "StepWidget",
    "ThoughtLine",
    "ThoughtLineMarkdown",
    "ActionLine",
    "ToolCallWidget",
    "SimpleEntryWidget",
    "ToolFeedback",
    "ToolStatus",
    "ToolInfo",
    # Content - Turn
    "Turn",
    "TurnState",
    "ThinkingEntry",
    # Common
    "ToastNotification",
    "ConfirmModal",
    "OverlayContainer",
    "ChatLog",
    # Scroll
    "ChatScroll",
    # Raiz
    "ChatTextArea",
    "RecordingToggleMixin",
]
