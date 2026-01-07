# Core Shared — Mecanismos Transversais

## O que é

Mecanismos compartilhados entre contexts, **sem regra de negócio**.

## Princípio

Use apenas quando:
- Há real compartilhamento de código entre contexts
- O código não contém lógica de domínio específica
- A alternativa seria duplicação pura

## O que PODE conter

- Types úteis (ex: `Priority`, `Identifier`)
- Helpers mínimos (ex: formatação de data pura)
- Constantes globais (ex: limits de sistema)

## O que NÃO PODE conter

- Regras de negócio de FileOps ou Tasks
- Lógica de orquestração
- Dependências externas pesadas

## Evolução

Se `shared/` crescer demais:
- Revisar se é realmente compartilhado
- Mover para context específico se pertencer a um
- Considerar criar um novo context se tiver linguagem própria

---

> "Shared deve ser mínimo, ou vira lixo." – made by Sky ✨
