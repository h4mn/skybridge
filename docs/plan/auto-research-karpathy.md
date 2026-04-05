# Auto Research - Andrej Karpathy

> **Transcrição do vídeo:** [Auto Research - How AI Runs Experiments While You Sleep](https://www.youtube.com/watch?v=4mQ9wQo6Bzk)

---

## 📋 O Que É Auto Research?

**Auto Research** é um projeto open-source de **Andrej Karpathy** que automatiza o loop de experimentação para treinar modelos de IA.

### Problema Que Resolve

```
Loop Manual de Treinamento:
1. Escrever código
2. Rodar e esperar completar
3. Checar score (perda/accurácia)
4. Se melhorou → manter
5. Se piorou → desfazer e tentar algo diferente
6. Repetir 100x manualmente
```

### Solução: Loop Automatizado

```
Auto Research Loop (IA Agent):
1. IA lê o código e instruções
2. IA propõe mudança (ex: learning rate decay)
3. Roda treinamento automaticamente
4. Checa score
5. Se melhorou → salva mudança
6. Se piorou → desfaz e tenta outra ideia
7. Repete sozinho 126x durante a noite
```

---

## 🏗️ Arquitetura (3 Arquivos)

```
auto-research/
├── prepare.py    # Setup dos dados (roda 1x)
├── train.py      # Código de treinamento (modificado pelo AI)
└── program.md    # Instruções para o AI agent
```

### program.md (Mais Importante)

Diz ao AI:
- O que focar
- Qual métrica otimizar
- Quais regras seguir

### Exemplo de Execução

```
Experimento 1:
├── AI: "Vou mudar learning rate de fixo para decay"
├── Score: 0.997 → 0.993 ✅ (menor é melhor)
└── AI: Salva mudança!

Experimento 2:
├── AI: "Vou adicionar dropout"
├── Score: 0.993 → 1.050 ❌ (piorou)
└── AI: Desfaz mudança, loga erro

Experimento 3:
├── AI: "Vou aumentar attention heads"
├── Score: 0.993 → 0.951 ✅
└── AI: Salva mudança!

Resultado (15 min): 3 experimentos
Resultado (noite inteira): 82 experimentos 🚀
```

---

## 🔄 O Padrão Universal (Não Só Para IA)

Auto Research foi feito para treinar IA, mas o **padrão é universal**:

```
1. Ler instruções
2. Ter ideia
3. Fazer mudança
4. Testar
5. Medir resultado
6. Se melhor → manter
7. Se pior → descartar
8. Repetir
```

Isso serve para **qualquer coisa** que você queira otimizar!

---

## ✅ Checklist: Auto Research Funciona Para Seu Caso?

**Quanto mais "SIM", melhor:**

| # | Pergunta | Por Que Importa |
|---|----------|-----------------|
| 1 | **Métrica única?** (open rate, lucro, CTR) | Loop precisa otimizar um número |
| 2 | **Teste rápido?** (segundos/horas) | Testes lentos (meses) são impraticáveis |
| 3 | **Muitos experimentos?** (dezenas/centenas) | 1 teste diz nada, volume é mágico |
| 4 | **Falha segura?** (só undo, sem perder dinheiro) | Fracasso não pode custar clientes reais |
| 5 | **Medida consistente?** (baseline estável) | Testar contra alvo que muda = ruído |
| 6 | **Resultado numérico?** (não "sentimento") | AI não avalia julgamento humano |

---

## 🎯 Use Cases por Tier

### **Tier 1: Funciona Perfeito** ⭐⭐⭐

Loop rápido, barato, tudo objetivo.

| Use Case | Métrica | Velocidade | Custo |
|----------|---------|------------|------|
| **Trading Backtest** | Sharpe Ratio | Segundos | Zero (simulado) |
| **Code Benchmarking** | Execution Speed | Segundos | Zero |
| **Compiler Optimization** | Performance | Segundos | Zero |

**Trading Backtest Exemplo:**
```
1. AI escreve estratégia (regras buy/sell)
2. Testa contra 2 anos de dados históricos
3. Mede Sharpe Ratio (retorno/risco)
4. Roda 1000x durante a noite
5. Sem risco real (tudo simulado)
```

### **Tier 2: Funciona Com Trade-offs** ⭐⭐

Padrão funciona, mas **lento** porque testa contra humanos reais.

| Use Case | Métrica | Velocidade | Trade-off |
|----------|---------|------------|-----------|
| **Cold Email** | Open Rate | Horas | Velocidade |
| **Ad Copy** | CTR / CPA | Dias | Custo ($) |
| **YouTube Titles** | CTR | Dias | Volume |
| **Newsletters** | Open Rate | Dias | Velocidade |
| **Chatbot Scripts** | Conversão | Dias | Velocidade |

**Cold Email Exemplo:**
```
1. AI escreve variante de email
2. Envia para 300 pessoas
3. Aguarda horas por opens
4. Se melhorou → mantém
5. Se piorou → tenta outra

Resultado: 20-30 experimentos/semana (vs 126/noite em Tier 1)
```

### **Tier 3: NÃO Funciona** ❌

Condições fundamentais **não podem ser atendidas**.

| Use Case | Por Que Falha |
|----------|---------------|
| **SEO Optimization** | Feedback leva semanas/meses; algoritmo muda; ruído alto |
| **SaaS Pricing** | Testes levam meses; preço errado perde clientes |
| **Brand/UX Design** | Sem métrica objetiva (número vs sentimento) |
| **General Research** | Pergunta "é completo?" é subjetiva |
| **Finance Ops** | Muito amplo; sem métrica/teste específico |

---

## 💡 Insights Principais

### 1. O Segredo é o Volume

> "One experiment tells you nothing. You need dozens at minimum and ideally hundreds. The magic is in the volume."

### 2. Velocidade = Quantidade de Experimentos

- **Tier 1:** 126 experimentos/noite
- **Tier 2:** 20-30 experimentos/semana
- **Tier 3:** Impraticável

### 3. Custo de Fracasso

- **Simulado (trading)**: Zero custo
- **Real (ads)**: Custo $ por experimento
- **Perigoso (pricing)**: Pode perder clientes

### 4. Consistência de Medida

Se o alvo do teste muda entre experimentos → ruído, não dados.

---

## 🔗 Conexão Skyvern

```
Andrej Karpathy (Auto Research)
    ↓ (inspirou)
BabyAGI / AutoGPT (task-driven agents)
    ↓ (usou como base)
Skyvern Forge Agent (browser automation)
```

**Auto Research** = Otimização automática de hyperparâmetros
**Skyvern** = Automação de browser com visão computacional

Ambos usam o **mesmo padrão**: Agent AI que leem, pensam, agem, medem, iteram.

---

## 📚 Fonte

- **Vídeo:** [Auto Research - How AI Runs Experiments While You Sleep](https://www.youtube.com/watch?v=4mQ9wQo6Bzk)
- **Autor:** Andrej Karpathy
- **Repositório:** https://github.com/karpathy/llm.c (provavelmente relacionado)

---

## 🤔 Aplicações na Skybridge?

**Possíveis usos do padrão Auto Research na Skybridge:**

1. **Otimização de Prompts Sky**
   - Métrica: Satisfação do usuário (score 1-5)
   - Velocidade: Horas/dias
   - Tier: 2 (trade-offs)

2. **Otimização de STT/TTS Parameters**
   - Métrica: WER (Word Error Rate) / Latência
   - Velocidade: Minutos
   - Tier: 1 (perfeito!)

3. **Otimização de Workflows**
   - Métrica: Tempo de conclusão
   - Velocidade: Minutos
   - Tier: 1 (perfeito!)

---

> "A mágica está no volume de experimentos, não na inteligência individual" – made by Sky 🚀
