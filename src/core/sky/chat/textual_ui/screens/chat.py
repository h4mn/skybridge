# coding: utf-8
"""
Screen principal do chat Sky.

P1: Turn como entidade (TurnSeparator + ThinkingIndicator conectados).
P3: Header com métricas dinâmicas após cada resposta.
P4: Título gerado por LLM a cada 3 turnos completos.
PRD027: Integração com comandos de voz (/voice, /tts, /stt).
"""

import asyncio
import random
from datetime import datetime

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer
from textual import work

from core.sky.chat.textual_ui.widgets import (
    ChatTextArea,
    ChatLog,
    ChatScroll,
)
from core.sky.chat.textual_ui.widgets.header import ChatHeader
from core.sky.chat.logging import ChatLogger
from core.sky.chat.textual_ui.widgets.animated_verb import AnimatedVerb, EstadoLLM, conjugar_passado
from core.sky.chat.textual_ui.widgets.turn import Turn, ThinkingEntry

# Integração com engine
from core.sky.chat.claude_chat import ClaudeChatAdapter, ChatMessage, get_claude_model, StreamEvent, StreamEventType
from core.sky.memory import get_memory

# PRD027: Comandos de voz
from core.sky.chat.textual_ui.commands import Command, CommandType
from core.sky.chat.textual_ui.voice_commands import (
    execute_stt_command,
    execute_tts_command,
    execute_voice_command,
    get_voice_handler,
)


# =============================================================================
# Verbos de Teste — Amostra variada para validação visual
#
# Formato: ("rótulo", EstadoLLM(verbo="X", predicado="texto completo (2+ palavras)"))
#
# DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
# Cada entrada forma título "Sky verbo predicado" com frase completa fluida.
# =============================================================================
_VERBOS_TESTE: list[tuple[str, EstadoLLM]] = [
    ("analisando",   EstadoLLM(verbo="analisando", predicado="estrutura do projeto", certeza=0.7, esforco=0.5, emocao="pensando", direcao=1)),
    ("codando",      EstadoLLM(verbo="codando", predicado="implementação de widgets", certeza=0.9, esforco=0.8, emocao="debugando", direcao=1)),
    ("refletindo",   EstadoLLM(verbo="refletindo", predicado="melhor abordagem possível", certeza=0.4, esforco=0.3, emocao="em_duvida", direcao=-1)),
    ("criando",      EstadoLLM(verbo="criando", predicado="novos componentes Textual", certeza=0.85, esforco=0.9, emocao="empolgado", direcao=1)),
    ("buscando",     EstadoLLM(verbo="buscando", predicado="informações relevantes", certeza=0.6, esforco=0.6, emocao="curioso", direcao=1)),
    ("corrigindo",   EstadoLLM(verbo="corrigindo", predicado="bugs críticos no sistema", certeza=0.75, esforco=0.7, emocao="cuidadoso", direcao=-1)),
    ("finalizando",  EstadoLLM(verbo="finalizando", predicado="tarefas pendentes hoje", certeza=0.95, esforco=0.4, emocao="concluindo", direcao=1)),
    ("correndo",     EstadoLLM(verbo="correndo", predicado="contra o prazo limite", certeza=0.5, esforco=1.0, emocao="urgente", direcao=1)),
    ("sonhando",     EstadoLLM(verbo="sonhando", predicado="novas ideias para o futuro", certeza=0.3, esforco=0.2, emocao="pensando", direcao=1)),
    ("pilotando",    EstadoLLM(verbo="pilotando", predicado="esta arquitetura complexa", certeza=0.88, esforco=0.65, emocao="neutro", direcao=1)),
]

# =============================================================================
# Inferência de EstadoLLM a partir da mensagem do usuário
# =============================================================================

_ESTADOS_POR_PADRAO: list[tuple[list[str], EstadoLLM]] = [
    # Debugging / erros
    (["erro", "bug", "falha", "crash", "exception", "quebr", "não funciona", "problema"],
     EstadoLLM(verbo="debugando", predicado="problema reportado", certeza=0.7, esforco=0.8, emocao="debugando", direcao=-1)),
    # Código / implementação
    (["código", "implementa", "cria", "escreve", "função", "class", "script", "módulo", "arquivo"],
     EstadoLLM(verbo="codando", predicado="nova funcionalidade", certeza=0.85, esforco=0.9, emocao="empolgado", direcao=1)),
    # Busca / exploração
    (["busca", "encontra", "lista", "mostra", "quais", "onde", "explora", "lê", "readme", "estrutura"],
     EstadoLLM(verbo="buscando", predicado="informações no código", certeza=0.7, esforco=0.6, emocao="curioso", direcao=1)),
    # Análise / entendimento
    (["analisa", "entende", "explica", "como funciona", "o que é", "por que", "diferença"],
     EstadoLLM(verbo="analisando", predicado="o contexto atual", certeza=0.6, esforco=0.7, emocao="pensando", direcao=1)),
    # Refatoração / melhoria
    (["refatora", "melhora", "otimiza", "limpa", "organiza", "renomeia", "move"],
     EstadoLLM(verbo="refatorando", predicado="estrutura do código", certeza=0.75, esforco=0.7, emocao="cuidadoso", direcao=-1)),
    # Testes
    (["test", "testa", "verifica", "valida", "confirma", "checa"],
     EstadoLLM(verbo="testando", predicado="comportamento do sistema", certeza=0.8, esforco=0.6, emocao="cuidadoso", direcao=1)),
    # Deploy / execução
    (["executa", "roda", "instala", "deploy", "publica", "bash", "comando", "terminal"],
     EstadoLLM(verbo="executando", predicado="comando solicitado", certeza=0.8, esforco=0.85, emocao="urgente", direcao=1)),
    # Documentação / texto
    (["documenta", "escreve", "redige", "resumo", "explica", "markdown", "readme"],
     EstadoLLM(verbo="escrevendo", predicado="documentação técnica", certeza=0.85, esforco=0.5, emocao="neutro", direcao=1)),
    # Dúvida / incerteza
    (["não sei", "talvez", "será que", "acho que", "parece", "possível"],
     EstadoLLM(verbo="refletindo", predicado="sobre a melhor abordagem", certeza=0.35, esforco=0.4, emocao="em_duvida", direcao=-1)),
]

_ESTADO_PADRAO = EstadoLLM(verbo="processando", predicado="sua solicitação", certeza=0.6, esforco=0.6, emocao="pensando", direcao=1)


def _inferir_estado(mensagem: str) -> EstadoLLM:
    """
    Infere EstadoLLM a partir do conteúdo da mensagem do usuário.

    Percorre padrões em ordem de prioridade e retorna o primeiro match.
    Fallback para estado genérico de processamento.
    """
    texto = mensagem.lower()
    for palavras, estado in _ESTADOS_POR_PADRAO:
        if any(p in texto for p in palavras):
            return estado
    return _ESTADO_PADRAO


# Prompt para geração de título (P4)
_TITULO_PROMPT = """\
Analise o histórico de conversa abaixo e gere um título curto descritivo.

REGRAS:
- Formato obrigatório: "verbo_gerúndio predicado"
- Exemplo: "debugando erro na API", "aprendendo async Python", "explorando o projeto"
- O verbo deve ser um gerúndio em português (terminado em -ando, -endo ou -indo)
- Máximo 5 palavras no total
- Sem pontuação, aspas ou prefixo "Sky"
- Responda APENAS com o título, sem mais nada

Histórico:
{historico}
"""


class ChatScreen(Screen):
    """
    Screen principal do chat Sky.

    P1: ChatScroll.iniciar_turno() gerencia Turn como entidade.
    P3: Header atualizado com métricas reais após cada resposta.
    P4: Título gerado por LLM a cada 3 turnos.
    """

    BINDINGS = [
        ("ctrl+l", "toggle_log", "Toggle Log"),
        ("ctrl+v", "ciclar_verbo", "Próximo Verbo"),
        ("ctrl+d", "open_devtools", "DevTools"),
        ("escape", "deactivate_voice", "Sair modo voz"),
    ]

    def __init__(self, input: str):
        super().__init__()
        self.input = input
        self._verbo_idx = 0

        # Engine de chat
        self._memory = get_memory()
        self._chat = ClaudeChatAdapter(memory=self._memory)

        # Turno atualmente em andamento
        self._turno_atual: Turn | None = None

        # Contadores de sessão (P3)
        self._turn_count: int = 0
        self._total_tokens_in: int = 0
        self._total_tokens_out: int = 0
        self._last_latency_ms: float = 0.0
        self._total_memories_used: int = 0

        # PRD027: Handler de comandos de voz
        self._voice_handler = get_voice_handler()

    def compose(self) -> ComposeResult:
        yield ChatHeader()
        yield ChatScroll(id="container")
        yield ChatTextArea(
            id="chat_input_textarea",
            placeholder="Digite algo..."
        )
        yield ChatLog()
        yield Footer()

    def on_mount(self) -> None:
        _, estado_inicial = random.choice(_VERBOS_TESTE)
        self.query_one(ChatHeader).update_estado(estado_inicial)

        # Inicializa ChatLogger e conecta ao ChatLog widget
        log_widget = self.query_one(ChatLog)
        self._chat_logger = ChatLogger(
            session_id=f"chat_screen_{id(self)}",
            chat_log_widget=log_widget,
            verbosity="WARNING",
            show_in_ui=True
        )

        # Log inicia fechado (Ctrl+L para toggle)
        log = self.query_one(ChatLog)
        # Não ativa "visible" - começa fechado
        log.evento("Tela montada", self.input)

        textarea = self.query_one("#chat_input_textarea", ChatTextArea)
        textarea.focus()

        self._abrir_turno_e_processar(self.input)

    def on_unload(self) -> None:
        """Chamado quando a tela é descarregada. Restaura stdout/stderr."""
        if hasattr(self, '_chat_logger') and self._chat_logger is not None:
            self._chat_logger.restore()

    def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted) -> None:
        texto = event.value.strip()
        if not texto:
            return

        log = self.query_one(ChatLog)
        log.evento("TextArea submetido", texto)

        self._abrir_turno_e_processar(texto)

    # PRD-REACT-001: Handler para Retry de mensagem
    def on_chat_retry(self, event) -> None:
        """
        Handler para evento de retry (botão Retry no ActionBar).

        Recebe um ChatRetry com a mensagem original do usuário.
        """
        mensagem = event.message if hasattr(event, 'message') else None
        if mensagem:
            log = self.query_one(ChatLog)
            log.evento("Retry solicitado", mensagem)
            self._abrir_turno_e_processar(mensagem)

    # ------------------------------------------------------------------
    # Lógica central
    # ------------------------------------------------------------------

    def _abrir_turno_e_processar(self, mensagem: str) -> None:
        """Abre Turn no ChatScroll e dispara worker."""
        # PRD027: Verifica se é comando de voz antes de processar
        command = Command.parse(mensagem)
        if command is not None:
            self._handle_command(command)
            return

        # Processamento normal de mensagem
        scroll = self.query_one("#container", ChatScroll)
        self._turno_atual = scroll.iniciar_turno(mensagem)
        self._processar_mensagem(mensagem)

    @work(exclusive=True)
    async def _processar_mensagem(self, mensagem: str) -> None:
        """
        Processa mensagem com Claude/RAG usando streaming (PRD019 Fase 1).

        Ao concluir, atualiza métricas (P3) e dispara título se necessário (P4).
        """
        turno = self._turno_atual
        if turno is None:
            return

        try:
            header = self.query_one(ChatHeader)
            log = self.query_one(ChatLog)

            # Verbo: inferido da mensagem — fica visível durante TODO o processamento
            estado_ativo = _inferir_estado(mensagem)
            header.update_estado(estado_ativo)
            log.evento("Verbo inferido", f"{estado_ativo.verbo} ({estado_ativo.emocao})")

            # PRD-REACT-001: Inicia o painel AgenticLoopPanel (padrão ReAct)
            turno.start_agentic_loop()

            # Chama engine com STREAMING (PRD019 Fase 1 + Fase 2)
            message = ChatMessage(role="user", content=mensagem)

            # Loop de streaming: consome StreamEvents
            async for stream_event in self._chat.stream_response(message):
                if stream_event.type == StreamEventType.TEXT:
                    # Chunk de texto normal - adiciona à resposta
                    await turno.append_response(stream_event.content)
                elif stream_event.type == StreamEventType.THOUGHT:
                    # PRD-REACT-001: Thought (intenção antes da ação)
                    await turno.add_thought(stream_event.content)
                elif stream_event.type == StreamEventType.TOOL_START:
                    # PRD-REACT-001: Tool start - cria Action no Step
                    meta = stream_event.metadata or {}
                    tool_name = meta.get("tool", "tool")
                    input_json = meta.get("input", "")
                    # Extrai parâmetro do content (formato "ToolName: param")
                    param = stream_event.content
                    if ": " in param:
                        param = param.split(": ", 1)[1]
                    await turno.add_action(tool_name, param, input_json=input_json)
                elif stream_event.type == StreamEventType.TOOL_RESULT:
                    # PRD-REACT-001: Tool result - resolve Action
                    meta = stream_event.metadata or {}
                    full_output = meta.get("result", "")
                    # LOG: confirma se full_output chegou populado
                    log.evento(
                        "TOOL_RESULT",
                        f"tool={meta.get('tool')} output_len={len(full_output)} exit={meta.get('exit_code')}"
                    )
                    turno.resolve_action(
                        stream_event.content,
                        full_output=full_output,
                        exit_code=meta.get("exit_code"),
                        command=meta.get("command", ""),
                    )
                elif stream_event.type == StreamEventType.ERROR:
                    # Erro - adiciona entrada
                    await turno.add_thinking_entry(ThinkingEntry(
                        type="error",
                        timestamp=datetime.now(),
                        content=stream_event.content,
                        metadata=stream_event.metadata,
                    ))

            # PRD-REACT-001: Ao completar, finaliza o AgenticLoopPanel
            turno.finalize_agentic_loop()

            # PRD-REACT-001: Mostra ActionBar com Retry ao completar
            turno.show_retry_action()

            # --- P3: coleta métricas do adapter ---
            self._turn_count += 1
            self._last_latency_ms = self._chat._last_latency_ms
            self._total_tokens_in += self._chat._last_tokens_in
            self._total_tokens_out += self._chat._last_tokens_out
            history_len = len(self._chat.get_history())

            rag_enabled = self._memory.is_rag_enabled() if hasattr(self._memory, "is_rag_enabled") else False
            memories_used = 0
            if rag_enabled:
                results = self._memory.search(mensagem, top_k=1)
                memories_used = len(results)
                self._total_memories_used += memories_used

            header.update_metricas(
                turn_count=self._turn_count,
                tokens_in=self._total_tokens_in,
                tokens_out=self._total_tokens_out,
                latency_ms=self._last_latency_ms,
                memories_used=self._total_memories_used,
                rag_enabled=rag_enabled,
                model=get_claude_model(),
            )
            header.update_context_bar(history_len)

            # Verbo: conjuga no passado para indicar ação concluída
            # "buscando" → "buscou", "analisando" → "analisou"
            verbo_passado = conjugar_passado(estado_ativo.verbo)
            estado_concluido = EstadoLLM(
                verbo=verbo_passado,
                predicado=estado_ativo.predicado,  # mantém predicado do estado ativo
                certeza=1.0,    # sem oscilação — ação encerrada
                esforco=0.0,    # sweep parado — estado de repouso
                emocao="concluindo",
                direcao=1,
            )
            header.update_estado(estado_concluido)
            log.evento("Verbo concluído", f"{estado_ativo.verbo} → {verbo_passado}")

            # --- P4: dispara geração de título a cada 3 turnos ---
            if self._turn_count % 3 == 0:
                self._gerar_titulo()

        except asyncio.CancelledError:
            # PRD-REACT-001: Usuário cancelou via Ctrl+C
            log = self.query_one(ChatLog)
            log.evento("Cancelamento", "Turno cancelado pelo usuário")
            if turno and not turno.is_cancelled:
                turno.set_cancelled()
        except Exception as e:
            import traceback
            log = self.query_one(ChatLog)
            log.error(f"Erro: {e}")
            log.error(traceback.format_exc())
            # FIX: Passa str(e) explicitamente
            turno.set_error(str(e) if hasattr(e, '__str__') else str(type(e).__name__))

        finally:
            # Cleanup seguro - não falha mesmo se widgets não existirem
            try:
                scroll = self.query_one("#container", ChatScroll)
                scroll.call_later(scroll.scroll_end)
            except Exception:
                pass
            try:
                text_area = self.query_one("#chat_input_textarea", ChatTextArea)
                text_area.focus()
            except Exception:
                pass
            self._turno_atual = None

    # ------------------------------------------------------------------
    # P4 — Geração de título via LLM
    # ------------------------------------------------------------------

    @work(exclusive=False, name="titulo")
    async def _gerar_titulo(self) -> None:
        """
        Gera título da conversa via LLM.

        Roda como worker async independente (exclusive=False) para
        não competir com o worker exclusivo do chat.
        Atualiza o header diretamente ao concluir (mesmo event loop).
        """
        # Guarda: não rodar enquanto há um turno em andamento
        # Evita chamadas SDK concorrentes que podem misturar respostas
        if self._turno_atual is not None:
            return

        historico = self._chat._format_conversation_context()
        if not historico.strip():
            return

        prompt = _TITULO_PROMPT.format(historico=historico[-1500:])

        try:
            # Adapter completamente isolado — _isolated=True garante:
            # 1. Sem acesso ao RAG compartilhado (não contamina buscas futuras)
            # 2. Sem gravação de aprendizados (prompt de título não é aprendizado)
            # 3. Histórico próprio — não polui o histórico da conversa principal
            tmp = ClaudeChatAdapter(_isolated=True)
            titulo_raw = await tmp.respond(ChatMessage(role="user", content=prompt))
            titulo = titulo_raw.strip().strip('"').strip("'").lower()

            if not titulo or len(titulo) > 60:
                return

            # Quebra em verbo + predicado
            partes = titulo.split(" ", 1)
            verbo = partes[0]
            predicado = partes[1] if len(partes) > 1 else "conversa"

            # Mesmo event loop — atualiza diretamente
            header = self.query_one(ChatHeader)
            header.update_title(verbo, predicado)
            self.query_one(ChatLog).evento("Título gerado", titulo)

        except Exception as e:
            # Falha silenciosa — título não é crítico
            # Log para debug
            try:
                self.query_one(ChatLog).error(f"Erro ao gerar título: {e}")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_toggle_log(self) -> None:
        log = self.query_one(ChatLog)
        log.toggle_class("visible")

    def action_ciclar_verbo(self) -> None:
        self._verbo_idx = (self._verbo_idx + 1) % len(_VERBOS_TESTE)
        verbo, estado = _VERBOS_TESTE[self._verbo_idx]
        header = self.query_one(ChatHeader)
        header.update_estado(estado, f"[{self._verbo_idx + 1}/{len(_VERBOS_TESTE)}]")
        log = self.query_one(ChatLog)
        log.evento(f"Verbo #{self._verbo_idx + 1}", f"{verbo} ({estado.emocao})")

    def action_open_devtools(self) -> None:
        """Abre a DevTools Screen."""
        from core.sky.chat.textual_ui.dom.screens import DevToolsScreen
        self.app.push_screen(DevToolsScreen())

    def on_animated_verb_inspecionado(self, event: AnimatedVerb.Inspecionado) -> None:
        """
        Handler para clique no AnimatedVerb.

        Substitui EstadoModal pelo diálogo de histórico completo.
        """
        from core.sky.chat.textual_ui.widgets.title_history_dialog import TitleHistoryDialog
        header = self.query_one(ChatHeader)
        self.app.push_screen(TitleHistoryDialog(header._title_history))

    def action_cancelar_turno(self) -> None:
        """
        PRD-REACT-001: Cancela o turno atualmente em processamento.

        Chamado pelo usuário via Ctrl+C. Marca o turno como CANCELLED
        e encerra o worker graciosamente.
        """
        if self._turno_atual is not None and self._turno_atual.state != TurnState.DONE:
            self._turno_atual.set_cancelled()

            # Notifica o usuário
            log = self.query_one(ChatLog)
            log.evento("Turno cancelado", "Usuário cancelou o processamento")

    # ------------------------------------------------------------------
    # PRD027: Comandos de Voz
    # ------------------------------------------------------------------

    def action_deactivate_voice(self) -> None:
        """Desativa modo voz (pressionar ESC)."""
        if self._voice_handler.is_voice_active:
            self._voice_handler.voice_mode_active = False
            log = self.query_one(ChatLog)
            log.evento("Modo voz", "Desativado via ESC")

            # Mostra toast ao usuário
            self._show_voice_message("🎙️ Modo voz desativado (ESC)")

    async def _handle_command(self, command: Command) -> None:
        """
        Processa comandos especiais (/voice, /tts, /stt, etc).

        Args:
            command: Comando parseado
        """
        log = self.query_one(ChatLog)
        log.evento("Comando detectado", f"{command.type.value}: {command.raw}")

        if command.type == CommandType.STT:
            await self._handle_stt_command(command.raw)
        elif command.type == CommandType.TTS:
            await self._handle_tts_command(command.raw)
        elif command.type == CommandType.VOICE:
            await self._handle_voice_mode_command(command.raw)
        else:
            # Outros comandos (help, new, etc) - processa normalmente
            scroll = self.query_one("#container", ChatScroll)
            self._turno_atual = scroll.iniciar_turno(command.raw)
            await self._processar_mensagem(command.raw)

    async def _handle_stt_command(self, raw_command: str) -> None:
        """
        Processa comando /stt [duração].

        Grava áudio e transcreve, adicionando resultado ao chat.
        """
        # Extrai duração se especificada
        parts = raw_command.split()
        duration = 5.0  # padrão
        if len(parts) > 1:
            try:
                duration = float(parts[1])
            except ValueError:
                duration = 5.0

        # Mostra indicador de gravando
        scroll = self.query_one("#container", ChatScroll)
        turno = scroll.iniciar_turno(f"/stt {duration}s")
        await turno.add_thinking_entry(ThinkingEntry(
            type="info",
            timestamp=datetime.now(),
            content=f"🎤 Gravando por {duration}s... fale agora",
        ))

        try:
            # Executa transcrição
            result = await execute_stt_command(duration=duration)

            # Atualiza turno com resultado
            await turno.add_thinking_entry(ThinkingEntry(
                type="success",
                timestamp=datetime.now(),
                content=result,
            ))
            log = self.query_one(ChatLog)
            log.evento("STT concluído", result)

        except Exception as e:
            await turno.add_thinking_entry(ThinkingEntry(
                type="error",
                timestamp=datetime.now(),
                content=f"❌ Erro na transcrição: {e}",
            ))

    async def _handle_tts_command(self, raw_command: str) -> None:
        """
        Processa comando /tts <texto>.

        Fala o texto especificado e adiciona confirmação ao chat.
        """
        # Extrai texto para falar
        text = raw_command[4:].strip()  # Remove "/tts"
        if not text:
            self._show_voice_message("💡 Uso: /tts <texto para falar>")
            return

        # Mostra indicador de processando
        scroll = self.query_one("#container", ChatScroll)
        turno = scroll.iniciar_turno(raw_command)
        await turno.add_thinking_entry(ThinkingEntry(
            type="info",
            timestamp=datetime.now(),
            content=f"🔊 Falando: \"{text}\"",
        ))

        try:
            # Executa TTS
            result = await execute_tts_command(text)

            # Atualiza turno com resultado
            await turno.add_thinking_entry(ThinkingEntry(
                type="success",
                timestamp=datetime.now(),
                content=result,
            ))
            log = self.query_one(ChatLog)
            log.evento("TTS concluído", text)

        except Exception as e:
            await turno.add_thinking_entry(ThinkingEntry(
                type="error",
                timestamp=datetime.now(),
                content=f"❌ Erro na síntese: {e}",
            ))

    async def _handle_voice_mode_command(self, raw_command: str) -> None:
        """
        Processa comando /voice para ativar/desativar modo conversacional.

        Modo voz permite conversar falando em vez de digitar.
        """
        is_active = await self._voice_handler.handle_voice_toggle()

        if is_active:
            self._show_voice_message(
                "🎙️ **Modo Voz Ativado**\n\n"
                "Pressione ESPAÇO para falar (push-to-talk)\n"
                "Pressione ESC ou /voice para desativar"
            )
            log = self.query_one(ChatLog)
            log.evento("Modo voz", "Ativado")
        else:
            self._show_voice_message("🎙️ Modo voz desativado.")
            log = self.query_one(ChatLog)
            log.evento("Modo voz", "Desativado")

    def _show_voice_message(self, message: str) -> None:
        """
        Mostra mensagem de voz no chat como mensagem do sistema.

        Args:
            message: Mensagem para exibir
        """
        # Cria turno especial para mensagem de sistema
        scroll = self.query_one("#container", ChatScroll)
        turno = scroll.iniciar_turno("[SISTEMA]")

        # Adiciona como thinking entry (não precisa de processamento)
        from textual import work
        @work(exclusive=True)
        async def _show_message():
            await turno.add_thinking_entry(ThinkingEntry(
                type="info",
                timestamp=datetime.now(),
                content=message,
            ))

        _show_message()


__all__ = ["ChatScreen"]
