# /track — Edge Cases & Error Handling

> Referência para situações incomuns. Carregar **apenas** quando o Quick Reference do SKILL.md não cobrir o caso.

## Índice

| # | Caso | Quando |
|---|------|--------|
| 1 | Múltiplos projetos detectados | Contexto menciona 2+ projetos |
| 2 | Tags conflitantes | Múltiplas tags com prioridade ambígua |
| 3 | Toggl API falha | Timeout ou erro de conexão |
| 4 | Trabalho contínuo > 2h | Sessão longa sem pausas |
| 5 | Múltiplos workspaces | Conta com mais de um workspace |
| 6 | Atividade mudou mid-stream | Troca de tarefa durante timer |
| 7 | Usuário ainda descansando | Pausa Pomodoro não terminou |
| 8 | RescueTime indisponível | API falha ou sem dados |
| 9 | Histórico vazio | Primeiro uso do dia |
| 10 | Duration negativo (timer rodando) | Entry ativa no Toggl |

---

## Detalhes

### 1. Múltiplos Projetos → Domain Scoring

```python
# Escolher projeto com MAIOR presença no contexto
dominios = {p: contar_ocorrencias(contexto, palavras_chave[p]) for p in projetos_detectados}
projeto_escolhido = max(dominios, key=dominios.get)

# Empate → perguntar usuário
if top_scores_are_tied(dominios):
    projeto = pedir_usuario("Múltiplos projetos: {top_2}. Qual usar?")
```

### 2. Tags Conflitantes → Relevance Ranking

```python
# Rank por relevância no contexto, top 3
tag_scores = {tag: calcular_relevancia(tag, contexto) for tag in tags_encontradas}
tags_selecionadas = sorted(tag_scores, key=tag_scores.get, reverse=True)[:3]
```

### 3. Toggl API Falha → Retry + Fallback

```python
max_retries = 2
for tentativa in range(max_retries):
    try:
        entry = toggl.get_current_entry()
        break
    except APIError:
        if tentativa == max_retries - 1:
            return modo_fallback("Toggl indisponível. Registrar localmente?")
        sleep(2 ** tentativa)
```

### 4. Trabalho Contínuo > 2h → Continuity Detection

```python
def timer_esta_correto(entry, contexto):
    if entry.duration < 0:  # Running
        duracao_real = (agora - entry.start).total_seconds() / 60
    else:
        duracao_real = entry.duration

    entradas_recentes = toggl.get_time_entries(hours=4)
    if trabalho_continuo_valido(entradas_recentes):
        tempo_ok = duracao_real < 6_horas  # Contínuo: até 6h
    else:
        tempo_ok = duracao_real < 2_horas

    return desc_match and proj_match and tags_ok and tempo_ok
```

### 5. Múltiplos Workspaces → Default Workspace

```python
DEFAULT_WORKSPACE = state.json.get("workspace_toggl_id")
if not DEFAULT_WORKSPACE:
    workspaces = toggl.list_workspaces()
    DEFAULT_WORKSPACE = workspaces[0].id
```

### 6. Atividade Mudou Mid-Stream → Sliding Window

```python
# Analisar últimas mensagens (não sessão inteira)
janela = contexto.ultimas_mensagens(minutos=15)
atividade_atual = inferir_atividade(janela)

if mudanca_drastica(atividade_anterior, atividade_atual):
    criar_nova_entrada()  # Não resumir entry antiga
```

### 7. Usuário Ainda Descansando → Active Verification

```python
if tempo_parado > 5_minutos:
    resposta = input("Voltou ao trabalho? (s/n): ")
    if resposta.lower() != 's':
        return  # Não iniciar timer
```

### 8. RescueTime Indisponível → Degrade Gracefully

```python
try:
    produtividade = rescuetime.get_productivity_score()
except APIError:
    produtividade = None  # Continua sem métricas
```

### 9. Histórico Vazio → Friendly Message

```python
if not toggl.get_time_entries(period="today"):
    print("📭 Nenhuma entrada hoje. Use /track 'nova tarefa' para começar.")
```

### 10. Duration Negativo (Timer Rodando)

```python
# CRITICAL: duration é NEGATIVO quando timer está rodando
if entry.duration < 0:  # RUNNING
    duracao_real = (datetime.now() - parse_iso(entry.start)).total_seconds() / 60
    tempo_ok = duracao_real < 6_horas if trabalho_continuo() else duracao_real < 2_horas
```

---

> "Edge cases são onde a mágica acontece... ou onde tudo quebra" – made by Sky
