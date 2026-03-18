# AGENTS.md

- **Comunicação**: O idioma de comunicação do agente é em pt-br com encoding utf-8, respeitando os caracteres do idioma, considere os exemplos:
    - BOM: Esta acentuação e caracteres especiais são bons.
    - RUIM: Esta acentuacao e caracteres especiais nao sao bons.
- **Objetivo**: unificar e evoluir a Skybridge (engine de agentes + ferramentas) a partir de evidência (snapshots/diffs).
- **Fonte de verdade**: `docs/adr` (decisões) e `docs/prd` (entregas); `docs/spec` define contratos.
- **Regra**: comunicação externa (time/líder) sempre em resumo executivo; detalhes ficam internos.

## Sandbox do Agente

- `.agents/` é espaço de trabalho livre do agente.
- O agente pode criar, editar e apagar arquivos nesse diretório.
- Conteúdo em `.agents/` é temporário e exploratório.
- Nada fora de `.agents/` deve ser alterado sem autorização explícita.
- Promoções para `docs/` exigem decisão humana.
- Após promoção, faça a organização do espaço.
- Opcionalmente, matenha log e histórico para futuras análises.

## Encoding UTF-8 no OpenCode Windows

O OpenCode cria PTY (pseudo-terminal) sem UTF-8 por padrão no Windows.

**Solução:** Sempre usar variáveis de ambiente:
```bash
LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m <module>
```

**Referência:** https://github.com/anomalyco/opencode/issues/10491

> "Clareza primeiro, execução depois." – made by Sky ✨
