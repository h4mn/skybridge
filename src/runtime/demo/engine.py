# -*- coding: utf-8 -*-
"""
Demo Engine — Orquestrador central de demonstrações.

Gerencia a execução de todas as demos com logging estruturado,
validação de pré-requisitos e coleta de métricas.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from time import time
from traceback import format_exc
from typing import Any

from kernel import Result
from runtime.observability.logger import Colors, get_logger, print_separator


class DemoExecutionLogger:
    """
    Logger especializado para execução de demos.

    Captura todos os eventos da execução para posterior análise.
    Integrado com sistema de Snapshot para registrar estado antes/depois.
    """

    def __init__(self, demo_id: str, execution_id: str, log_dir: Path | None = None):
        self.demo_id = demo_id
        self.execution_id = execution_id
        # Usa padrão do projeto: workspace/skybridge/logs
        self.log_dir = log_dir or Path("workspace/skybridge/logs/demos")
        self.start_time = time()
        self.events: list[dict] = []

        # Snaphots para comparacao antes/depois
        self.snapshots_before: dict[str, Any] = {}
        self.snapshots_after: dict[str, Any] = {}

    def capture_snapshot_before(self, subject: str, target: str) -> str | None:
        """
        Captura snapshot antes da operação.

        Args:
            subject: Subject do snapshot (ex: "trello").
            target: Alvo do snapshot (ex: board_id).

        Returns:
            ID do snapshot capturado ou None.
        """
        from runtime.observability.snapshot.capture import capture_snapshot
        from runtime.observability.snapshot.models import SnapshotSubject

        try:
            snapshot = capture_snapshot(
                subject=SnapshotSubject(subject.upper()),
                target=target,
                depth=3,
                tags={
                    "phase": "before",
                    "demo_id": self.demo_id,
                    "execution_id": self.execution_id,
                },
            )
            self.snapshots_before[subject] = snapshot
            self.info(f"Snapshot BEFORE capturado: {snapshot.metadata.snapshot_id}")
            return snapshot.metadata.snapshot_id
        except Exception as e:
            self.warning(f"Erro ao capturar snapshot BEFORE: {e}")
            return None

    def capture_snapshot_after(self, subject: str, target: str) -> tuple[str, str | None, str | None]:
        """
        Captura snapshot depois da operação e gera diff.

        Args:
            subject: Subject do snapshot (ex: "trello").
            target: Alvo do snapshot (ex: board_id).

        Returns:
            Tupla (after_id, before_id, diff_id) ou None.
        """
        from runtime.observability.snapshot.capture import capture_snapshot
        from runtime.observability.snapshot.models import SnapshotSubject

        try:
            snapshot_after = capture_snapshot(
                subject=SnapshotSubject(subject.upper()),
                target=target,
                depth=3,
                tags={
                    "phase": "after",
                    "demo_id": self.demo_id,
                    "execution_id": self.execution_id,
                },
            )
            self.snapshots_after[subject] = snapshot_after

            after_id = snapshot_after.metadata.snapshot_id
            before_id = None
            diff_id = None

            # Gera diff se tiver before
            if subject in self.snapshots_before:
                snapshot_before = self.snapshots_before[subject]
                before_id = snapshot_before.metadata.snapshot_id

                # Usa extractor para comparar
                from runtime.observability.snapshot.registry import ExtractorRegistry

                try:
                    extractor = ExtractorRegistry.get(SnapshotSubject(subject.upper()))
                    diff = extractor.compare(snapshot_before, snapshot_after)
                    diff_id = diff.diff_id

                    self.info(f"Snapshot AFTER capturado: {after_id}")
                    self.info(f"Diff gerado: {diff_id} ({diff.summary.added_files} added, {diff.summary.removed_files} removed)")
                except ValueError:
                    # Extractor não registrado - apenas loga
                    pass

            return (after_id, before_id, diff_id)

        except Exception as e:
            self.warning(f"Erro ao capturar snapshot AFTER: {e}")
            return (None, None, None)

    def log(self, level: str, message: str, **extra) -> None:
        """Registra um evento de log."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **extra,
        }
        self.events.append(event)

    def info(self, message: str, **extra) -> None:
        """Log informativo."""
        self.log("INFO", message, **extra)

    def warning(self, message: str, **extra) -> None:
        """Log de aviso."""
        self.log("WARNING", message, **extra)

    def success(self, message: str, **extra) -> None:
        """Log de sucesso."""
        self.log("SUCCESS", message, **extra)

    def error(self, message: str, **extra) -> None:
        """Log de erro."""
        self.log("ERROR", message, **extra)

    def progress(self, step: int, total: int, message: str, **extra) -> None:
        """Log de progresso."""
        self.log(
            "PROGRESS",
            message,
            step=step,
            total=total,
            percentage=int((step / total) * 100),
            **extra,
        )

    def get_summary(self) -> dict:
        """Retorna resumo da execução."""
        duration = time() - self.start_time

        return {
            "demo_id": self.demo_id,
            "execution_id": self.execution_id,
            "duration_seconds": round(duration, 2),
            "events_count": len(self.events),
            "events_by_level": self._count_by_level(),
        }

    def _count_by_level(self) -> dict[str, int]:
        """Conta eventos por nível."""
        counts: dict[str, int] = {}
        for event in self.events:
            level = event["level"]
            counts[level] = counts.get(level, 0) + 1
        return counts

    def save_to_file(self) -> Path | None:
        """Salva logs em arquivo JSON."""
        import json

        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{self.demo_id}_{self.execution_id}.json"
            filepath = self.log_dir / filename

            log_data = {
                "execution_id": self.execution_id,
                "demo_id": self.demo_id,
                "started_at": datetime.fromtimestamp(self.start_time).isoformat(),
                "duration_seconds": time() - self.start_time,
                "events": self.events,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            return filepath
        except Exception as e:
            self.error(f"Falha ao salvar log: {e}")
            return None


class DemoEngine:
    """
    Engine central de execução de demos.

    Responsável por:
    - Orquestrar execução de demos
    - Logging estruturado completo
    - Validação de pré-requisitos
    - Coleta de métricas

    Exemplo::

        engine = DemoEngine()
        result = await engine.run_demo("trello-flow")

        # Listar todas
        catalog = await engine.list_available()
    """

    def __init__(self, log_dir: Path | None = None):
        """
        Inicializa o engine.

        Args:
            log_dir: Diretório para salvar logs (default: .runtime/logs/demos)
        """
        self.log_dir = log_dir
        self.logger = get_logger()

    async def list_available(self) -> dict[str, list[dict]]:
        """
        Lista todas as demos disponíveis agrupadas por categoria.

        Returns:
            Dicionário com categorias e listas de demos.
        """
        from runtime.demo.registry import DemoRegistry, DemoCategory

        result = {}

        for category in DemoCategory:
            demos = DemoRegistry.list_by_category(category)
            result[category.value] = [
                {
                    "id": d.demo_id,
                    "name": d.demo_name,
                    "description": d.description,
                    "tags": d.tags,
                    "required_configs": d.required_configs,
                    "estimated_duration": d.estimated_duration_seconds,
                }
                for d in demos
            ]

        return result

    async def get_demo_info(self, demo_id: str) -> dict | None:
        """
        Obtém informações detalhadas de uma demo.

        Args:
            demo_id: ID da demo.

        Returns:
            Dicionário com informações ou None se não encontrada.
        """
        from runtime.demo.registry import DemoRegistry

        return DemoRegistry.demo_info(demo_id)

    async def run_demo(
        self,
        demo_id: str,
        params: dict[str, Any] | None = None,
        verbose: bool = True,
    ) -> dict:
        """
        Executa uma demo específica.

        Args:
            demo_id: ID da demo a executar.
            params: Parâmetros adicionais para a demo.
            verbose: Se True, imprime logs no console.

        Returns:
            Dicionário com resultado da execução.
        """
        from runtime.demo.registry import DemoRegistry
        from runtime.demo.base import DemoContext

        # Busca demo
        demo_class = DemoRegistry.get(demo_id)

        if not demo_class:
            return {
                "success": False,
                "message": f"Demo não encontrada: {demo_id}",
                "demo_id": demo_id,
            }

        # Cria instância e contexto
        demo = demo_class()
        context = DemoContext(demo_id=demo_id, params=params or {})

        # Inicia logger de execução
        exec_logger = DemoExecutionLogger(demo_id, context.execution_id, self.log_dir)

        # Adiciona exec_logger ao context para demos usarem snapshots
        context.metadata["exec_logger"] = exec_logger

        start_time = time()

        try:
            # Banner inicial
            if verbose:
                demo.print_banner(context)

            exec_logger.info("Demo iniciada", demo_id=demo_id)

            # Valida pré-requisitos
            if verbose:
                demo.log_info("Validando pré-requisitos...")

            validation = await demo.validate_prerequisites()

            if validation.is_err:
                error_msg = f"Pré-requisitos falharam: {validation.error}"
                exec_logger.error(error_msg)
                demo.log_error(error_msg)

                return {
                    "success": False,
                    "message": error_msg,
                    "demo_id": demo_id,
                    "execution_id": context.execution_id,
                }

            exec_logger.success("Pré-requisitos validados")

            # Executa demo
            if verbose:
                demo.log_info("Executando demo...")

            result = await demo.run(context)

            # Atualiza tempo de execução
            result.execution_time_seconds = round(time() - start_time, 2)

            if result.success:
                exec_logger.success("Demo concluída com sucesso")
                if verbose:
                    demo.log_success(result.message)
            else:
                exec_logger.error("Demo falhou", error=result.message)
                if verbose:
                    demo.log_error(result.message)

            # Salva log
            log_file = exec_logger.save_to_file()
            if log_file and verbose:
                demo.log_info(f"Log salvo em: {log_file}")

            return {
                **result.to_dict(),
                "demo_id": demo_id,
                "execution_id": context.execution_id,
                "log_file": str(log_file) if log_file else None,
                "log_summary": exec_logger.get_summary(),
            }

        except Exception as e:
            duration = round(time() - start_time, 2)
            error_msg = f"Erro durante execução: {e}"
            traceback_str = format_exc()

            exec_logger.error(error_msg, traceback=traceback_str)

            if verbose:
                demo.log_error(error_msg)
                print(traceback_str)

            return {
                "success": False,
                "message": error_msg,
                "demo_id": demo_id,
                "execution_id": context.execution_id,
                "execution_time_seconds": duration,
                "traceback": traceback_str,
            }

    async def list_by_flow_type(self, flow_type: str) -> list[dict]:
        """
        Lista demos por tipo de fluxo.

        Args:
            flow_type: Tipo de fluxo desejado (ex: 'issue_lifecycle').

        Returns:
            Lista de demos do fluxo especificado.
        """
        from runtime.demo.registry import DemoRegistry
        from runtime.demo.base import DemoFlowType

        target_flow = DemoFlowType(flow_type)
        matching_demos = []

        for demo_class in DemoRegistry.list_all().values():
            demo = demo_class()
            if demo.define_flow().flow_type == target_flow:
                matching_demos.append({
                    "id": demo.demo_id,
                    "name": demo.demo_name,
                    "description": demo.description,
                    "category": demo.category.value,
                })

        return matching_demos

    def print_menu(self) -> None:
        """Imprime menu interativo de demos."""
        import asyncio

        async def _print():
            catalog = await self.list_available()

            print()
            print_separator("=", 80)
            print(f"{Colors.CYAN}🎯 SKYBRIDGE - DEMO ENGINE{Colors.RESET}")
            print_separator("=", 80)

            total = 0
            for category, demos in catalog.items():
                if demos:
                    print(f"\n{Colors.WHITE}{category.upper()}{Colors.RESET}")
                    for demo in demos:
                        total += 1
                        print(f"  {Colors.CYAN}{demo['id']}{Colors.RESET} - {demo['name']}")
                        print(f"      {demo['description']}")

            print()
            print_separator("─", 80)
            print(f"{Colors.DIM}Total: {total} demos disponíveis{Colors.RESET}")
            print_separator("─", 80)
            print(f"\n💡 {Colors.YELLOW}Usage:{Colors.RESET}")
            print(f"   python -m apps.demo.cli run <demo-id>")
            print(f"   python -m apps.demo.cli info <demo-id>")
            print(f"   python -m apps.demo.cli list --flow <flow-type>")
            print()

        asyncio.run(_print())

    def get_statistics(self) -> dict:
        """
        Retorna estatísticas das demos registradas.

        Returns:
            Dicionário com estatísticas.
        """
        from runtime.demo.registry import DemoRegistry
        from runtime.demo.base import DemoCategory

        all_demos = DemoRegistry.list_all()

        return {
            "total_demos": len(all_demos),
            "by_category": {
                cat.value: len(DemoRegistry.list_by_category(cat))
                for cat in DemoCategory
            },
            "avg_duration": sum(d.estimated_duration_seconds for d in all_demos.values()) / max(len(all_demos), 1),
            "total_tags": len(set(tag for d in all_demos.values() for tag in d.tags)),
        }


# Singleton global
_engine: DemoEngine | None = None


def get_demo_engine(log_dir: Path | None = None) -> DemoEngine:
    """
    Retorna instância singleton do DemoEngine.

    Args:
        log_dir: Diretório para logs (apenas na primeira chamada).

    Returns:
        Instância do DemoEngine.
    """
    global _engine
    if _engine is None:
        _engine = DemoEngine(log_dir)
    return _engine
