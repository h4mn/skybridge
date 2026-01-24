#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de Conexão e Operações SQLite Job Queue.

PRD018 Fase 2 - Plano B: SQLite como fila de jobs.

Uso:
    python scripts/test_sqlite_queue.py
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.webhooks.domain import WebhookJob, WebhookEvent, JobStatus
from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_basic_operations():
    """Testa operações básicas da fila."""
    logger.info("=" * 60)
    logger.info("TESTE 1: Operações Básicas")
    logger.info("=" * 60)

    # Criar fila em arquivo temporário
    queue = SQLiteJobQueue(db_path="data/test_jobs.db")

    try:
        # Criar job de teste
        job = WebhookJob(
            job_id="test-job-001",
            correlation_id="test-corr-001",
            created_at=datetime.utcnow(),
            status=JobStatus.PENDING,
            event=WebhookEvent(
                source="github",
                event_type="issues_opened",
                event_id="evt-001",
                payload={"issue_number": 123, "title": "Test Issue"},
                received_at=datetime.utcnow(),
            ),
            metadata={"test": True},
        )

        # Teste 1: Enqueue
        logger.info("1. Enfileirando job...")
        job_id = await queue.enqueue(job)
        logger.info(f"   ✓ Job enfileirado: {job_id}")

        # Teste 2: Size
        logger.info("2. Verificando tamanho da fila...")
        size = queue.size()
        logger.info(f"   ✓ Tamanho da fila: {size}")

        # Teste 3: Dequeue
        logger.info("3. Desenfileirando job...")
        dequeued_job = await queue.dequeue(timeout_seconds=2.0)
        if dequeued_job:
            logger.info(f"   ✓ Job desenfileirado: {dequeued_job.job_id}")
            logger.info(f"   ✓ Payload: {dequeued_job.event.payload}")
        else:
            logger.error("   ✗ Nenhum job desenfileirado")
            return False

        # Teste 4: Complete
        logger.info("4. Marcando job como completo...")
        await queue.complete(
            dequeued_job.job_id,
            result={"status": "success", "changes": ["file1.py"]},
        )
        logger.info(f"   ✓ Job {dequeued_job.job_id} completado")

        # Teste 5: Métricas
        logger.info("5. Buscando métricas...")
        metrics = await queue.get_metrics()
        logger.info(f"   ✓ Métricas: {metrics}")

        logger.info("✅ TESTE 1: PASSOU\n")
        return True

    except Exception as e:
        logger.error(f"✗ TESTE 1: FALHOU - {e}")
        return False
    finally:
        await queue.close()


async def test_concurrent_dequeue():
    """Testa concorrência no dequeue."""
    logger.info("=" * 60)
    logger.info("TESTE 2: Concorrência (3 workers simultâneos)")
    logger.info("=" * 60)

    queue = SQLiteJobQueue(db_path="data/test_jobs.db")

    try:
        # Enfileirar 5 jobs
        logger.info("1. Enfileirando 5 jobs...")
        for i in range(5):
            job = WebhookJob(
                job_id=f"concurrent-job-{i:03d}",
                correlation_id=f"concurrent-corr-{i}",
                created_at=datetime.utcnow(),
                status=JobStatus.PENDING,
                event=WebhookEvent(
                    source="github",
                    event_type="issues_opened",
                    event_id=f"evt-{i}",
                    payload={"issue_number": i},
                    received_at=datetime.utcnow(),
                ),
            )
            await queue.enqueue(job)
        logger.info(f"   ✓ 5 jobs enfileirados")

        # Dequeue concorrente
        logger.info("2. Iniciando 3 workers concorrentes...")

        async def worker(worker_id: int):
            jobs_processed = []
            for _ in range(3):  # Tentar pegar até 3 jobs
                job = await queue.dequeue(timeout_seconds=1.0)
                if job:
                    jobs_processed.append(job.job_id)
                    await queue.complete(job.job_id)
                    logger.info(
                        f"   Worker {worker_id}: processou {job.job_id}"
                    )
                else:
                    break
            return jobs_processed

        # Executar 3 workers simultâneos
        results = await asyncio.gather(
            worker(1),
            worker(2),
            worker(3),
        )

        # Verificar duplicações
        all_jobs = []
        for worker_jobs in results:
            all_jobs.extend(worker_jobs)

        unique_jobs = set(all_jobs)
        duplicates = len(all_jobs) - len(unique_jobs)

        logger.info(f"   ✓ Total jobs processados: {len(all_jobs)}")
        logger.info(f"   ✓ Jobs únicos: {len(unique_jobs)}")
        logger.info(f"   ✓ Duplicados: {duplicates}")

        if duplicates > 0:
            logger.error(f"   ✗ DUPLICADOS DETECTADOS: {duplicates}")
            return False

        logger.info("✅ TESTE 2: PASSOU (sem duplicações)\n")
        return True

    except Exception as e:
        logger.error(f"✗ TESTE 2: FALHOU - {e}")
        return False
    finally:
        await queue.close()


async def test_delivery_deduplication():
    """Testa deduplicação de delivery."""
    logger.info("=" * 60)
    logger.info("TESTE 3: Deduplicação de Webhook")
    logger.info("=" * 60)

    queue = SQLiteJobQueue(db_path="data/test_jobs.db")

    try:
        delivery_id = "test-delivery-123"

        # Teste 1: Primeira vez não existe
        logger.info("1. Verificando se delivery existe (primeira vez)...")
        exists = await queue.exists_by_delivery(delivery_id)
        logger.info(f"   ✓ Exists: {exists}")
        if exists:
            logger.error("   ✗ Delivery não deveria existir ainda")
            return False

        # Teste 2: Marcar como processado
        logger.info("2. Marcando delivery como processado...")
        await queue.mark_delivery_processed(delivery_id, "job-001")
        logger.info("   ✓ Delivery marcado")

        # Teste 3: Agora deve existir
        logger.info("3. Verificando se delivery existe (após marcação)...")
        exists = await queue.exists_by_delivery(delivery_id)
        logger.info(f"   ✓ Exists: {exists}")
        if not exists:
            logger.error("   ✗ Delivery deveria existir agora")
            return False

        logger.info("✅ TESTE 3: PASSOU\n")
        return True

    except Exception as e:
        logger.error(f"✗ TESTE 3: FALHOU - {e}")
        return False
    finally:
        await queue.close()


async def test_failure_recovery():
    """Testa recuperação de falha."""
    logger.info("=" * 60)
    logger.info("TESTE 4: Recuperação de Falha")
    logger.info("=" * 60)

    queue = SQLiteJobQueue(db_path="data/test_jobs.db")

    try:
        # Enfileirar job
        job = WebhookJob(
            job_id="fail-test-job",
            correlation_id="fail-test-corr",
            created_at=datetime.utcnow(),
            status=JobStatus.PENDING,
            event=WebhookEvent(
                source="github",
                event_type="issues_opened",
                event_id="evt-fail",
                payload={"issue_number": 999},
                received_at=datetime.utcnow(),
            ),
        )
        await queue.enqueue(job)
        logger.info("1. Job enfileirado")

        # Desenfileirar
        dequeued = await queue.dequeue(timeout_seconds=1.0)
        if not dequeued:
            logger.error("   ✗ Falha ao desenfileirar")
            return False
        logger.info(f"2. Job desenfileirado: {dequeued.job_id}")

        # Marcar como falhou
        await queue.fail(dequeued.job_id, "Erro simulado para teste")
        logger.info("3. Job marcado como falhou")

        # Verificar métricas
        metrics = await queue.get_metrics()
        logger.info(f"4. Métricas: failed={metrics['total_failed']}")
        if metrics["total_failed"] == 0:
            logger.error("   ✗ Nenhum job falho registrado")
            return False

        logger.info("✅ TESTE 4: PASSOU\n")
        return True

    except Exception as e:
        logger.error(f"✗ TESTE 4: FALHOU - {e}")
        return False
    finally:
        await queue.close()


async def test_cleanup_and_vacuum():
    """Testa cleanup e vacuum."""
    logger.info("=" * 60)
    logger.info("TESTE 5: Cleanup e VACUUM")
    logger.info("=" * 60)

    queue = SQLiteJobQueue(db_path="data/test_jobs.db")

    try:
        # Enfileirar alguns jobs
        for i in range(3):
            job = WebhookJob(
                job_id=f"cleanup-job-{i}",
                correlation_id=f"cleanup-corr-{i}",
                created_at=datetime.utcnow(),
                status=JobStatus.PENDING,
                event=WebhookEvent(
                    source="github",
                    event_type="issues_opened",
                    event_id=f"evt-cleanup-{i}",
                    payload={"issue_number": i},
                    received_at=datetime.utcnow(),
                ),
            )
            await queue.enqueue(job)

        # Completar jobs
        for i in range(3):
            job = await queue.dequeue(timeout_seconds=1.0)
            if job:
                await queue.complete(job.job_id)

        logger.info("1. 3 jobs completados")

        # Cleanup (remove jobs completados antigos)
        # Como acabamos de completar, não deve remover nada
        deleted = await queue.cleanup_old_jobs(older_than_days=1)
        logger.info(f"2. Cleanup removeu {deleted} jobs (esperado: 0)")

        # Vacuum
        await queue.vacuum()
        logger.info("3. VACUUM executado")

        # Verificar tamanho do arquivo
        db_path = Path("data/test_jobs.db")
        if db_path.exists():
            size_kb = db_path.stat().st_size / 1024
            logger.info(f"4. Tamanho do banco: {size_kb:.2f} KB")

        logger.info("✅ TESTE 5: PASSOU\n")
        return True

    except Exception as e:
        logger.error(f"✗ TESTE 5: FALHOU - {e}")
        return False
    finally:
        await queue.close()


async def main():
    """Executa todos os testes."""
    logger.info("\n" + "=" * 60)
    logger.info("SQLite Job Queue - Teste Completo")
    logger.info("=" * 60 + "\n")

    # Criar diretório data se não existir
    Path("data").mkdir(exist_ok=True)

    # Limpar banco de testes anterior
    test_db_path = Path("data/test_jobs.db")
    if test_db_path.exists():
        logger.info(f"Limpando banco de testes anterior: {test_db_path}")
        test_db_path.unlink()
        # Remover também arquivos WAL/SHM
        for ext in ["-wal", "-shm"]:
            wal_path = test_db_path.with_suffix(f".db{ext}")
            if wal_path.exists():
                wal_path.unlink()

    tests = [
        ("Operações Básicas", test_basic_operations),
        ("Concorrência", test_concurrent_dequeue),
        ("Deduplicação", test_delivery_deduplication),
        ("Recuperação de Falha", test_failure_recovery),
        ("Cleanup e VACUUM", test_cleanup_and_vacuum),
    ]

    results = []
    for name, test_func in tests:
        result = await test_func()
        results.append((name, result))

    # Resumo final
    logger.info("=" * 60)
    logger.info("RESUMO DOS TESTES")
    logger.info("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASSOU" if result else "✗ FALHOU"
        logger.info(f"{status}: {name}")

    logger.info("=" * 60)
    logger.info(f"Total: {passed}/{total} testes passaram")

    if passed == total:
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        logger.error(f"❌ {total - passed} TESTE(S) FALHARAM")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
