# -*- coding: utf-8 -*-
"""
Demo Base — Classes base para implementação de demos.

Define a interface contratual que todas as demos devem seguir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from kernel import Result


class DemoLifecycle(str, Enum):
    """Ciclo de vida de uma demo."""

    DEV = "dev"
    """Em desenvolvimento - pode quebrar, mudanças frequentes."""

    STABLE = "stable"
    """Testada e funcional - pronto para uso em apresentações."""

    DEPRECATED = "deprecated"
    """Obsoleta - mantida por compatibilidade, mas não recomendada."""

    ARCHIVED = "archived"
    """Removida do código - mantida apenas para referência histórica."""


class DemoCategory(Enum):
    """Categorias de demonstrações."""

    TRELLO = "trello"
    """Demos focadas em integração com Trello."""

    GITHUB = "github"
    """Demos focadas em integração com GitHub."""

    E2E = "e2e"
    """Demos end-to-end completas (múltiplos serviços)."""

    QUEUE = "queue"
    """Demos de sistema de fila/messaging."""

    AGENT = "agent"
    """Demos de execução de agentes."""

    ENGINE = "engine"
    """Demos que testam a própria Demo Engine e CLI."""


class DemoFlowType(Enum):
    """
    Tipos de fluxo que uma demo pode simular.

    Define o contexto de negócio da demo.
    """

    ISSUE_LIFECYCLE = "issue_lifecycle"
    """Fluxo completo de lifecycle de uma issue (abertura → processamento → conclusão)."""

    WEBHOOK_PROCESSING = "webhook_processing"
    """Fluxo de recebimento e processamento de webhooks."""

    CARD_SYNC = "card_sync"
    """Fluxo de sincronização entre GitHub e Trello."""

    JOB_EXECUTION = "job_execution"
    """Fluxo de execução de jobs por agentes."""

    AGENT_ITERATION = "agent_iteration"
    """Fluxo de iteração do agente (fases de pensamento/ação)."""

    STANDALONE = "standalone"
    """Demo independente sem contexto de fluxo específico."""


@dataclass
class DemoContext:
    """
    Contexto de execução de uma demo.

    Contém todas as informações necessárias para executar uma demo,
    incluindo parâmetros dinâmicos passados pelo usuário.
    """

    demo_id: str
    """ID da demo sendo executada."""

    execution_id: str = field(default_factory=lambda: str(uuid4()))
    """ID único desta execução (para rastreamento)."""

    started_at: datetime = field(default_factory=datetime.utcnow)
    """Momento em que a demo iniciou."""

    params: dict[str, Any] = field(default_factory=dict)
    """Parâmetros adicionais passados pelo usuário."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Metadados adicionais para uso interno da demo."""


@dataclass
class DemoResult:
    """
    Resultado da execução de uma demo.

    Contém informações sobre sucesso/fracasso e dados retornados.
    """

    success: bool
    """Indica se a demo foi executada com sucesso."""

    message: str = ""
    """Mensagem descritiva do resultado."""

    data: dict[str, Any] = field(default_factory=dict)
    """Dados adicionais retornados pela demo (URLs, IDs, etc)."""

    execution_time_seconds: float = 0.0
    """Tempo total de execução em segundos."""

    logs: list[str] = field(default_factory=list)
    """Logs gerados durante a execução."""

    @classmethod
    def success(cls, message: str, **data) -> "DemoResult":
        """Cria resultado de sucesso."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error(cls, message: str, **data) -> "DemoResult":
        """Cria resultado de erro."""
        return cls(success=False, message=message, data=data)

    def to_dict(self) -> dict[str, Any]:
        """Converte para dict (para JSON serialization)."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "execution_time_seconds": self.execution_time_seconds,
            "logs_count": len(self.logs),
        }


@dataclass
class DemoFlow:
    """
    Metadados sobre o fluxo de negócio que a demo representa.

    Permite categorizar e documentar qual parte do sistema
    está sendo demonstrada.
    """

    flow_type: DemoFlowType
    """Tipo do fluxo."""

    description: str
    """Descrição do que o fluxo representa."""

    actors: list[str]
    """Atores/Componentes envolvidos (ex: ['GitHub', 'Trello', 'Agent'])."""

    steps: list[str]
    """Passos do fluxo em ordem."""

    entry_point: str
    """Ponto de entrada do fluxo (ex: 'webhook', 'cli', 'api')."""

    expected_outcome: str
    """Resultado esperado ao final do fluxo."""

    def __str__(self) -> str:
        """Representação string do fluxo."""
        return f"[{self.flow_type.value.upper()}] {self.description}"


class BaseDemo(ABC):
    """
    Classe base para todas as demos.

    Toda demo deve herdar desta classe e implementar os métodos
    abstratos. A classe base fornece funcionalidade comum como
    validação de pré-requisitos, logging e banners.

    Exemplo de implementação::

        class TrelloFlowDemo(BaseDemo):
            demo_id = "trello-flow"
            demo_name = "Trello Flow Demo"
            description = "Demonstra fluxo completo com Trello"
            category = DemoCategory.TRELLO
            required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN"]

            def define_flow(self) -> DemoFlow:
                return DemoFlow(
                    flow_type=DemoFlowType.CARD_SYNC,
                    description="Sincronização de issue GitHub para card Trello",
                    actors=["GitHub", "TrelloIntegrationService", "Trello"],
                    steps=["Receber webhook", "Criar card", "Atualizar status"],
                    entry_point="webhook",
                    expected_outcome="Card criado no Trello com dados da issue"
                )

            async def validate_prerequisites(self) -> Result[None, str]:
                # Valida configs
                ...

            async def run(self, context: DemoContext) -> DemoResult:
                # Executa demo
                ...
    """

    # Metadados da demo (sobrescritos pelas subclasses)
    demo_id: str = NotImplemented
    """Identificador único da demo."""

    demo_name: str = NotImplemented
    """Nome legível da demo."""

    description: str = NotImplemented
    """Descrição do que a demo faz."""

    category: DemoCategory = NotImplemented
    """Categoria a que pertence."""

    required_configs: list[str] = field(default_factory=list)
    """Variáveis de ambiente obrigatórias."""

    estimated_duration_seconds: int = 60
    """Estimativa de duração em segundos."""

    tags: list[str] = field(default_factory=list)
    """Tags para busca/filtragem (ex: ['webhook', 'trello', 'e2e'])."""

    related_issues: list[int] = field(default_factory=list)
    """
    Issues do GitHub relacionadas a esta demo.

    Permite vincular demos a issues específicas, permitindo que
    agentes descubram demos relevantes para a issue que estão trabalhando.

    Exemplo:
        related_issues = [36, 38, 40]  # Demos relacionadas a webhooks
    """

    lifecycle: DemoLifecycle = DemoLifecycle.STABLE
    """Ciclo de vida atual desta demo."""

    deprecated_since: str | None = None
    """Versão desde quando foi depreciada (ex: "v1.2.0")."""

    replaced_by: str | None = None
    """ID da demo que substitui esta (se aplicável)."""

    last_reviewed: str | None = None
    """Data da última revisão (YYYY-MM-DD)."""

    @abstractmethod
    def define_flow(self) -> DemoFlow:
        """
        Define o fluxo de negócio que esta demo representa.

        Returns:
            DemoFlow com metadados sobre o fluxo simulado.
        """
        pass

    @abstractmethod
    async def validate_prerequisites(self) -> Result[None, str]:
        """
        Valida se todos os pré-requisitos estão atendidos.

        Deve verificar:
        - Variáveis de ambiente configuradas
        - Serviços externos acessíveis
        - Dependências instaladas

        Returns:
            Result.ok(None) se válido, Result.err(mensagem) caso contrário.
        """
        pass

    @abstractmethod
    async def run(self, context: DemoContext) -> DemoResult:
        """
        Executa a demo.

        Args:
            context: Contexto de execução com parâmetros.

        Returns:
            DemoResult com sucesso/erro e dados retornados.
        """
        pass

    def print_banner(self, context: DemoContext | None = None) -> None:
        """Imprime banner padrão da demo."""
        from runtime.observability.logger import Colors, print_separator

        flow = self.define_flow()

        print()
        print_separator("=", 80)
        print(f"🚀 {self.demo_name}")
        print_separator("=", 80)
        print(f"\n📋 {self.description}")
        print(f"\n📊 Categoria: {Colors.CYAN}{self.category.value.upper()}{Colors.RESET}")
        print(f"📋 Lifecycle: {self._lifecycle_color()}{self.lifecycle.value.upper()}{Colors.RESET}")
        print(f"⏱️  Duração estimada: ~{self.estimated_duration_seconds}s")
        print(f"🏷️  Tags: {', '.join(self.tags) if self.tags else 'N/A'}")

        # Avisos de lifecycle
        if self.lifecycle == DemoLifecycle.DEV:
            print(f"\n{Colors.WARNING}⚠️  DEMO EM DESENVOLVIMENTO - PODE QUEBRAR{Colors.RESET}")
        elif self.lifecycle == DemoLifecycle.DEPRECATED:
            if self.replaced_by:
                print(f"\n{Colors.ERROR}⚠️  DEMO DEPRECIADA - Use '{self.replaced_by}' em vez{Colors.RESET}")
            else:
                print(f"\n{Colors.ERROR}⚠️  DEMO DEPRECIADA - Não recomendada para uso{Colors.RESET}")
            if self.deprecated_since:
                print(f"   Depreciada desde: {self.deprecated_since}")

        if flow:
            print(f"\n🔄 {Colors.YELLOW}{flow}{Colors.RESET}")
            print(f"   Atores: {', '.join(flow.actors)}")
            print(f"   Entrada: {flow.entry_point}")
            print(f"   Resultado: {flow.expected_outcome}")

        if self.required_configs:
            print(f"\n⚙️  Configurações necessárias:")
            for config in self.required_configs:
                print(f"   • {config}")

        if context:
            print(f"\n🆔 Execução: {Colors.WHITE}{context.execution_id}{Colors.RESET}")

        print_separator("=", 80)
        print()

    def _lifecycle_color(self) -> str:
        """Retorna cor do lifecycle."""
        from runtime.observability.logger import Colors

        return {
            DemoLifecycle.DEV: Colors.WARNING,
            DemoLifecycle.STABLE: Colors.INFO,
            DemoLifecycle.DEPRECATED: Colors.ERROR,
            DemoLifecycle.ARCHIVED: Colors.DIM,
        }.get(self.lifecycle, Colors.RESET)

    def log_info(self, message: str) -> None:
        """Registra mensagem informativa."""
        from runtime.observability.logger import Colors

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} ℹ️  {message}")

    def log_warning(self, message: str) -> None:
        """Registra mensagem de aviso."""
        from runtime.observability.logger import Colors

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} ⚠️  {message}")

    def log_success(self, message: str) -> None:
        """Registra mensagem de sucesso."""
        from runtime.observability.logger import Colors

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} {Colors.INFO}✅{Colors.RESET} {message}")

    def log_error(self, message: str) -> None:
        """Registra mensagem de erro."""
        from runtime.observability.logger import Colors

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} {Colors.ERROR}❌{Colors.RESET} {message}")

    def log_progress(self, step: int, total: int, message: str) -> None:
        """Registra progresso com barra de progresso textual."""
        from runtime.observability.logger import Colors

        percentage = int((step / total) * 100)
        bar_length = 30
        filled = int((step / total) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(
            f"{Colors.DIM}[{timestamp}]{Colors.RESET} "
            f"{Colors.CYAN}[{step}/{total}]{Colors.RESET} "
            f"{Colors.WHITE}[{percentage}%]{Colors.RESET} "
            f"[{bar}] {message}"
        )

    def log_separator(self, char: str = "─", length: int = 60) -> None:
        """Imprime separador visual."""
        print(char * length)

    async def capture_trello_before(
        self,
        exec_logger,
        board_id: str,
    ) -> str | None:
        """
        Helper para capturar snapshot do Trello antes da operação.

        Args:
            exec_logger: DemoExecutionLogger da execução atual.
            board_id: ID do board Trello.

        Returns:
            ID do snapshot ou None.
        """
        from os import getenv

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")

        if not api_key or not api_token:
            self.log_warning("TRELLO_API_KEY ou TRELLO_API_TOKEN não configurados - skip snapshot")
            return None

        # Registra extractor temporariamente
        from runtime.observability.snapshot.extractors.trello_extractor import TrelloExtractor
        from runtime.observability.snapshot.registry import ExtractorRegistry

        extractor = TrelloExtractor(api_key, api_token)
        ExtractorRegistry._extractors[extractor.subject] = extractor

        return exec_logger.capture_snapshot_before("trello", board_id)

    async def capture_trello_after(
        self,
        exec_logger,
        board_id: str,
    ) -> tuple[str, str | None, str | None]:
        """
        Helper para capturar snapshot do Trello depois da operação.

        Args:
            exec_logger: DemoExecutionLogger da execução atual.
            board_id: ID do board Trello.

        Returns:
            Tupla (after_id, before_id, diff_id) ou (None, None, None).
        """
        from os import getenv

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")

        if not api_key or not api_token:
            return (None, None, None)

        # Registra extractor temporariamente
        from runtime.observability.snapshot.extractors.trello_extractor import TrelloExtractor
        from runtime.observability.snapshot.registry import ExtractorRegistry

        extractor = TrelloExtractor(api_key, api_token)
        ExtractorRegistry._extractors[extractor.subject] = extractor

        return exec_logger.capture_snapshot_after("trello", board_id)

    async def _validate_configs(self) -> Result[None, str]:
        """
        Valida variáveis de ambiente configuradas.

        Método auxiliar para implementações de validate_prerequisites.
        """
        from os import getenv

        missing = [cfg for cfg in self.required_configs if not getenv(cfg)]

        if missing:
            return Result.err(f"Configurações faltando: {', '.join(missing)}")

        return Result.ok(None)
