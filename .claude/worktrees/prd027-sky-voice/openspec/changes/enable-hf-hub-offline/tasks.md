# Tasks: Habilitar Modo Offline do HuggingFace Hub

## 1. Implementação

- [x] 1.1 Adicionar `import os` no topo de `embedding.py` (se não existir)
- [x] 1.2 Adicionar `os.environ["HF_HUB_OFFLINE"] = "1"` no método `_get_model()` antes de instanciar SentenceTransformer
- [x] 1.3 Adicionar tratamento de erro para modelo não cacheado com mensagem instrutiva

## 2. Verificação

- [x] 2.1 Testar carregamento do modelo com cache existente
- [x] 2.2 Verificar ausência de warning "unauthenticated requests"
- [x] 2.3 Testar comportamento quando modelo não está cacheado (deve falhar com mensagem clara)
