# TASK000 - Discovery Skybridge (Snapshot + Score)

## Escopo e metodo
- Root: B:\_repositorios
- Profundidade maxima: 5 (snapshot)
- Coleta: nomes de pastas/arquivos e extensoes; leitura apenas de README* quando necessario
- Pesos (PB000): .py=+3, .md=+2, .toml/.txt=+2, .yml/.yaml/.json=+1
- Bonus: skybridge dir / modules/skybridge / src/skybridge (+10), README citando Skybridge (+8), CLI (__main__.py/cli.py) (+5), openapi/workflows (+3)
- Penalidades: entidade generica sem marcador forte (-10), alta contagem com baixa densidade de marcadores (-5)

## Ranking de entidades (score)
1) B:\_repositorios\Hadsteca\modules\skybridge -> 226
2) B:\_repositorios\_backup\sky-bridge -> 67
3) B:\_repositorios\Sky_Bridge -> 60
4) B:\_repositorios\gpt\src\sky -> 50
5) B:\_repositorios\_backup\sky-app\skybridge -> 16
6) B:\_repositorios\Skybridge_2\skybridge -> 5
7) B:\_repositorios\pyro\projects\sky -> 4
8) B:\_repositorios\skybridge -> 2
9) B:\_repositorios\Hadsteca\tests\unit\skybridge -> -7
10) B:\_repositorios\TTS\Sky -> -7
11) B:\_repositorios\Hadsteca\workspaces\skybridge -> -8

## Evidencias por entidade

### B:\_repositorios\Hadsteca\modules\skybridge (score 226)
- Contagens: .py=60 .md=8 .toml=0 .txt=11 .yml/.yaml=2 .json=3
- Marcadores fortes: openapi/workflows
- CLI: nao
- Integracoes: openapi=sim, workflows=nao

### B:\_repositorios\_backup\sky-bridge (score 67)
- Contagens: .py=9 .md=4 .toml=1 .txt=5 .yml/.yaml=4 .json=0
- Marcadores fortes: README menciona Skybridge, CLI (__main__.py/cli.py), openapi/workflows
- CLI: sim
- Integracoes: openapi=nao, workflows=sim
- README hits:
  - B:\_repositorios\_backup\sky-bridge\README.md

### B:\_repositorios\Sky_Bridge (score 60)
- Contagens: .py=3 .md=13 .toml=1 .txt=5 .yml/.yaml=2 .json=0
- Marcadores fortes: README menciona Skybridge, openapi/workflows
- CLI: nao
- Integracoes: openapi=nao, workflows=sim
- README hits:
  - B:\_repositorios\Sky_Bridge\README.md

### B:\_repositorios\gpt\src\sky (score 50)
- Contagens: .py=15 .md=0 .toml=0 .txt=0 .yml/.yaml=0 .json=0
- Marcadores fortes: CLI (__main__.py/cli.py)
- CLI: sim
- Integracoes: openapi=nao, workflows=nao

### B:\_repositorios\_backup\sky-app\skybridge (score 16)
- Contagens: .py=2 .md=1 .toml=0 .txt=0 .yml/.yaml=0 .json=0
- Marcadores fortes: README menciona Skybridge
- CLI: nao
- Integracoes: openapi=nao, workflows=nao
- README hits:
  - B:\_repositorios\_backup\sky-app\skybridge\README_MCP.md

### B:\_repositorios\Skybridge_2\skybridge (score 5)
- Contagens: .py=5 .md=0 .toml=0 .txt=0 .yml/.yaml=0 .json=0
- Marcadores fortes: nenhum
- CLI: nao
- Integracoes: openapi=nao, workflows=nao
- Penalidades: generic=-10 dense=0

### B:\_repositorios\pyro\projects\sky (score 4)
- Contagens: .py=0 .md=6 .toml=0 .txt=1 .yml/.yaml=0 .json=0
- Marcadores fortes: nenhum
- CLI: nao
- Integracoes: openapi=nao, workflows=nao
- Penalidades: generic=-10 dense=0

### B:\_repositorios\skybridge (score 2)
- Contagens: .py=0 .md=6 .toml=0 .txt=0 .yml/.yaml=0 .json=0
- Marcadores fortes: nenhum
- CLI: nao
- Integracoes: openapi=nao, workflows=nao
- Penalidades: generic=-10 dense=0

### B:\_repositorios\Hadsteca\tests\unit\skybridge (score -7)
- Contagens: .py=1 .md=0 .toml=0 .txt=0 .yml/.yaml=0 .json=0
- Marcadores fortes: nenhum
- CLI: nao
- Integracoes: openapi=nao, workflows=nao
- Penalidades: generic=-10 dense=0

### B:\_repositorios\TTS\Sky (score -7)
- Contagens: .py=1 .md=0 .toml=0 .txt=0 .yml/.yaml=0 .json=0
- Marcadores fortes: nenhum
- CLI: nao
- Integracoes: openapi=nao, workflows=nao
- Penalidades: generic=-10 dense=0

### B:\_repositorios\Hadsteca\workspaces\skybridge (score -8)
- Contagens: .py=0 .md=1 .toml=0 .txt=0 .yml/.yaml=0 .json=0
- Marcadores fortes: nenhum
- CLI: nao
- Integracoes: openapi=nao, workflows=nao
- Penalidades: generic=-10 dense=0

## Recomendacoes acionaveis
- Nucleo provavel: B:\_repositorios\Hadsteca\modules\skybridge (maior score)
- Implementacoes paralelas/abandono: B:\_repositorios\_backup\sky-bridge
- Fragmentos reaproveitaveis: B:\_repositorios\_backup\sky-bridge (docs com Skybridge)

## Tabela comparativa (resumo)
| Entidade | Score | Codigo (.py) | Docs (.md) | Config (.toml/.txt) | Infra/API (.yml/.yaml/.json) | CLI | Snapshot/Diff | Dominios detectados | Integracoes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| B:\_repositorios\Hadsteca\modules\skybridge | 226 | 60 | 8 | 11 | 5 | nao | nao | file,rota,mensagem | openapi |
| B:\_repositorios\_backup\sky-bridge | 67 | 9 | 4 | 6 | 4 | sim | nao | file | workflows |
| B:\_repositorios\Sky_Bridge | 60 | 3 | 13 | 6 | 2 | nao | nao | nenhum | workflows |
| B:\_repositorios\gpt\src\sky | 50 | 15 | 0 | 0 | 0 | sim | nao | nenhum | - |
| B:\_repositorios\_backup\sky-app\skybridge | 16 | 2 | 1 | 0 | 0 | nao | nao | nenhum | - |
| B:\_repositorios\Skybridge_2\skybridge | 5 | 5 | 0 | 0 | 0 | nao | nao | nenhum | - |
| B:\_repositorios\pyro\projects\sky | 4 | 0 | 6 | 1 | 0 | nao | nao | nenhum | - |
| B:\_repositorios\skybridge | 2 | 0 | 6 | 0 | 0 | nao | nao | nenhum | - |
| B:\_repositorios\Hadsteca\tests\unit\skybridge | -7 | 1 | 0 | 0 | 0 | nao | nao | nenhum | - |
| B:\_repositorios\TTS\Sky | -7 | 1 | 0 | 0 | 0 | nao | nao | nenhum | - |
| B:\_repositorios\Hadsteca\workspaces\skybridge | -8 | 0 | 1 | 0 | 0 | nao | nao | nenhum | - |