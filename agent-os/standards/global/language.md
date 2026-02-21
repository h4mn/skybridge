# Language Standard

## Default Language

**All communication, documentation, and code comments MUST use Portuguese Brasileiro (pt-BR).**

### Communication

- Always respond and communicate in **Português Brasileiro**
- Technical terms and code identifiers should remain in their original form
- Examples: `function`, `class`, `async`, `await`, `API`, `endpoint`

### Documentation

- All documentation files (`.md`) must be written in pt-BR
- Comments in code should use pt-BR when explaining logic
- Technical specifications and requirements must be in pt-BR

### Code Examples

```python
# Bom - comentário em pt-BR
def processar_usuario(usuario_id: int) -> dict:
    """Processa um usuário e retorna os dados."""
    # Buscar usuário no banco
    usuario = db.query(usuario_id)
    return usuario
```

```python
# Ruim - comentário em inglês
def processar_usuario(usuario_id: int) -> dict:
    """Process user and return data."""
    # Query user from database
    usuario = db.query(usuario_id)
    return usuario
```

### Exception

Technical terms, library names, function names, and variable names should remain in English or their original language.

## OpenSpec Integration

When using OpenSpec commands (`/opsx:*`), all artifacts (proposal, specs, design, tasks) must be written in **Português Brasileiro**.

## Agent OS Integration

When using Agent OS commands (`/discover-standards`, `/inject-standards`, etc.), all output and documentation should be in **Português Brasileiro**.
