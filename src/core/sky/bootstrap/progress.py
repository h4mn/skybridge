# coding: utf-8
"""
Progress - Barra de progresso do bootstrap.
"""

import time
from contextlib import contextmanager
from typing import Any, Callable, Optional

# Rich imports são lazy (dentro das funções) para não demorar o import do módulo


# Console global para output durante bootstrap (sem tipo para evitar import)
_global_console = None


def _get_console():
    """Retorna console global ou cria novo."""
    global _global_console
    if _global_console is None:
        from rich.console import Console
        _global_console = Console()
    return _global_console


class Progress:
    """
    Gerencia barra de progresso do bootstrap.

    Responsável por:
    - Exibir barra de progresso com tema Sky
    - Gerenciar múltiplos estágios
    - Medir tempo de cada estágio
    """

    # Cores do tema Sky
    SPINNER_STYLE = "dots.blue"
    BAR_STYLE = "bar.blue"
    TEXT_STYLE = "progress.description"
    TIME_STYLE = "progress.elapsed"

    def __init__(self, console: Optional[Any] = None):
        """
        Inicializa gerenciador de progresso.

        Args:
            console: Console Rich para output. Padrão: novo console.
        """
        self._console = console
        self._stages = []
        self._task_ids = {}
        self._start_time = None

    def add_stage(self, stage: "Stage") -> None:
        """
        Adiciona um estágio ao bootstrap.

        Args:
            stage: Configuração do estágio a adicionar.
        """
        self._stages.append(stage)

    def _create_progress(self):
        """
        Cria objeto Rich Progress com configurações Sky.

        Returns:
            RichProgress configurado.
        """
        from rich.console import Console
        from rich.progress import (
            Progress as RichProgress,
            BarColumn,
            TaskProgressColumn,
            TextColumn,
            TimeElapsedColumn,
            SpinnerColumn,
        )

        return RichProgress(
            SpinnerColumn(style=self.SPINNER_STYLE),
            TextColumn(
                "[progress.description]{task.description}",
                style=self.TEXT_STYLE,
            ),
            BarColumn(complete_style="blue", finished_style="bright_blue"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            transient=False,  # Mantém histórico visual
        )

    @contextmanager
    def run(self, total: Optional[int] = None):
        """
        Context manager para executar bootstrap com barra de progresso.

        Args:
            total: Total de estágios (calculado automaticamente se None)

        Yields:
            Progress configurado e pronto para usar.
        """
        from rich.console import Console

        # Criar console se não fornecido
        if self._console is None:
            self._console = Console()

        self._start_time = time.time()
        total = total or len(self._stages)

        progress = self._create_progress()

        try:
            with progress as p:
                # Criar tarefas para cada estágio
                for i, stage in enumerate(self._stages, 1):
                    task_id = p.add_task(
                        stage.description,
                        total=1,
                        visible=False,  # Só mostra quando ativo
                    )
                    self._task_ids[stage.name] = task_id

                # Tarefa geral de progresso
                main_task = p.add_task(
                    "Sky Chat",
                    total=total,
                    visible=True,
                )

                yield _ProgressContext(p, main_task, self._task_ids, self._stages)

        finally:
            elapsed = time.time() - self._start_time
            self._console.print(f"[dim]Carregamento concluído em {elapsed:.1f}s[/dim]")


class _ProgressContext:
    """
    Contexto interno para execução de estágios.

    Usado internamente por Progress.run() para gerenciar
    atualização de tarefas durante o bootstrap.
    """

    def __init__(
        self,
        progress: Any,  # RichProgress (evitamos import no topo)
        main_task: int,
        task_ids: dict,
        stages: list,
    ):
        self._progress = progress
        self._main_task = main_task
        self._task_ids = task_ids
        self._stages = stages
        self._current_stage_index = 0

    def start_stage(self, stage_name: str) -> None:
        """
        Marca estágio como ativo na barra de progresso.

        Args:
            stage_name: Nome do estágio a ativar.
        """
        task_id = self._task_ids.get(stage_name)
        if task_id is not None:
            self._progress.update(task_id, visible=True)

    def update_stage_description(self, stage_name: str, description: str) -> None:
        """
        Atualiza a descrição de um stage ativo em tempo real (mesma linha).

        Útil para mostrar mensagens animadas durante estágios longos,
        como o carregamento dos pesos do modelo.

        Args:
            stage_name: Nome do estágio a atualizar.
            description: Nova descrição a exibir.
        """
        task_id = self._task_ids.get(stage_name)
        if task_id is not None:
            self._progress.update(task_id, description=description, refresh=True)

    def complete_stage(self, stage_name: str) -> None:
        """
        Marca estágio como completo e avança progresso geral.

        Args:
            stage_name: Nome do estágio a completar.
        """
        task_id = self._task_ids.get(stage_name)
        if task_id is not None:
            self._progress.update(task_id, completed=1, visible=False)

        # Avança progresso geral
        self._progress.advance(self._main_task, 1)
        self._current_stage_index += 1

    def run_stage(
        self,
        stage_name: str,
        fn: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Executa uma função como estágio do bootstrap.

        Mostra progresso, mede tempo, e trata erros.

        Args:
            stage_name: Nome do estágio
            fn: Função a executar
            *args: Argumentos posicionais para a função
            **kwargs: Argumentos nomeados para a função

        Returns:
            Resultado da função executada
        """
        self.start_stage(stage_name)
        start = time.time()

        try:
            result = fn(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start
            self._progress.console.print(
                f"[dim]  [OK] {self._get_stage_description(stage_name)} ({elapsed:.2f}s)[/dim]"
            )
            self.complete_stage(stage_name)

    def _get_stage_description(self, stage_name: str) -> str:
        """Retorna descrição do estágio pelo nome."""
        for stage in self._stages:
            if stage.name == stage_name:
                return stage.description
        return stage_name
