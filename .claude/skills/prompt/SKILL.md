---
name: prompt-engineer
description: Use this skill whenever the user wants to create, improve, or structure a /prompt file or agent instruction. Triggers on phrases like "cria um prompt para", "melhora esse prompt", "escreve um /prompt", "quero um prompt que faça X", or when the user describes an intent that should become a structured agent instruction. Also triggers when the user wants to run /ralph-loop with a well-crafted input — apply best practices to the raw intent and execute the command directly. Use this skill even for vague inputs like "quero evoluir X" or "faz o agente fazer Y" — the skill's job is to turn rough ideas into precise instructions.
---

# Prompt Engineer

Transforma intenção bruta em prompts estruturados prontos para uso em agentes, e executa comandos como `/ralph-loop` com o prompt melhorado.

## Processo

### 1. Extrair intenção

Antes de escrever o prompt, identifique os 4 eixos. Infira o que puder — pergunte apenas o que for crítico e não estiver claro.

| Eixo | Pergunta | Exemplo |
|---|---|---|
| **Objetivo** | O que o agente deve produzir? | "um arquivo solution.py funcional" |
| **Contexto** | Qual é o domínio e estado atual? | "projeto Python, testes falhando" |
| **Restrições** | O que o agente não deve fazer? | "não alterar arquivos de config" |
| **Critério de sucesso** | Como saber que está pronto? | "todos os testes passam" |

### 2. Construir o prompt

Use esta estrutura base. Adapte seções conforme necessário — não todas são obrigatórias.

```
<papel>
Você é [papel específico] com expertise em [domínio].
</papel>

<tarefa>
[Verbo de ação claro] + [objeto] + [resultado esperado].
</tarefa>

<contexto>
[Estado atual do sistema, arquivos relevantes, histórico necessário]
</contexto>

<restrições>
- [O que fazer — positivo primeiro]
- [O que NÃO fazer — negativo depois]
</restrições>

<saída>
Formato: [arquivo / texto / diff / comando]
Local: [caminho ou destino]
</saída>

<completion>
O trabalho está concluído quando: [critério verificável e objetivo]
</completion>
```

**Princípios obrigatórios:**
- Positivo antes de negativo nas restrições
- Critério de parada explícito e mensurável — o agente deve saber quando parou
- Formato de saída concreto — nunca ambíguo
- Uma tarefa por prompt — se há múltiplas, decomponha em etapas sequenciais
- Verbos de ação precisos: "analise", "gere", "refatore" — nunca "faça algo com"

### 3. Inferir parâmetros de execução

Para comandos que aceitam `--max-iterations` e `--completion-promise`, use esta tabela:

| Complexidade da tarefa | max-iterations | completion-promise |
|---|---|---|
| 1 objetivo, escopo fechado | 3 | artefato esperado descrito objetivamente |
| 2–3 objetivos, escopo médio | 5 | todos os objetivos verificáveis em sequência |
| Multi-etapa, refatoração profunda | 8 | critério de qualidade + artefato final |
| Experimental / exploratório | 10 | "sistema estável e testado" |

### 4. Executar o comando

Após construir o prompt, **mostre ao usuário** o prompt melhorado e os parâmetros escolhidos com uma linha de justificativa. Então execute:

**Para ralph-loop:**
```
/ralph-loop:ralph-loop PROMPT --max-iterations N --completion-promise "TEXT"
```

Onde:
- `PROMPT` = o prompt estruturado da etapa 2 (como string, com quebras de linha escapadas se necessário)
- `--max-iterations N` = valor inferido pela complexidade
- `--completion-promise "TEXT"` = o `<completion>` do prompt, resumido em 1 frase

**Para outros executores futuros:** esta skill é extensível. Adicione uma seção em `references/` com o padrão de execução do novo executor e referencie aqui.

## Exemplo completo

**Input bruto do usuário:**
> "quero evoluir o agente que gera os testes do meu módulo de pagamento"

**Prompt gerado:**

```
<papel>
Você é um engenheiro de software especialista em testes automatizados Python.
</papel>

<tarefa>
Analise o módulo de pagamento e gere um conjunto de testes unitários que cubra
os casos principais, incluindo casos de erro e edge cases.
</tareda>

<contexto>
Módulo alvo: src/payments/
Testes existentes: tests/test_payments.py (incompletos)
Framework: pytest
</contexto>

<restrições>
- Escreva testes isolados com mocks para dependências externas
- Cubra pelo menos: sucesso, falha por saldo, falha por timeout
- Não altere o código do módulo de pagamento
</restrições>

<saída>
Arquivo: tests/test_payments.py
Formato: pytest com fixtures e parametrize onde aplicável
</saída>

<completion>
O trabalho está concluído quando todos os testes passam com `pytest tests/test_payments.py`
e a cobertura do módulo payments/ é ≥ 80%.
</completion>
```

**Parâmetros inferidos:**
- `--max-iterations 5` (escopo médio: análise + geração + ajuste de mocks)
- `--completion-promise "pytest passa e cobertura ≥ 80%"`

**Comando executado:**
```
/ralph-loop:ralph-loop "<prompt acima>" --max-iterations 5 --completion-promise "pytest passa e cobertura >= 80%"
```
