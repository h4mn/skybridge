---
name: utf8-check
description: Detecta e diagnostica problemas de acentuação UTF-8 em scripts Python, especialmente para Google Sheets API. Use quando houver erros de encoding, caracteres corrompidos (ç, ã, é aparecendo como símbolos), ou ao trabalhar com dados que contenham acentos portugueses brasileiros. TRIGGER quando o usuário mencionar problemas de encoding, acentos estranhos, "utf8-check", ou antes de executar scripts que manipulam texto com caracteres especiais.
---

# UTF-8 Checker

Esta skill fornece diagnóstico e soluções para problemas de acentuação UTF-8 em scripts Python.

## Sintomas Comuns

- Acentos (ç, ã, õ, é, ê, í, ó, ú) aparecem corrompidos
- Scripts Python gravando dados com acentos em arquivos/APIs
- Erros de encoding ao executar scripts
- `UnicodeEncodeError` ou `UnicodeDecodeError`

## Diagnóstico Rápido

Execute para verificar o ambiente atual:

```bash
python -c "import sys; print('stdout:', sys.stdout.encoding); print('default:', sys.getdefaultencoding())"
```

**Resultado esperado:** Ambos devem mostrar `utf-8`

## Solução Rápida

### 1. Para scripts Google Sheets (Hadsteca)

Use o módulo centralizado:

```python
# Adicione no topo do script
from sky_sheet_config import (
    configurar_utf8,
    normalizar_texto,
    SHEET_ID,
    CREDENTIAL_FILE,
    VALUE_INPUT_OPTION
)

# Configure UTF-8
configurar_utf8()

# Ao gravar dados, use:
ws.update(
    values=[[normalizar_texto(valor)]],
    range_name=celula,
    value_input_option=VALUE_INPUT_OPTION  # RAW, não USER_ENTERED
)
```

### 2. Para scripts Python genéricos

```python
import sys
import io

# Forçar UTF-8 no stdout
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Forçar no environment
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

### 3. Para ler/gravar arquivos

```python
# Sempre especifique encoding
with open('arquivo.txt', 'r', encoding='utf-8') as f:
    conteudo = f.read()

with open('arquivo.txt', 'w', encoding='utf-8') as f:
    f.write(texto)
```

### 4. Solução Permanente (Windows + Git Bash)

Adicione ao `~/.bashrc`:

```bash
# Força Python a usar UTF-8 para stdout/stderr/stdin
export PYTHONUTF8=1
```

Depois aplique com: `source ~/.bashrc`

## Verificação Pós-Fix

Rode novamente o diagnóstico:

```bash
python -c "import sys; print('stdout:', sys.stdout.encoding)"
```

Se mostrar `utf-8`, está corrigido!

## Documentação Completa

Para mais detalhes, veja: `workspaces/futura/tarefas/3732001/scripts/README_UTF8.md`

## Checklist de Aplicação

- [ ] Executei o diagnóstico?
- [ ] Identifiquei stdout != utf-8?
- [ ] Apliquei a solução apropriada?
- [ ] Validei com verificação pós-fix?

---

> "UTF-8 não é uma opção, é um padrão." – made by Sky ⚡
