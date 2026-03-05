# Design: Habilitar Modo Offline do HuggingFace Hub

## Context

O `SentenceTransformer` carrega modelos do HuggingFace Hub. Por padrão, mesmo com o modelo cacheado localmente em `~/.cache/huggingface/hub/`, a biblioteca verifica se há atualizações no servidor remoto.

Isso causa:
1. Warning de requisições não autenticadas
2. Latência na inicialização
3. Falha se a internet estiver instável

## Goals / Non-Goals

**Goals:**
- Garantir funcionamento 100% offline após primeiro download
- Eliminar verificação de atualizações remotas
- Remover warning de "unauthenticated requests"

**Non-Goals:**
- Não implementar download inicial do modelo (assume-se já cacheado)
- Não configurar HF_TOKEN (não necessário para modo offline)

## Decisions

### Decisão 1: Usar variável de ambiente `HF_HUB_OFFLINE`

**Escolha:** Configurar `os.environ["HF_HUB_OFFLINE"] = "1"` antes de instanciar o modelo.

**Alternativas consideradas:**
1. **HF_TOKEN** - Requer conta no HF, não resolve latência
2. **HF_DATASETS_OFFLINE** - Não afeta modelos, só datasets
3. **Configurar globalmente no sistema** - Não é portável, depende do ambiente

**Racional:** `HF_HUB_OFFLINE=1` é a solução oficial do HuggingFace para forçar uso exclusivo do cache local.

### Decisão 2: Configurar no método `_get_model()`

**Escolha:** Adicionar a configuração no lazy load do modelo, não no `__init__`.

**Racional:**
- Só afeta quando o modelo é realmente carregado
- Permite que testes unitários mocked não precisem da variável
- Mantém o comportamento isolado

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Modelo não cacheado causa erro | Documentar que primeiro uso requer internet |
| Usuário quer atualizar modelo | Limpar cache manualmente ou usar `HF_HUB_OFFLINE=0` |

## Migration Plan

1. Adicionar `os.environ["HF_HUB_OFFLINE"] = "1"` em `_get_model()`
2. Testar com modelo já cacheado
3. Documentar no README sobre primeiro uso

**Rollback:** Remover a linha se causar problemas inesperados.
