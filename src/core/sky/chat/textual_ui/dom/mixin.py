# coding: utf-8
"""
SkyWidgetMixin - Mixin para auto-registro de widgets no SkyTextualDOM.

Adicione este mixin a widgets Textual para registro automático:

    class MyWidget(Static, SkyWidgetMixin):
        pass

O widget será registrado automaticamente no on_mount() e desregistrado no on_unmount().
"""

from textual.widget import Widget

from core.sky.chat.textual_ui.dom import SkyTextualDOM


class SkyWidgetMixin:
    """
    Mixin para auto-registro de widgets no SkyTextualDOM.

    Atributos:
        _dom_id: ID customizado (opcional, gerado automaticamente se None)
        _dom_registered: Se o widget está registrado no DOM

    O widget será registrado automaticamente quando montado e desregistrado
    quando desmontado.
    """

    _dom_id: str | None = None
    _dom_registered: bool = False
    _dom_node = None  # Referência para DOMNode (após registro)

    def on_mount(self) -> None:
        """
        Auto-registra o widget no SkyTextualDOM.

        Este método é chamado pelo Textual quando o widget é montado.
        """
        # Chamar on_mount da classe base se existir
        try:
            super().on_mount()
        except AttributeError:
            pass

        # Registrar no DOM
        if not self._dom_registered:
            self._dom_node = SkyTextualDOM().register(
                self, parent=self._get_dom_parent(), dom_id=self._dom_id
            )
            self._dom_id = self._dom_node.dom_id
            self._dom_registered = True

    def on_unmount(self) -> None:
        """
        Auto-desregistra o widget do SkyTextualDOM.

        Este método é chamado pelo Textual quando o widget é desmontado.
        """
        # Chamar on_unmount da classe base se existir
        try:
            super().on_unmount()
        except AttributeError:
            pass

        # Desregistrar do DOM
        if self._dom_registered and self._dom_id:
            SkyTextualDOM().unregister(self._dom_id)
            self._dom_registered = False

    def _get_dom_parent(self) -> Widget | None:
        """
        Retorna o widget pai se também estiver registrado no DOM.

        Returns:
            Widget pai ou None
        """
        if hasattr(self, "parent") and isinstance(self.parent, Widget):
            return self.parent
        return None

    def get_dom_node(self):
        """
        Retorna o DOMNode deste widget (se registrado).

        Returns:
            DOMNode ou None se não registrado
        """
        return self._dom_node


# Typing helper
def is_dom_widget(widget: Widget) -> bool:
    """
    Verifica se um widget tem o SkyWidgetMixin.

    Args:
        widget: Widget Textual

    Returns:
        True se widget usa SkyWidgetMixin
    """
    return isinstance(widget, SkyWidgetMixin)


__all__ = ["SkyWidgetMixin", "is_dom_widget"]
