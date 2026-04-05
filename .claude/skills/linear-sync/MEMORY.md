# Memory - Skill linear-sync

## [2026-03-28T17:24:00Z] - Sky usando Roo Code via GLM-5

**Tarefa:** Criar skill `linear-sync` para gerenciar issues Linear com organização por labels e hierarquia.

**Arquivos Modificados:**
- `.agents/skills/linear-sync/SKILL.md` (criado)
- `.claude/skills/linear-sync/SKILL.md` (criado)

**Resumo das Alterações:**
Skill consolidada para integração Linear + Codebase com:
- 4 operações atômicas: `linear_search`, `linear_create`, `linear_update`, `linear_milestone`
- Organização hierárquica: Milestone → Change → Phase → Task
- Labels padronizadas: `change:xxx`, `scope:xxx`, `priority:xxx`
- Checklist de sincronização manual codebase-roadmap
- Seção de melhorias evolutivas para futuras integrações (OpenSpec, ADRs, Custom Fields, Snapshots)

Abordagem simplificada escolhida após análise crítica:
- 1 arquivo único (~200 tokens)
- Sem specRef/ADR obrigatório (labels suficientes)
- Diff/drift via seção instrucional (não infraestrutura)

**Próximos Passos:**
- Testar skill com cenários reais do projeto
- Considerar integração com MCP Linear quando disponível

---
