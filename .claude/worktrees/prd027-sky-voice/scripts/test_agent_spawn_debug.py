# -*- coding: utf-8 -*-
"""
Teste isolado do spawn do agente Claude SDK.

Objetivo: Debugar por que o agente não está completando.
Este script testa o spawn em um worktree isolado com logging detalhado.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from runtime.observability.logger import get_logger
from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions

# Configura logging básico
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler()]
)


async def test_simple_query():
    """Testa um query simples no SDK."""
    logger = get_logger()

    logger.info("=" * 60)
    logger.info("TESTE 1: Query simples sem worktree")
    logger.info("=" * 60)

    try:
        options = ClaudeAgentOptions(
            system_prompt="Você é um assistente útil.",
            permission_mode="bypassPermissions",
            cwd=str(Path.cwd()),
            allowed_tools=[],
        )

        async with ClaudeSDKClient(options=options) as client:
            logger.info("[TEST-1] Cliente criado, enviando query...")

            # Envia query simples
            await client.query("Olá! Por favor, responda apenas com: OK")

            logger.info("[TEST-1] Query enviada, aguardando resposta...")

            # Captura mensagens
            message_count = 0
            async for msg in client.receive_response():
                message_count += 1
                msg_type = msg.__class__.__name__
                logger.info(f"[TEST-1] Mensagem #{message_count}: {msg_type}")

                if msg_type == "ResultMessage":
                    logger.info(f"[TEST-1] ResultMessage recebida! is_error={getattr(msg, 'is_error', None)}")
                    result = getattr(msg, 'result', 'N/A')
                    logger.info(f"[TEST-1] Resultado: {result}")
                    return True

            logger.warning(f"[TEST-1] receive_response() encerrou sem ResultMessage ({message_count} mensagens)")
            return False

    except Exception as e:
        logger.error(f"[TEST-1] Erro: {e}")
        return False


async def test_hello_world_skill():
    """Testa o skill hello-world em um worktree de teste."""
    logger = get_logger()

    logger.info("=" * 60)
    logger.info("TESTE 2: Skill hello-world em worktree")
    logger.info("=" * 60)

    # Cria worktree temporário
    test_worktree = Path.cwd() / "skybridge-test-worktree"

    try:
        # Remove worktree anterior se existir
        if test_worktree.exists():
            import shutil
            shutil.rmtree(test_worktree)

        # Cria worktree
        os.makedirs(test_worktree, exist_ok=True)

        logger.info(f"[TEST-2] Worktree criado: {test_worktree}")

        # Importa adapter
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
        from core.webhooks.domain import WebhookEvent, WebhookSource
        from core.webhooks.domain import WebhookJob
        from datetime import datetime

        # Cria job de teste
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="test-123",
            payload={
                "issue": {
                    "number": 999,
                    "title": "Teste hello-world",
                    "body": "Este é um teste do skill hello-world",
                },
                "repository": {
                    "full_name": "h4mn/skybridge",
                    "owner": {"login": "h4mn"},
                    "name": "skybridge",
                },
            },
            received_at=datetime.utcnow(),
        )

        job = WebhookJob(
            job_id=f"test-job-{datetime.utcnow().timestamp()}",
            event=event,
            status="pending",
            worktree_path=str(test_worktree),
            issue_number=999,
        )

        logger.info(f"[TEST-2] Job criado: {job.job_id}")

        # Cria adapter e spawna agente
        adapter = ClaudeSDKAdapter()

        skybridge_context = {
            "worktree_path": str(test_worktree),
            "branch_name": "test-branch",
            "repo_name": "h4mn/skybridge",
        }

        logger.info("[TEST-2] Chamando adapter.spawn()...")

        result = await adapter.spawn(
            job=job,
            skill="hello-world",  # Skill mais simples
            worktree_path=str(test_worktree),
            skybridge_context=skybridge_context,
        )

        if result.is_ok:
            execution = result.value
            logger.info(f"[TEST-2] SUCESSO! Agent completou")
            logger.info(f"[TEST-2] stdout: {execution.stdout[:200] if execution.stdout else 'vazio'}")
            return True
        else:
            logger.error(f"[TEST-2] FALHOU: {result.error}")
            return False

    except Exception as e:
        logger.error(f"[TEST-2] Erro: {e}")
        return False

    finally:
        # Limpa worktree
        if test_worktree.exists():
            import shutil
            shutil.rmtree(test_worktree)
            logger.info(f"[TEST-2] Worktree removido")


async def main():
    """Executa todos os testes."""
    logger = get_logger()

    logger.info("=" * 60)
    logger.info("INICIANDO TESTES DO SPAWN DO AGENTE")
    logger.info("=" * 60)

    # Teste 1: Query simples
    test1_result = await test_simple_query()

    if test1_result:
        logger.info("✓ TESTE 1 PASSOU")
    else:
        logger.error("✗ TESTE 1 FALHOU")

    # Teste 2: Skill hello-world
    test2_result = await test_hello_world_skill()

    if test2_result:
        logger.info("✓ TESTE 2 PASSOU")
    else:
        logger.error("✗ TESTE 2 FALHOU")

    # Resumo
    logger.info("=" * 60)
    logger.info("RESUMO DOS TESTES")
    logger.info(f"  Teste 1 (Query simples): {'PASSOU' if test1_result else 'FALHOU'}")
    logger.info(f"  Teste 2 (hello-world):   {'PASSOU' if test2_result else 'FALHOU'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
