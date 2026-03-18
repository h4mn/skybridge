# -*- coding: utf-8 -*-
"""
Script de diagnóstico para integração Trello.

Verifica:
1. Configuração de variáveis de ambiente
2. Acesso à API do Trello
3. Existência do board e listas
4. Teste de criação de card
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def check_env_vars() -> dict:
    """Verifica variáveis de ambiente do Trello."""
    print("\n" + "=" * 60)
    print("1. VERIFICANDO VARIÁVEIS DE AMBIENTE")
    print("=" * 60)

    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    results = {
        "api_key": bool(api_key),
        "api_token": bool(api_token),
        "board_id": bool(board_id),
    }

    print(f"TRELLO_API_KEY:   {'✅ Configurado' if api_key else '❌ NÃO configurado'}")
    print(f"TRELLO_API_TOKEN: {'✅ Configurado' if api_token else '❌ NÃO configurado'}")
    print(f"TRELLO_BOARD_ID:  {'✅ Configurado' if board_id else '❌ NÃO configurado'}")

    if board_id:
        print(f"   Board ID: {board_id}")

    return results


async def check_trello_api(api_key: str, api_token: str) -> dict:
    """Verifica acesso à API do Trello."""
    print("\n" + "=" * 60)
    print("2. VERIFICANDO ACESSO À API DO TRELLO")
    print("=" * 60)

    import httpx

    client = httpx.AsyncClient(
        base_url="https://api.trello.com/1",
        params={"key": api_key, "token": api_token},
        timeout=30.0,
    )

    try:
        # Teste simples: buscar informações do token
        response = await client.get("/tokens/{token}".format(token=api_token))
        response.raise_for_status()
        data = response.json()

        print("✅ Acesso à API confirmado")
        print(f"   Identifier: {data.get('identifier', 'N/A')}")

        await client.aclose()
        return {"api_access": True, "identifier": data.get("identifier", "N/A")}

    except Exception as e:
        print(f"❌ Erro ao acessar API: {e}")
        await client.aclose()
        return {"api_access": False, "error": str(e)}


async def check_board(api_key: str, api_token: str, board_id: str) -> dict:
    """Verifica se o board existe e lista as listas."""
    print("\n" + "=" * 60)
    print("3. VERIFICANDO BOARD E LISTAS")
    print("=" * 60)

    import httpx

    client = httpx.AsyncClient(
        base_url="https://api.trello.com/1",
        params={"key": api_key, "token": api_token},
        timeout=30.0,
    )

    try:
        # Busca informações do board
        response = await client.get(f"/boards/{board_id}")
        response.raise_for_status()
        board_data = response.json()

        print(f"✅ Board encontrado: {board_data.get('name', 'N/A')}")
        print(f"   URL: {board_data.get('url', 'N/A')}")

        # Busca listas do board
        response = await client.get(f"/boards/{board_id}/lists")
        response.raise_for_status()
        lists_data = response.json()

        print(f"\n📋 Listas encontradas ({len(lists_data)}):")
        list_names = []
        for lst in lists_data:
            if not lst.get("closed"):
                name = lst.get("name", "N/A")
                list_id = lst.get("id", "N/A")
                list_names.append(name.lower())
                print(f"   - {name} ({list_id})")

        await client.aclose()

        # Verifica se a lista padrão "📥 Issues" existe
        has_issues_list = any("issues" in name or "📥" in name for name in list_names)
        has_a_fazer = any("a fazer" in name or "📋" in name for name in list_names)

        print(f"\n📥 Lista 'Issues': {'✅ Encontrada' if has_issues_list else '⚠️ NÃO encontrada'}")
        print(f"📋 Lista 'A Fazer': {'✅ Encontrada' if has_a_fazer else '⚠️ NÃO encontrada'}")

        return {
            "board_exists": True,
            "board_name": board_data.get("name", "N/A"),
            "lists": list_names,
            "has_issues_list": has_issues_list,
            "has_a_fazer": has_a_fazer,
        }

    except Exception as e:
        print(f"❌ Erro ao acessar board: {e}")
        await client.aclose()
        return {"board_exists": False, "error": str(e)}


async def check_event_bus() -> dict:
    """Verifica se o EventBus está funcionando."""
    print("\n" + "=" * 60)
    print("4. VERIFICANDO EVENT BUS")
    print("=" * 60)

    try:
        from infra.domain_events.in_memory_event_bus import InMemoryEventBus

        event_bus = InMemoryEventBus()

        # Teste simples: publicar e receber um evento
        from core.domain_events.issue_events import IssueReceivedEvent

        test_event = IssueReceivedEvent(
            aggregate_id="test#999",
            issue_number=999,
            repository="test/repo",
            title="Test Event",
            body="Test body",
            sender="test",
            action="opened",
            labels=[],
            assignee=None,
        )

        received_events = []

        async def handler(event):
            received_events.append(event)

        sub_id = event_bus.subscribe(IssueReceivedEvent, handler)
        await event_bus.publish(test_event)

        # Pequeno delay para processamento
        await asyncio.sleep(0.1)

        event_bus.unsubscribe(sub_id)

        if received_events:
            print("✅ EventBus funcionando corretamente")
            return {"event_bus_ok": True}
        else:
            print("⚠️ EventBus criado mas evento não foi recebido")
            return {"event_bus_ok": False, "error": "Event not received"}

    except Exception as e:
        print(f"❌ Erro ao verificar EventBus: {e}")
        return {"event_bus_ok": False, "error": str(e)}


async def test_card_creation(api_key: str, api_token: str, board_id: str) -> dict:
    """Tenta criar um card de teste."""
    print("\n" + "=" * 60)
    print("5. TESTE DE CRIAÇÃO DE CARD")
    print("=" * 60)

    import httpx

    client = httpx.AsyncClient(
        base_url="https://api.trello.com/1",
        params={"key": api_key, "token": api_token},
        timeout=30.0,
    )

    try:
        # Primeiro busca uma lista para criar o card
        response = await client.get(f"/boards/{board_id}/lists")
        response.raise_for_status()
        lists_data = response.json()

        # Procura uma lista aberta (preferencialmente "A Fazer" ou a primeira)
        target_list = None
        for lst in lists_data:
            if not lst.get("closed"):
                if "a fazer" in lst.get("name", "").lower() or "📋" in lst.get("name", ""):
                    target_list = lst
                    break

        if not target_list and lists_data:
            # Usa a primeira lista aberta
            for lst in lists_data:
                if not lst.get("closed"):
                    target_list = lst
                    break

        if not target_list:
            print("❌ Nenhuma lista encontrada para criar o card")
            await client.aclose()
            return {"card_created": False, "error": "No list found"}

        list_name = target_list.get("name", "N/A")
        list_id = target_list.get("id")

        print(f"Criando card na lista: {list_name}")

        # Cria um card de teste
        payload = {
            "name": "🧪 Teste Skybridge - Deletar",
            "desc": "Card de teste criado pelo script de diagnóstico. Pode deletar.",
            "idList": list_id,
        }

        response = await client.post("/cards", json=payload)
        response.raise_for_status()
        card_data = response.json()

        card_id = card_data.get("id")
        card_url = card_data.get("url")

        print(f"✅ Card criado com sucesso!")
        print(f"   ID: {card_id}")
        print(f"   URL: {card_url}")

        await client.aclose()
        return {
            "card_created": True,
            "card_id": card_id,
            "card_url": card_url,
            "list_name": list_name,
        }

    except Exception as e:
        print(f"❌ Erro ao criar card: {e}")
        await client.aclose()
        return {"card_created": False, "error": str(e)}


async def main():
    """Função principal de diagnóstico."""
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DA INTEGRAÇÃO TRELLO - SKYBRIDGE")
    print("=" * 60)

    # 1. Verifica variáveis de ambiente
    env_results = await check_env_vars()

    if not all([env_results["api_key"], env_results["api_token"]]):
        print("\n❌ VARIÁVEIS DE AMBIENTE NÃO CONFIGURADAS")
        print("\nConfigure as seguintes variáveis:")
        print("  TRELLO_API_KEY - Obter em: https://trello.com/app-key")
        print("  TRELLO_API_TOKEN - Gerar em: https://trello.com/app-key")
        print("  TRELLO_BOARD_ID - ID do board (na URL do board)")
        return

    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    # 2. Verifica acesso à API
    api_results = await check_trello_api(api_key, api_token)

    if not api_results.get("api_access"):
        print("\n❌ NÃO FOI POSSÍVEL ACESSAR A API DO TRELLO")
        print("\nVerifique se:")
        print("  - A API_KEY está correta")
        print("  - O TOKEN tem as permissões necessárias")
        print("  - Há conexão com a internet")
        return

    # 3. Verifica board (se configurado)
    if board_id:
        board_results = await check_board(api_key, api_token, board_id)

        if not board_results.get("board_exists"):
            print("\n❌ BOARD NÃO ENCONTRADO")
            print("\nVerifique se:")
            print("  - O BOARD_ID está correto")
            print("  - O token tem acesso ao board")
            return

    # 4. Verifica EventBus
    event_results = await check_event_bus()

    # 5. Teste de criação de card
    if board_id:
        card_results = await test_card_creation(api_key, api_token, board_id)

    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DO DIAGNÓSTICO")
    print("=" * 60)

    print(f"Variáveis de ambiente: {'✅' if all(env_results.values()) else '❌'}")
    print(f"Acesso à API Trello:   {'✅' if api_results.get('api_access') else '❌'}")

    if board_id:
        print(f"Board configurado:      {'✅' if board_results.get('board_exists') else '❌'}")
        print(f"Lista 'Issues':        {'✅' if board_results.get('has_issues_list') else '⚠️'}")
        print(f"Lista 'A Fazer':      {'✅' if board_results.get('has_a_fazer') else '⚠️'}")
        print(f"Criação de card:       {'✅' if card_results.get('card_created') else '❌'}")
    else:
        print("Board configurado:      ⚠️ NÃO configurado")

    print(f"EventBus:               {'✅' if event_results.get('event_bus_ok') else '❌'}")

    print("\n" + "=" * 60)

    # Recomendações
    if board_id and not board_results.get("has_issues_list"):
        print("\n⚠️ RECOMENDAÇÃO: A lista '📥 Issues' não existe.")
        print("   O TrelloIntegrationService usa essa lista como padrão.")
        print("   Crie a lista ou configure o default_list_name corretamente.")


if __name__ == "__main__":
    asyncio.run(main())
