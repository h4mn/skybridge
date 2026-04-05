# -*- coding: utf-8 -*-
"""
Script de Sincronização de Labels do Linear

TODO: Implementar este script quando o erro "Entity not found: labelIds" ocorrer novamente.

PROBLEMA:
---------
Os label IDs estão hardcoded em múltiplos arquivos:
- src/core/discord/commands/inbox_slash.py
- src/core/discord/presentation/tools/inbox.py
- .claude/skills/inbox/__init__.py

Quando labels são recriados no Linear, os IDs mudam e o código quebra.

SOLUÇÃO:
---------
Este script deve:
1. Buscar todos os labels do time Skybridge via Linear API/MCP
2. Gerar um dict com nome -> ID dos labels relevantes
3. Atualizar AUTOMATICAMENTE todos os arquivos que usam LABELS

IMPLEMENTAÇÃO:
--------------
```python
import asyncio
from pathlib import Path

# Via Linear MCP (preferido) ou GraphQL API
# mcp__plugin_linear_linear__list_issue_labels(team="Skybridge")

LABEL_FILES = [
    "src/core/discord/commands/inbox_slash.py",
    "src/core/discord/presentation/tools/inbox.py",
    ".claude/skills/inbox/__init__.py",
]

async def sync_labels():
    \"\"\"
    Busca labels do Linear e atualiza os arquivos de configuração.
    \"\"\"
    # 1. Buscar labels via MCP
    # 2. Mapear nome -> ID
    # 3. Para cada arquivo em LABEL_FILES:
    #    - Ler conteúdo
    #    - Substituir LABELS = {...} com novos IDs
    #    - Esperar de volta
    # 4. Reportar mudanças
    pass


if __name__ == "__main__":
    asyncio.run(sync_labels())
```

HISTÓRICO:
----------
- 2026-04-05: Labels atualizados manualmente via MCP list_issue_labels
  - domínio:geral: 01fb356c... → 871a427a...
  - domínio:discord: d73805a8... → c118601f...
  - domínio:autokarpa: b729ecd3... → a97fbf6b...
  - domínio:paper: 88e309d3... → de2cf772...

> "Automate the boring stuff" – made by Sky 🚀
