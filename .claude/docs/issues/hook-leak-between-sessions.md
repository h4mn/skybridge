# ISSUE: Stop Hook Vazando Entre Sessões

## Status

🔴 **ABERTO** | Crítico | Data: 2026-04-04

## Descrição

Stop hooks registrados dinamicamente por planos/skills estão executando em **sessões incorretas** do mesmo projeto, causando erros quando sessões tentam fechar.

## Reprodução

1. Sessão A (discord) cria um plano com stop-hook
2. Stop-hook é registrado globalmente para o projeto `skybridge`
3. Sessão B (autotrack) tenta fechar
4. **ERRO**: Stop-hook da sessão A executa na sessão B

## Exemplo Real

```
Sessão: autotrack (PID 11460)
Hook tentando executar: plan-pyropaws-discovery.md
Erro: Hook pertence à sessão discord (PID 15024)
```

## Sessões Envolvidas

| PID | Session ID | Nome | Hook Deveria Executar? |
|------|------------|------|------------------------|
| 11460 | 7d19f4e4-19c1-4c3a-9d71-96482125d13b | autotrack | ❌ NÃO |
| 15024 | 135c02a7-c03c-4420-8200-c2ed168a0bdb | discord | ✅ SIM |
| 29216 | 72dc7f6e-e0d8-4e32-8e6a-a88414294e5e | ralph-loop | - (auto) |

## Root Cause

Hooks no Claude Code são configurados por **projeto**, não por **sessão**. Não há verificação nativa de session_id em hooks dinâmicos.

## Solução Proposta

### Solução Imediata: Wrapper Script

✅ **IMPLEMENTADO**: `.claude/hooks/session-aware-hook-wrapper.sh`

Hooks dinâmicos devem usar o wrapper para verificar session_id antes de executar:

```bash
bash .claude/hooks/session-aware-hook-wrapper.sh <SESSION_ID> <COMANDO>
```

### Solução de Longo Prazo: Suporte Nativo

Idealmente, o Claude Code deveria suportar hooks **scope-aware**:

```json
{
  "hooks": {
    "Stop": [
      {
        "sessionScope": "135c02a7-c03c-4420-8200-c2ed168a0bdb",
        "command": "bash script.sh"
      }
    ]
  }
}
```

## Workaround Atual

1. Identificar session_id da sessão que deve ter o hook
2. Registrar hook usando o wrapper com o session_id correto
3. Hook só executará na sessão especificada

## Documentação Relacionada

- Guia: `.claude/docs/hook-session-isolation-guide.md`
- Ralph Loop Multi-Sessão: `openspec/changes/ralph-loop-multi-sessao/`
- Wrapper: `.claude/hooks/session-aware-hook-wrapper.sh`

## Metadados

- **Guild ID PyroPaws**: 208357890317221888
- **Fórum criado**: 1490030080565449038
- **Acompanhamento**: Issue interna para correção

---

> "Hooks devem respeitar os limites das sessões" – made by Sky 🚀
