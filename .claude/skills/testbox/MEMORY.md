# MEMORY - Skill Testbox

## [2026-03-28T17:10:00-03:00] - Sky usando Roo Code via GLM-5

**Tarefa:** Criar skill `testbox` baseada no conceito de testes caixa preta/caixa branca.

**Arquivos Criados:**
- `.agents/skills/testbox/SKILL.md` - Skill principal com 2 modos (black/white)
- `.agents/skills/testbox/templates/insights.md` - Template para modo BLACK
- `.agents/skills/testbox/templates/analysis.md` - Template para modo WHITE
- `.agents/skills/testbox/examples/paper-trading-m0.md` - Exemplo prático baseado em cenário real

**Resumo das Alterações:**

Skill criada com filosofia de testes de software:
- **Modo BLACK**: Observa comportamento externo sem acessar código, usando specs Gherkin de `openspec/specs/` e `openspec/changes/` como guia do esperado
- **Modo WHITE**: Analisa estrutura interna do código, correlacionando com insights do modo BLACK

Integrações planejadas:
- `systematic-debugging` para bugs complexos
- `test-driven-development` para criar testes
- Backlog para criar issues/tasks

Fluxo: BLACK → insights.md → WHITE → análise.md → (Code Mode / Backlog / systematic-debugging)

**Próximos Passos:**
- Testar a skill em um cenário real (ex: Paper Trading M0)
- Validar integração com systematic-debugging
- Criar specs Gherkin de exemplo em openspec/

---
