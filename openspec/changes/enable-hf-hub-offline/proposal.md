# Proposal: Habilitar Modo Offline do HuggingFace Hub

## Why

O modelo de embedding `paraphrase-multilingual-MiniLM-L12-v2` verifica atualizações no HuggingFace Hub a cada carregamento, causando:
- Warning de "unauthenticated requests" no console
- Lentidão desnecessária na inicialização
- Dependência de conexão com internet mesmo com modelo cacheado

O spec existente já prevê funcionamento offline, mas a implementação não garante isso.

## What Changes

- Adicionar `HF_HUB_OFFLINE=1` antes de carregar o modelo SentenceTransformer
- Garantir que o modelo use apenas o cache local (~/.cache/huggingface/)
- Eliminar verificações de atualização remotas

## Capabilities

### New Capabilities

Nenhuma. A funcionalidade já existe, é uma correção de implementação.

### Modified Capabilities

- `semantic-search`: Adicionar requisito de configurar modo offline explicitamente

## Impact

- `src/core/sky/memory/embedding/embedding.py`: Linha ~130, método `_get_model()`
- Comportamento: Modelo não verifica atualizações remotas
- Risco: Se o modelo não estiver cacheado, erro será lançado (comportamento desejado)
