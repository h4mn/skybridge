# Cedilha — Harness pt-BR para LLMs

## Nome

**cedilha** — a ç que o LLM apaga.

## Problema

LLMs geram texto em pt-BR sem diacríticos (ç, ã, é, ê, í, ó, ú). Impacto:

- **TTS ilegível** — fonemas errados
- **Perda de foco** — cérebro de nativo trava ao ler sem acentos
- **Produtividade** — tempo gasto corrigindo manualmente

**Responsabilidade:** O LLM deveria gerar texto correto. Cedilha não substitui isso — é uma rede de segurança enquanto o problema não é resolvido na geração.

---

## Fase 1 — Hook Detector (imediato)

### Objetivo

Hook PostToolUse do Claude Code que **detecta** diacríticos ausentes e **alerta**, sem corrigir. Ao bloquear a escrita, o modelo é forçado a corrigir o próprio erro — aprendendo pelo feedback.

### Comportamento

```
LLM gera arquivo sem acentos
  → Hook detecta padrões (transcricao, voce, analise, ...)
  → Hook bloqueia a escrita e lista os problemas
  → Modelo corrige e reescreve com acentos
  → Hook aprova
```

### Entrega

- `src/core/cedilha/cedilha_hook.py` — script do hook
- Dicionário reverso inline (~200 palavras mais comuns)
- Integração no `hooks.json` do projeto

### Formato do alerta

```
 Cedilha: 12 diacríticos ausentes em arquivo.md
  - linha 5: "transcricao" → "transcrição"
  - linha 8: "voce" → "você"
  - linha 12: "analise" → "análise"
  ... e mais 9

Corrija e reescreva o arquivo.
```

---

## Fase 2 — Decisão futura

Após validação da Fase 1, decidir entre:

| Opção | Descrição | Esforço |
|---|---|---|
| **A: PyPI** | Biblioteca completa com dicionário amplo + CLI | Médio |
| **B: Benchmark** | Dataset + eval pra contribuir pro time do GLM | Médio |
| **C: Token diag** | Investigar tokenização do GLM com diacríticos | Baixo |
| **D: RL fine-tune** | Dados de reinforcement pra corrigir comportamento | Alto |

A decisão depende de:
- Quão efetivo é o hook da Fase 1
- Se o problema persiste com diferentes modelos
- Se há interesse da comunidade

---

## Requisito de sistema

A partir de agora, projetos da Sky devem:

1. **Hook cedilha ativo** em todo projeto que gera texto pt-BR
2. **Nenhum texto vai pra TTS** sem passar pelo cedilha
3. **Testes verificam diacríticos** em outputs de LLM

---

> "Cedilha não é detalhe, é pronúncia" – made by Sky ç
