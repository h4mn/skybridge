# Metodologia de Investigação com Equipe de Agentes - Lições Aprendidas

**Data:** 2026-02-09
**Investigação:** Skybridge - Análise de projeto "abandonado"
**Metodologia:** Coordenação de 5 agentes especializados em paralelo
**Status:** ✅ SUCESSO

---

## 📋 Resumo Executivo

Esta investigação demonstrou que **equipes de agentes especializados** podem conduzir análises complexas de codebases de forma eficaz, desde que:

1. **Cada agente tenha uma responsabilidade clara e única**
2. **Contrato de comunicação seja estabelecido upfront**
3. **Líder humano processe e consolide os findings**
4. **Escopo seja bem definido para evitar overlap**

**Tempo total de investigação:** ~45 minutos
**Arquivos analisados:** 100+ arquivos de código + documentação
**Relatórios gerados:** 5 relatórios especializados + 1 consolidado

---

## 1. Metodologia Aplicada

### 1.1 Estrutura da Equipe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ESTRUTURA DA EQUIPE                                │
│                                                                              │
│  ┌─────────────────┐                                                          │
│  │   TEAM LEAD      │  [humano/coordenador]                                   │
│  │   (Você)        │  - Cria equipe                                           │
│  └────────┬────────┘  - Define tarefas                                        │
│           │           - Processa relatórios                                   │
│           │           - Consolida findings                                    │
│           │                                                                 │
│           ├─────────────────────────────────────────────────────────────┐   │
│           │                                                             │   │
│  ┌────────▼────────┐  ┌────────▼─────────┐  ┌────────▼──────────┐       │   │
│  │ docs-explorer   │  │ git-historian    │  │code-archaeologist  │       │   │
│  │ (azul)          │  │ (verde)          │  │ (amarelo)          │       │   │
│  │                 │  │                  │  │                    │       │   │
│  │ README.md       │  │ git log          │  │ TODO/FIXME         │       │   │
│  │ docs/*.md        │  │ branches         │  │ NotImplemented    │       │   │
│  │ ADRs/PRDs/SPECs  │  │ commits          │  │ test skips         │       │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────────┘       │   │
│                                                                              │
│  ┌────────▼─────────┐  ┌────────▼──────────┐                               │   │
│  │ tech-detective   │  │ devsetup-analyst  │                               │   │
│  │ (roxo)           │  │ (laranja)         │                               │   │
│  │                  │  │                   │                               │   │
│  │ Dependências     │  │ .env.example      │                               │   │
│  │ Exceções         │  │ Setup complexity   │                               │   │
│  │ Workarounds      │  │ Onboarding gaps   │                               │   │
│  └──────────────────┘  └──────────────────┘                               │   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Ciclo de Vida da Investigação

```
FASE 1: PREPARAÇÃO (5 min)
├─ 1.1 Entender objetivo do usuário
├─ 1.2 Criar equipe com TeamCreate
├─ 1.3 Definir tarefas com TaskCreate
├─ 1.4 Atribuir owners com TaskUpdate
└─ 1.5 Spawnar agentes com Task tool

FASE 2: EXECUÇÃO EM PARALELO (20-30 min)
├─ 2.1 Cada agente trabalha independentemente
├─ 2.2 Líder humano investiga preliminarmente
├─ 2.3 Líder coleta contexto adicional
└─ 2.4 Aguardar relatórios dos agentes

FASE 3: CONSOLIDAÇÃO (15-20 min)
├─ 3.1 Receber relatórios via SendMessage
├─ 3.2 Processar e analisar findings
├─ 3.3 Identificar padrões e correlações
├─ 3.4 Sintetizar insights
└─ 3.5 Gerar relatório final

FASE 4: ENCERRAMENTO (2 min)
├─ 4.1 Agradecer equipe
├─ 4.2 Encerrar com TeamDelete
└─ 4.3 Salvar relatório consolidado
```

---

## 2. Contrato de Comunicação

### 2.1 Instrução dada aos Agentes

Cada agente recebeu a seguinte instrução crítica:

```python
# IMPORTANTE: Responda usando SendMessage tool com:
# - type="message"
# - recipient="team-lead"
# - content="<seu relatório completo>"
# - summary="<resumo de 5-10 palavras>"
```

### 2.2 Formato Esperado do Relatório

Cada agente foi instruído a retornar:

```
# RELATÓRIO: [Título do Agente]

## 1. [Categoria Principal]
- Item 1
- Item 2

## 2. [Categoria Principal]
- Item 1
- Item 2

## CONCLUSÃO
[Resumo executivo do agente]
```

### 2.3 O que Funcionou

✅ **Instrução clara de comunicação** - Todos os agentes entenderam que deviam enviar mensagens para "team-lead"

✅ **Resumo de 5-10 palavras** - Facilitou scanning rápido dos findings

✅ **Responsabilidade única** - Cada agente teve um domínio específico sem overlap

### 2.4 O que Poderia Ser Melhorado

⚠️ **Confirmação de recebimento** - Alguns agentes enviaram notificações de idle antes de enviar o relatório

⚠️ **Formato inconsistente** - Alguns relatórios vieram como JSON, outros como markdown

⚠️ **Timeout** - Não havia timeout explícito para os agentes completarem

---

## 3. Responsabilidades por Agente

### 3.1 docs-explorer (Azul)

**Missão:** Analisar estrutura geral e documentação do projeto

**Tarefas:**
1. Ler README.md e toda documentação em docs/
2. Identificar propósito e intenção original
3. Mapear arquitetura proposta
4. Identificar gap entre documentado vs implementado
5. Buscar specs/*.md para especificações

**Saída Esperada:**
- O que é o projeto
- Qual era a visão/original intent
- O que está documentado vs implementado
- Documentação faltando ou incompleta

**Modelo:** Opus 4.6 (maior capacidade para análise documental)

### 3.2 git-historian (Verde)

**Missão:** Investigar histórico Git para entender onde/por que parou

**Tarefas:**
1. Executar git log --oneline --all -50
2. Procurar commits indicando problemas (revert, WIP, fix, bug)
3. Executar git branch -a para ver branches não mergeados
4. Identificar quando commits diminuíram ou pararam
5. Analisar padrões de commit

**Saída Esperada:**
- Timeline do projeto
- Evidências de luta/dificuldade
- Branches abandonados
- Padrões que indicam problemas

**Modelo:** Opus 4.6 (melhor análise de padrões)

### 3.3 code-archaeologist (Amarelo)

**Missão:** Mapear todo trabalho inacabado no código

**Tarefas:**
1. Usar Grep para TODO, FIXME, HACK, XXX, BUG
2. Buscar testes com pytest.skip
3. Identificar funções/classes com apenas pass/NotImplementedError
4. Buscar código comentado extensivamente
5. Procurar stubs ou funções vazias

**Saída Esperada:**
- Lista de TODOs/FIXMEs com localização
- Código incompleto identificado
- Testes skip/pending
- Padrões recorrentes de problemas

**Modelo:** Opus 4.6 (análise very thorough)

### 3.4 tech-detective (Roxo)

**Missão:** Identificar bloqueios técnicos e dependências problemáticas

**Tarefas:**
1. Ler pyproject.toml/requirements.txt
2. Identificar dependências desatualizadas ou problemáticas
3. Buscar tratamentos de exceção que indicam problemas
4. Identificar padrões de workarounds
5. Verificar problemas conhecidos em issues

**Saída Esperada:**
- Dependências principais e problemas
- Padrões de exceção/erro
- Workarounds encontrados
- Possíveis gargalos técnicos

**Modelo:** Opus 4.6 (análise thorough)

### 3.5 devsetup-analyst (Laranja)

**Missão:** Entender dificuldades de setup e ambiente de desenvolvimento

**Tarefas:**
1. Ler .env.example para entender variáveis necessárias
2. Identificar quantas variáveis de ambiente são necessárias
3. Verificar se há Docker/docker-compose
4. Entender processo de setup local documentado
5. Identificar dificuldades para novo desenvolvedor

**Saída Esperada:**
- Complexidade do setup local
- Número de variáveis de ambiente
- Dependências externas (APIs, serviços)
- O que poderia ser simplificado
- Gargalos de onboarding

**Modelo:** Opus 4.6 (análise thorough)

---

## 4. Técnicas Utilizadas

### 4.1 Paralelização com Task Tool

```python
# Spawnar múltiplos agentes em paralelo
Task(
    description="Investigar estrutura",
    subagent_type="Explore",
    prompt="...",
    team_name="skybridge-investigation",
    name="docs-explorer"
)

Task(
    description="Investigar git",
    subagent_type="Explore",
    prompt="...",
    team_name="skybridge-investigation",
    name="git-historian"
)

# ... e assim por diante
```

**Benefício:** 5 agentes trabalhando simultaneamente = ~5x mais rápido que sequencial

### 4.2 Task List para Rastreamento

```python
TaskCreate(
    subject="Analisar estrutura geral",
    description="...",
    activeForm="Analisando estrutura"
)
# ... criar múltiplas tarefas

TaskUpdate(
    taskId="1",
    owner="docs-explorer"
)
# ... atribuir cada tarefa a um agente
```

**Benefício:** Visibilidade clara do progresso e responsabilidades

### 4.3 SendMessage para Contrato de Comunicação

```python
# Instrução explícita aos agentes:
"Responda usando SendMessage tool com:
- type='message'
- recipient='team-lead'
- content='<seu relatório completo>'
- summary='<resumo 5-10 palavras>'"
```

**Benefício:** Canal de comunicação bem definido e previsível

### 4.4 Investigação Preliminar do Líder

Enquanto agentes trabalhavam, o líder conduziu investigação paralela:

```python
# Líder lê arquivos chave enquanto agentes trabalham
Read("README.md")
Read("pyproject.toml")
Read("ANALISE_PROBLEMAS_ATUAIS.md")
Read("core/vision.md")
```

**Benefício:** Contexto adicional para melhor interpretação dos relatórios

---

## 5. Lições Aprendidas

### 5.1 O Que Funcionou Bem ✅

#### 1. Responsabilidades Não-Overlapping

Cada agente teve um domínio **distinto e não-sobreposto**:

| Agente | Domínio | Sobreposição? |
|--------|---------|---------------|
| docs-explorer | Documentação | ❌ Não |
| git-historian | Histórico Git | ❌ Não |
| code-archaeologist | TODOs/FIXMEs | ❌ Não |
| tech-detective | Dependências/Técnico | ❌ Não |
| devsetup-analyst | Setup/Onboarding | ❌ Não |

**Resultado:** Zero duplicação de esforço, findings complementares.

#### 2. Instrução de Comunicação Explícita

Todos os agentes entenderam que deviam usar `SendMessage` com `recipient="team-lead"`.

**Resultado:** 4 de 5 agentes enviaram relatórios completos via mensagem.

#### 3. Nível de Thoroughness Apropriado

Cada agente recebeu instrução de trabalhar com nível "thorough" ou "very thorough".

**Resultado:** Análise profunda sem desperdiçar tempo em excesso.

#### 4. Investigação Preliminar do Líder

Líder não esperou passivamente - conduziu própria investigação em paralelo.

**Resultado:** Contexto adicional permitiu melhor síntese dos findings.

### 5.2 O Que Poderia Ser Melhorado ⚠️

#### 1. Timeout e Status Checking

**Problema:** Alguns agentes enviaram notificações de "idle" antes de completar.

**Solução Futura:**
```python
# Definir timeout explícito
Task(
    ...,
    timeout=180000  # 3 minutos
)

# Verificar status periodicamente
while not all_reports_received():
    check_agent_status()
    await asyncio.sleep(10)
```

#### 2. Formato Padronizado de Relatório

**Problema:** Relatórios vieram em formatos levemente diferentes (JSON vs Markdown).

**Solução Futura:**
```python
# Fornecer template explícito
"""
Use EXATAMENTE este formato:

## RELATÓRIO: [Nome do Agente]

### 1. [Categoria]
- Item
- Item

### CONCLUSÃO
[Resumo]
"""
```

#### 3. Confirmação de Recebimento

**Problema:** Sem confirmação explícita de que agente recebeu a instrução.

**Solução Futura:**
```python
# Agente deve responder imediatamente
SendMessage(
    type="message",
    recipient="team-lead",
    content="✅ Instrução recebida. Iniciando investigação...",
    summary="Confirmação de recebimento"
)
```

#### 4. Handling de Falhas Parciais

**Problema:** Se um agente falhar completamente, não há fallback fácil.

**Solução Futura:**
```python
# Implementar retry com outro agente
if agent_timeout(agent_id):
    retry_with_different_agent(
        task=failed_task,
        exclude_agents=[failed_agent_id]
    )
```

---

## 6. Padrões para Próximas Investigações

### 6.1 Template de Prompt para Agente

```python
AGENT_PROMPT_TEMPLATE = """
Você é um agente de investigação da equipe {team_name}. SUA MISSÃO:

{Tarefas específicas do agente}

IMPORTANTE: Responda usando SendMessage tool com:
- type="message"
- recipient="team-lead"
- content="<seu relatório completo em markdown>"
- summary="<resumo de 5-10 palavras>"

Seu relatório deve conter:
{Itens específicos esperados}

Trabalhe de forma {thoroughness_level}.
"""
```

### 6.2 Checklist de Preparação

```python
def setup_investigation_team(objective: str):
    checklist = [
        "✓ Criar equipe com TeamCreate",
        "✓ Definir objetivo claro e específico",
        "✓ Criar tarefas não-overlapping",
        "✓ Atribuir owners",
        "✓ Spawnar agentes com Task tool",
        "✓ Instruir comunicação via SendMessage",
        "✓ Definir nível de thoroughness",
        "✓ Estabelecer timeout",
        "✓ Preparar investigação preliminar",
    ]
    return checklist
```

### 6.3 Template de Relatório Consolidado

```markdown
# Relatório de Investigação: {Nome do Projeto}

**Data:** {Data}
**Investigação:** {Descrição}
**Metodologia:** Coordenação de {N} agentes especializados
**Status:** {Status}

## Resumo Executivo
{Resumo de 3-5 linhas}

## Principais Descobertas
| Aspecto | Status | Nota |
|---------|--------|------|

## {Seção 1}
{Conteúdo}

## {Seção 2}
{Conteúdo}

## Conclusão
{Conclusão}
```

### 6.4 Padrões de Nomenclatura

```python
# Equipes
{projeto}-{tipo}
# Ex: skybridge-investigation

# Agentes
{domínio}-{especialidade}
# Ex: docs-explorer, git-historian

# Tarefas
{verbo} {entidade} {contexto}
# Ex: Analisar estrutura geral e documentação

# Relatórios
TIPO_{PROJETO}_{DATA}.md
# Ex: INVESTIGACAO_SKYBRIDGE_20260209.md
```

---

## 7. Métricas de Sucesso

### 7.1 Métricas Quantitativas

| Métrica | Valor | Target | Status |
|---------|-------|--------|--------|
| **Tempo total de investigação** | ~45 min | < 60 min | ✅ |
| **Arquivos analisados** | 100+ | > 50 | ✅ |
| **Agentes que completaram** | 4/5 (80%) | > 75% | ✅ |
| **Relatórios recebidos** | 4 | 5 | ⚠️ |
| **Descobertas únicas** | 30+ | > 20 | ✅ |
| **Palavras no relatório final** | ~8000 | > 5000 | ✅ |

### 7.2 Métricas Qualitativas

| Dimensão | Avaliação | Nota |
|----------|-----------|------|
| **Clareza dos findings** | Excelente | 9/10 |
| **Profundidade da análise** | Excelente | 9/10 |
| **Consistência entre agentes** | Boa | 8/10 |
| **Acionabilidade das recomendações** | Excelente | 9/10 |
| **Facilidade de síntese** | Boa | 8/10 |

---

## 8. Aplicações Futuras

### 8.1 Outros Tipos de Investigação

Esta metodologia pode ser aplicada a:

| Tipo | Descrição | Agentes Sugeridos |
|------|-----------|------------------|
| **Debug** | Encontrar bug em codebase | code-explorer, test-analyst, git-blamer |
| **Refactor** | Planejar refatoração | code-analyst, dependency-tracker, test-coverage |
| **Security** | Auditoria de segurança | security-scanner, dependency-auditor, secret-hunter |
| **Performance** | Análise de performance | profiler, bottleneck-finder, log-analyst |
| **Documentation** | Atualizar docs | doc-auditor, code-comparer, gap-analyst |

### 8.2 Escala para Projetos Maiores

Para projetos maiores (1000+ arquivos):

```
1. FASE 1: Reconhecimento (2-3 agentes)
   └─ Mapear estrutura, identificar componentes principais

2. FASE 2: Análise Profunda (5-7 agentes)
   └─ Cada agente investiga um bounded context

3. FASE 3: Síntese (1 agente + líder)
   └─ Consolidar findings em relatório executivo
```

### 8.3 Integração com CI/CD

```yaml
# .github/workflows/investigation.yml
name: Periodic Investigation

on:
  schedule:
    - cron: "0 0 * * 0"  # Semanal

jobs:
  investigate:
    runs-on: ubuntu-latest
    steps:
      - name: Run investigation agents
        run: python scripts/run_investigation.py

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: investigation-report
          path: docs/report/INVESTIGACAO_*.md
```

---

## 9. Conclusão

### O Que Aprendemos

1. **Equipes de agentes funcionam** para investigações complexas
2. **Responsabilidades claras** são essenciais para evitar duplicação
3. **Contrato de comunicação explícito** garante relatórios recebidos
4. **Líder humano ativo** melhora qualidade da síntese
5. **Paralelização** reduz tempo de investigação drasticamente

### Recomendações para Próximas Investigações

1. ✅ **Definir escopo não-overlapping** para cada agente
2. ✅ **Estabelecer contrato de comunicação** upfront
3. ✅ **Usar nível "thorough"** para balance profundidade vs velocidade
4. ✅ **Conduzir investigação preliminar** em paralelo
5. ⚠️ **Implementar timeout** para evitar agents travados
6. ⚠️ **Padronizar formato de relatório** para facilitar síntese

### Impacto

Esta metodologia permitiu:
- **Análise de 100+ arquivos** em 45 minutos
- **Identificação de 30+ problemas** documentados
- **Descoberta de problema crítico** (Kanban desconectado)
- **Recomendações acionáveis** com estimativas realistas

---

## Apêndice: Código de Exemplo

### A.1 Criar Equipe de Investigação

```python
from Task import TeamCreate, TaskCreate, TaskUpdate, Task, SendMessage

# 1. Criar equipe
TeamCreate(
    team_name="{projeto}-investigation",
    description="Investigação de {contexto}"
)

# 2. Definir tarefas
TaskCreate(
    subject="Analisar {domínio 1}",
    description="{detalhes da tarefa 1}",
    activeForm="Analisando {domínio 1}"
)

# ... mais tarefas

# 3. Atribuir owners
TaskUpdate(taskId="1", owner="{agente-1}")
# ... mais atribuições

# 4. Spawnar agentes
Task(
    description="{descrição curta}",
    subagent_type="Explore",
    prompt="{prompt completo com instruções de SendMessage}",
    team_name="{projeto}-investigation",
    name="{nome-agente}"
)

# ... mais agentes
```

### A.2 Processar Relatórios

```python
# Aguardar relatórios
reports = []
while len(reports) < expected_reports:
    # Checar mensagens recebidas
    new_messages = check_messages()
    for msg in new_messages:
        if msg.type == "message" and msg.sender in expected_agents:
            reports.append(msg.content)

    # Timeout se necessário
    if time_elapsed() > MAX_TIME:
        break

# Consolidar findings
consolidated_report = consolidate_reports(reports)
```

### A.3 Encerrar Equipe

```python
from TeamDelete import TeamDelete

# Agradecer equipe
SendMessage(
    type="broadcast",
    content="Investigação concluída! Relatório: {caminho}",
    summary="Investigação completa"
)

# Encerrar e limpar
TeamDelete()
```

---

**Fim do Relatório**

**Data:** 2026-02-09
**Versão:** 1.0
**Autor:** Team Lead + Equipe skybridge-investigation
