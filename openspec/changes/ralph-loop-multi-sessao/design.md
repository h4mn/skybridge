# Design: Ralph Loop Multi-Sessão

## Context

**Estado atual:**
- Ralph Loop usa arquivo de estado compartilhado: `.claude/ralph-loop.local.md`
- Múltiplas sessões Claude Code no mesmo projeto acessam o mesmo arquivo
- Quando Sessão A cria loop, Sessão B pode ler e confundir-se com o loop dela

**Infraestrutura existente:**
- Hook `UserPromptSubmit` captura session_id a cada mensagem → salva em `.claude/cache/ralph-session-id.txt`
- Setup script usa retry de 2s para ler o cache
- Stop hook já tem lógica de comparação de session_id (linhas 31-35)

## Goals / Non-Goals

**Goals:**
- Cada sessão do Ralph Loop ter seu próprio arquivo de estado isolado
- Múltiplas sessões podem executar loops simultâneos sem interferência
- Manter compatibilidade com funcionalidades existentes

**Non-Goals:**
- Modificar o comportamento do loop (apenas isolamento)
- Alterar a forma como session_id é capturado
- Mudar a lógica de bloqueio do stop hook

## Decisions

### Decisão 1: Nome de Arquivo por Sessão

**Escolha:** `.claude/ralph-loop.{session_id}.md`

**Rationale:**
- session_id já está disponível via cache do UserPromptSubmit hook
- Nome único por sessão garante isolamento natural
- Fácil de identificar qual sessão dona de qual arquivo

**Alternativas consideradas:**
- `ralph-loop.{PID}.md` → PIDs podem se reutilizar entre sessões
- `ralph-loop.{timestamp}.md` → Menos legível, pode haver colisões

### Decisão 2: Stop Hook Encontra Arquivo via Session_ID

**Escolha:** Stop hook usa session_id do HOOK_INPUT para localizar arquivo da sessão atual

**Implementação:**
```bash
# No stop-hook.sh:
HOOK_SESSION=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')
RALPH_STATE_FILE=".claude/ralph-loop.${HOOK_SESSION}.md"
```

**Rationale:**
- HOOK_INPUT já contém session_id da sessão atual
- Não precisa buscar ou iterar por arquivos
- Direto e eficiente

**Alternativas consideradas:**
- `find .claude -name "ralph-loop.*.md"` → Lento, busca em todos os projetos
- Ler cache e comparar → Cache pode não estar disponível no hook

### Decisão 3: Cancel Skill Usa Cache

**Escolha:** cancel-ralph.md lê session_id do cache do UserPromptSubmit hook

**Implementação:**
```bash
SESSION_ID=$(cat .claude/cache/ralph-session-id.txt)
rm .claude/ralph-loop.${SESSION_ID}.md
```

**Rationale:**
- Cache já é mantido pelo UserPromptSubmit hook
- Evita ler arquivos globais fora do projeto
- Simples e confiável

**Alternativas consideradas:**
- Ler history.jsonl → Lento, fora do projeto, complexo
- Buscar por arquivos `*.md` → Ambíguo qual remover

## Risks / Trade-offs

| Risco | Probabilidade | Impacto | Mitigação |
|-------|-------------|---------|-----------|
| Session_id vazio no hook | Baixa | Alto | Fallback para UUID (já implementado) |
| Cache limpo antes do cancel | Média | Médio | Verificar arquivo existe antes de remover |
| Múltiplos arquivos órfãos | Baixa | Baixo | Cleanup ao cancelar |

## Migration Plan

**Passo 1:** Modificar setup-ralph-loop.sh (linha ~184)
```bash
# De:
cat > .claude/ralph-loop.local.md <<EOF

# Para:
cat > .claude/ralph-loop.${SESSION_ID}.md <<EOF
```

**Passo 2:** Modificar stop-hook.sh (linha ~13)
```bash
# De:
RALPH_STATE_FILE=".claude/ralph-loop.local.md"

# Para:
HOOK_SESSION=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')
RALPH_STATE_FILE=".claude/ralph-loop.${HOOK_SESSION}.md"
```

**Passo 3:** Modificar cancel-ralph.md
```bash
# Usar cache do UserPromptSubmit hook:
SESSION_ID=$(cat .claude/cache/ralph-session-id.txt)
rm .claude/ralph-loop.${SESSION_ID}.md
```

**Rollback:** Reverter mudanças nos scripts. Arquivos `.local.md` antigos podem ser limpos manualmente.

## Open Questions

1. **Compatibilidade com versões antigas:** Sessões com loops antigos (`.local.md`) ainda funcionam?
   - **Resposta:** Sim, stop hook precisa aceitar ambos os formatos temporariamente

2. **Cleanup de arquivos:** Quando remover arquivos órfãos?
   - **Decisão:** Limpar ao cancelar, ou adicionar cleanup automático no SessionStart

---

> "Sessões isoladas trabalham melhor juntas" – made by Sky 🚀
