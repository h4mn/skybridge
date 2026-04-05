# /track Baseline Performance Test

## Cenário Original (Relatado pelo Usuário)

> "A Skill Track ela tá demorando mais de um minuto quando eu peço pra ela fazer qualquer coisa, Inicie uma nova Track. Ela demora entre 3, 4, 5 minutos. Eu peço 'retoma o pomodoro'; ela demora mais de 4 minutos."

**Meta:** < 1 minuto
**Baseline (antes):** 3-5 minutos

## Protocolo de Teste

### Setup
- Sessão LIMPA do Claude Code (restart se necessário)
- Nenhum contexto de otimizações anteriores
- Timer pronto (celular ou comando `time`)

### Teste A: "Inicia o Pomodoro"

```
1. Marque: INÍCIO [HH:MM:SS]
2. Digite: /track inicia o pomodoro
3. Espere resposta completa aparecer
4. Marque: FIM [HH:MM:SS]
5. Calcule: FIM - INÍCIO = ___ segundos
```

**Resultado esperado:** < 60 segundos
**Resultado baseline:** 180-300 segundos (3-5 min)

### Teste B: "Retoma o Pomodoro" (apenas se timer já rodou antes)

```
1. Deixe Pomodoro rodar ~10 min
2. Pare o timer manualmente
3. Espere 2 min (break)
4. Marque: INÍCIO [HH:MM:SS]
5. Digite: /track retoma o pomodoro
6. Espere resposta completa
7. Marque: FIM [HH:MM:SS]
8. Calcule: FIM - INÍCIO = ___ segundos
```

**Resultado esperado:** < 60 segundos
**Resultado baseline:** 240+ segundos (4+ min)

## Log de Resultados

| Rodada | Teste | Início | Fim | Tempo (seg) | Status |
|--------|-------|--------|-----|-------------|--------|
| 1 | A | | | | |
| 2 | A | | | | |
| 3 | A | | | | |
| - | B | | | | |

**Média Teste A:** ___ segundos
**Status:** Passou (<60s) / Falhou (≥60s)

## Pós-Teste

Se tempo ≥ 60s:
1. Copie output completo da skill
2. Anote onde ocorreu a demora (loading? API calls? raciocínio?)
3. Reporte findings

---

> "Sem baseline, não há ciência" – made by Sky
