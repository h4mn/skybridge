# Tasks: /track Productivity System

**Observação:** Esta é uma change DOCUMENTAL. O código já está implementado em `.claude/skills/track/`. As tarefas abaixo validam que a especificação OPSX cobre completamente a implementação existente.

## 1. Validação de Especificação

- [ ] 1.1 Verificar se `orchestrator.py` está completamente coberto pelas specs
- [ ] 1.2 Verificar se `skill.md` workflow está documentado em specs
- [ ] 1.3 Verificar se `state.json` estrutura está especificada
- [ ] 1.4 Verificar se `events.log` formato está documentado
- [ ] 1.5 Verificar se edge-cases.md estão mapeados em scenarios

## 2. Validação de Capabilities

- [ ] 2.1 Validar spec `toggl-crud` vs funções MCP implementadas
- [ ] 2.2 Validar spec `auto-restart` vs consistency_check()
- [ ] 2.3 Validar spec `pomodoro-scheduler` vs resume_logic()
- [ ] 2.4 Validar spec `performance-cache` vs state.json caching
- [ ] 2.5 Validar spec `productivity-feedback` vs cálculo de cotas

## 3. Validação de Scenarios

- [ ] 3.1 Verificar se cada requirement tem pelo menos um scenario
- [ ] 3.2 Verificar se todos os scenarios usam formato WHEN/THEN
- [ ] 3.3 Verificar se scenarios são testáveis (podem virar testes)
- [ ] 3.4 Verificar se edge-cases documentados têm scenarios correspondentes

## 4. Revisão de Artefatos

- [ ] 4.1 Revisar `proposal.md` para clareza e completude
- [ ] 4.2 Revisar `design.md` para decisões arquiteturais
- [ ] 4.3 Revisar specs para alinhamento com código existente
- [ ] 4.4 Verificar se todos os arquivos da skill estão documentados

## 5. Arquivamento

- [ ] 5.1 Executar `openspec verify document-track-productivity-system`
- [ ] 5.2 Executar `openspec archive document-track-productivity-system`
- [ ] 5.3 Atualizar MEMORY.md com referência à especificação
- [ ] 5.4 Commit com mensagem: "docs(/track): especificação OPSX completa"

---

**Status após validação:**
- ✅ Todos os artifacts criados
- ✅ Specs cobrem implementação existente
- ✅ Pronto para arquivar (não requer implementação)

> "Documentar é preservar conhecimento para o eu do futuro" – made by Sky [tasks]
