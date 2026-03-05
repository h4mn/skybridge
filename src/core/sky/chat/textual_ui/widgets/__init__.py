# coding: utf-8
"""
Widgets customizados para a UI Textual.

Bubbles, AnimatedTitle, ThinkingIndicator, ToolFeedback, Toast, etc.
"""

from core.sky.chat.textual_ui.widgets.bubbles import SkyBubble, UserBubble
from core.sky.chat.textual_ui.widgets.title import AnimatedTitle, TitleStatic
from core.sky.chat.textual_ui.widgets.title_history import TitleHistory, TitleEntry
from core.sky.chat.textual_ui.widgets.title_history_dialog import TitleHistoryDialog, HistoryEntryItem
from core.sky.chat.textual_ui.widgets.header import ChatHeader
from core.sky.chat.textual_ui.widgets.thinking import (
    ThinkingIndicator,
    ThinkingPanel,
    ToolCallWidget,
    SimpleEntryWidget,
    StepWidget,
    AgenticLoopPanel,
    ThoughtLine,
    ThoughtLineMarkdown,
    ActionLine,
)
from core.sky.chat.textual_ui.widgets.tool_feedback import (
    ToolFeedback,
    ToolStatus,
    ToolInfo,
)
from core.sky.chat.textual_ui.widgets.toast import ToastNotification
from core.sky.chat.textual_ui.widgets.modal import ConfirmModal

# Novos widgets
from core.sky.chat.textual_ui.widgets.animated_verb import (
    EstadoLLM,
    AnimatedVerb,
    EstadoModal,
)
from core.sky.chat.textual_ui.widgets.chat_text_area import ChatTextArea
from core.sky.chat.textual_ui.widgets.chat_log import ChatLog
from core.sky.chat.textual_ui.widgets.chat_scroll import ChatScroll
from core.sky.chat.textual_ui.widgets.context_bar import ContextBar
from core.sky.chat.textual_ui.widgets.overlay_container import OverlayContainer
from core.sky.chat.textual_ui.widgets.turn import (
    Turn,
    TurnState,
    TurnSeparator,
    ThinkingEntry,
)

__all__ = [
    # Original
    "SkyBubble",
    "UserBubble",
    "AnimatedTitle",
    "TitleStatic",
    "ChatHeader",
    # Thinking UI
    "ThinkingIndicator",
    "ThinkingPanel",
    "ToolCallWidget",
    "SimpleEntryWidget",
    # PRD-REACT-001: novos componentes ReAct
    "ThoughtLine",
    "ThoughtLineMarkdown",
    "ActionLine",
    "StepWidget",
    "AgenticLoopPanel",
    # Tool Feedback
    "ToolFeedback",
    "ToolStatus",
    "ToolInfo",
    # Toast e Modal
    "ToastNotification",
    "ConfirmModal",
    # Novos
    "EstadoLLM",
    "AnimatedVerb",
    "EstadoModal",
    "ChatTextArea",
    "ChatLog",
    "ChatScroll",
    "ContextBar",
    "OverlayContainer",
    # Title History
    "TitleHistory",
    "TitleEntry",
    "TitleHistoryDialog",
    "HistoryEntryItem",
    # P1 — Turnos
    "Turn",
    "TurnState",
    "TurnSeparator",
    # Turn internals
    "ThinkingEntry",
]
