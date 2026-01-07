---
status: aceito
data: 2025-12-26
---

# ADR009 — Cabeçalho UTF-8 obrigatório em arquivos Python

**Status:** Aceito  
**Data:** 2025-12-26

## Contexto

O repositório usa português (pt-BR) em comentários e textos, com caracteres acentuados.
Houve casos de mojibake em arquivos Python, indicando inconsistência de encoding na
edição/leitura. Para evitar regressões e garantir legibilidade, é necessário padronizar
explicitamente o encoding.

## Decisão

1. **Cabeçalho UTF-8 obrigatório**
   - Todo arquivo .py em src/ deve conter o coding cookie # -*- coding: utf-8 -*-
     na primeira ou segunda linha (após shebang, se existir).

2. **Validação automática**
   - Um teste automatizado deve falhar caso algum .py em src/ não tenha o
     cabeçalho UTF-8.
   - Um teste adicional deve falhar se houver marcadores comuns de mojibake
     (ex.: U+00C3, U+00C2, U+FFFD) em arquivos .py de src/.

## Alternativas Consideradas

1. **Confiar no default do Python 3 (UTF-8)**
   - Rejeitada: apesar de ser o padrão, não previne editores/ambientes que gravem
     com encoding incorreto.

2. **Exigir cabeçalho apenas quando houver caracteres não-ASCII**
   - Rejeitada: dificulta enforcement e aumenta risco de drift entre arquivos.

## Consequências

### Positivas

- Comentários e strings em pt-BR ficam estáveis e legíveis.
- Reduz risco de mojibake em revisões, CI e diferentes ambientes.

### Negativas / Trade-offs

- Adiciona uma linha padrão em todos os arquivos .py.

## DoD

- Todos os .py de src/ possuem o cabeçalho UTF-8.
- Testes de encoding e mojibake passam no CI/local.

> Clareza primeiro, execução depois. – made by Sky ✨
