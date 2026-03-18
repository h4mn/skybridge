---
status: aceito
data: 2025-12-22
---

﻿# PLAYBOOK - Discovery da Skybridge via Snapshot + Scoring

## 0) Propósito
Executar uma descoberta reprodutível para localizar e comparar "entidades" (tentativas/fragmentos) da Skybridge espalhadas em `B:\_repositorios`, reduzindo ruído do monolito e produzindo um relatório que viabilize unificação.

## 1) Entradas
- Root: `B:\_repositorios`
- Profundidade: `max_depth = 5`
- Referência de formato: `B:\_repositorios\pyro\README_SNAPSHOT.md`
- Marcadores (keywords): `skybridge`, `sky-bridge`, `sky_bridge`, `sky`, `bridge`

## 2) Escopo do scan
### 2.1 Coletar (nomes + metadados)
Na fase 1, coletar **apenas**:
- nomes de pastas
- nomes de arquivos
- extensão
- tamanho e modified (se disponível)

### 2.2 Ler conteúdo (sob demanda)
Só ler conteúdo quando necessário como evidência:
- `README*`
- `pyproject.toml`
- configs relevantes (ex.: `openapi*.yml|yaml|json`, workflows)

## 3) Heurística de "Entidade"
Tratar como entidade qualquer diretório candidato que atenda **um** dos critérios:
- contém `README*` ou `pyproject.toml`
- contém `src/` ou `tests/`
- contém pasta/arquivo com marcador forte (ver seção 5)

## 4) Índices por entidade (extração)
Para cada entidade, coletar:
- contagem por tipo: `.py`, `.md`, `.toml/.txt`, `.yml/.yaml/.json`
- marcadores fortes presentes (lista)
- indícios de CLI: `__main__.py`, `cli.py`
- indícios de integração: `git`, `openapi`, `workflows`
- evidências: lista curta de paths que justificam o score

## 5) Score (ponderado)
### 5.1 Pesos base por tipo de arquivo
- `.py` = +3
- `.md` = +2
- `.toml/.txt` = +2
- `.yml/.yaml/.json` = +1

### 5.2 Bônus por marcadores fortes
- pasta `skybridge` / `modules/skybridge` / `src/skybridge` = +10
- README citando "Skybridge" (match) = +8
- presença de CLI (`__main__.py` ou `cli.py`) = +5
- openapi/workflows detectados = +3

### 5.3 Penalizações (anti-monolito)
- entidade muito genérica **sem** marcador forte = -10
- alta contagem de arquivos, mas baixa densidade de marcadores (ruído) = -5

> Observação: ajuste fino dos pesos é permitido após o primeiro relatório.

## 6) Saídas (relatório)
Gerar um relatório único com:

### 6.1 Ranking de candidatos
- Lista ordenada por score
- Top N (ex.: 10-20)

### 6.2 Evidências por entidade
Para cada entidade do ranking:
- score final
- marcadores fortes encontrados
- principais arquivos/pastas que justificam (5-15 itens)

### 6.3 Recomendações
- "Núcleo provável"
- "Paralelas/abandonadas"
- "Fragmentos reaproveitáveis"
- "Risco monolito" (sim/não + motivo)

### 6.4 Tabela comparativa por entidade
Colunas sugeridas:
- Entidade (path)
- Score
- Código (.py)
- Docs (.md)
- Config (.toml/.txt)
- Infra/API (.yml/.yaml/.json)
- CLI (sim/não)
- Snapshot/Diff (sim/não)
- Domínios detectados (File/Rota/Mensagem/etc.)
- Integrações (git/openapi/workflows/etc.)

## 7) Pós-processamento (fechamento)
- Selecionar 1-2 entidades "núcleo provável".
- Abrir ADR subsequente para unificação (se necessário).
- Criar TASK para análise profunda apenas nos candidatos top.

## 8) DoD - Definition of Done
O playbook está "cumprido" quando:
- existe ranking ordenado por score
- cada candidato possui evidências explícitas
- existe tabela comparativa completa
- há recomendação clara de núcleo provável
- campo destacando funcionalidades por entidade

---
> "Mapa primeiro, refator depois." - made by Sky
