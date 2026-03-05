# coding: utf-8
"""
POC: UI Textual do Sky Chat - Prova de Conceito

Este arquivo serve como ponto de partida para entender o fluxo
da interface Textual TUI do zero, sem dependências complexas.

FLUXO BÁSICO:
1. App (TextualApp) → gerencia a aplicação
2. WelcomeScreen → tela de apresentação
3. ChatScreen → tela principal do chat
4. Widgets → componentes visuais (bubbles, input, etc.)

ESTRUTURA DE SCREENS:
--------------------

# App (container principal)
#   ├─ WelcomeScreen (primeira tela)
#   │   └─ Input → usuário digita mensagem
#   └─ ChatScreen (tela do chat)
#       ├─ Header (título + métricas)
#       ├─ ScrollView (mensagens)
#       │   ├─ UserBubble (mensagem do usuário)
#       │   ├─ SkyBubble (resposta da Sky)
#       │   └─ ThinkingIndicator (animação)
#       └─ Footer (input field)

MÉTODOS IMPORTANTES:
--------------------

# App:
#   - run() → inicia o loop da TUI
#   - push_screen(screen) → navega entre telas

# Screen:
#   - compose() → define o layout (yield widgets)
#   - on_mount() → chamado quando screen é montada
#   - on_input_submitted(event) → chamado ao enviar input

# Widget:
#   - mount(widget) → adiciona widget filho
#   - query_one("#id") → busca widget por ID
#   - scroll_end() → scroll para o final

FLUXO DE MENSAGEM:
------------------

# 1. Usuário digita no Footer/Input
# 2. on_input_submitted() é chamado
# 3. process_message() → cria UserBubble e exibe
# 4. Worker assíncrono → gera resposta
# 5. SkyBubble → exibe resposta

# Exemplo de fluxo simples:

# class ChatScreen(Screen):
#     def compose(self):
#         yield Header()  # topo
#         yield ScrollView()  # meio
#         yield Footer()  # fundo
#
#     def on_input_submitted(self, event):
#         scroll = self.query_one(ScrollView)
#         scroll.mount(Static(f"Você: {event.value}"))
#         scroll.mount(Static(f"Sky: Resposta..."))
#         scroll.scroll_end()

DEBUG:
-------

# Para debug, use prints estratégicos:
# - print("CHEGUEI AQUI") → marca que o código foi executado
# - print(f"Valor: {variavel}") → mostra valor de variável
# - try/except → captura erros com traceback

# PRÓXIMOS PASSOS:
# 1. Criar App mínima que inicia
# 2. Criar WelcomeScreen com Input
# 3. Criar ChatScreen que mostra mensagens
# 4. Testar fluxo completo

"""
from .app import PocApp

if __name__ == "__main__":
    app = PocApp()
    app.run()