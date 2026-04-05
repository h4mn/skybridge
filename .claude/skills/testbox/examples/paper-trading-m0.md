# Exemplo: Paper Trading M0

Este exemplo demonstra o uso da skill `testbox` no cenário real do Paper Trading via Discord MCP.

## Contexto

- **Sistema:** Paper Trading (simulador de operações financeiras)
- **Interface:** Discord MCP
- **API:** `src.core.paper.facade.api.app`
- **Objetivo:** Testar M0 antes de continuar com M1

---

## Fase 1: Modo BLACK

### Comando

```
testbox black paper-trading
```

### Execução do Agente

O agente opera como **usuário do sistema**, sem acessar código interno:

1. **Conecta ao Discord MCP**
2. **Testa operações:**
   - Comprar BTC-USD @ mercado
   - Verificar posições
   - Consultar saldo
   - Verificar PnL
3. **NÃO lê:**
   - `paper_state.json`
   - Código interno
   - Arquivos de configuração

### Resultado: insights-paper-trading.md

```markdown
---
target: paper-trading
mode: black
generated_at: 2026-03-28T16:00:00-03:00
ready_for_white: true
---

# Insights [BLACK] - Paper Trading M0

## Resumo Executivo

Sistema de paper trading funcional para operações básicas de compra/venda a mercado.
Identificados 4 gaps de funcionalidade e 2 bugs que impactam a experiência do usuário.

---

## Informações do Sistema

| Campo | Valor |
|-------|-------|
| **Sistema** | Paper Trading |
| **Interface** | Discord MCP |
| **Versão** | M0 |
| **Ambiente** | Produção |
| **Data da Análise** | 2026-03-28T16:00:00-03:00 |

---

## Entradas Testadas

| ID | Entrada | Tipo | Obrigatório | Descrição |
|----|---------|------|-------------|-----------|
| IN-1 | buy {ativo} {qty} | comando | Sim | Comprar ativo a mercado |
| IN-2 | sell {ativo} {qty} | comando | Sim | Vender ativo a mercado |
| IN-3 | positions | comando | Não | Listar posições abertas |
| IN-4 | balance | comando | Não | Consultar saldo |
| IN-5 | pnl | comando | Não | Verificar PnL |

---

## Cenários Testados

### Cenário C-1: Comprar BTC-USD

- **Dado:** Saldo disponível de $213k USD
- **Quando:** Executo `buy BTC-USD 1`
- **Então:** Posição aberta de 1 BTC-USD
- **Observado:** Posição aberta @ $66,796.66
- **Status:** ✅

### Cenário C-2: Verificar Posições

- **Dado:** Posição aberta de 1 BTC-USD
- **Quando:** Executo `positions`
- **Então:** Lista com 1 posição
- **Observado:** Lista correta com preço médio
- **Status:** ✅

### Cenário C-3: Consultar Saldo

- **Dado:** Após compra de 1 BTC
- **Quando:** Executo `balance`
- **Então:** Saldo atualizado (USD - valor da compra)
- **Observado:** Saldo ~$146k USD (correto)
- **Status:** ✅

### Cenário C-4: Ordem Limit (não existe)

- **Dado:** Qualquer estado
- **Quando:** Tento executar ordem limit
- **Então:** Ordem registrada com preço alvo
- **Observado:** Funcionalidade não disponível
- **Status:** ❌ (GAP)

---

## Gaps Identificados

| ID | Descrição | Impacto | Prioridade |
|----|-----------|---------|------------|
| GAP-1 | Sem ordens limit (só mercado) | Alto | P1 |
| GAP-2 | Mistura BRL/USD sem conversão automática | Médio | P2 |
| GAP-3 | Race condition em múltiplas instâncias | Alto | P1 |
| GAP-4 | Sem endpoint de saque | Baixo | P3 |

### GAP-1: Sem Ordens Limit

- **Descrição:** Sistema só suporta ordens a mercado
- **Impacto:** Usuário não pode definir preço alvo de entrada/saída
- **Frequência:** Sempre (funcionalidade inexistente)
- **Reprodução:** Tentar executar qualquer ordem limit

### GAP-3: Race Condition

- **Descrição:** Múltiplas instâncias acessando `paper_state.json`
- **Impacto:** Perda de dados, inconsistência de estado
- **Frequência:** Quando múltiplos processos rodam simultaneamente

---

## Bugs Encontrados

| ID | Descrição | Severidade | Reproduzível | Status |
|----|-----------|------------|--------------|--------|
| BUG-1 | TypeError float/Decimal no portfolio | Alto | Sim | Corrigido |
| BUG-2 | Field mismatch id/ordem_id nas ordens | Médio | Sim | Corrigido |

### BUG-1: TypeError float/Decimal

- **Descrição:** Erro de tipo ao misturar float e Decimal em cálculos
- **Severidade:** Alto (quebra funcionalidade)
- **Reprodução:**
  1. Abrir posição
  2. Calcular PnL
  3. TypeError é lançado
- **Resultado Esperado:** Cálculo correto do PnL
- **Resultado Real:** Exceção TypeError
- **Status:** ✅ Corrigido

### BUG-2: Field Mismatch

- **Descrição:** API retorna `id` mas código espera `ordem_id`
- **Severidade:** Médio (quebra integração)
- **Status:** ✅ Corrigido

---

## Hipóteses para WHITE

- [ ] Verificar se GAP-1 é limitação de design ou implementação faltando
- [ ] Investigar onde acontece a conversão BRL/USD (ou falta dela)
- [ ] Confirmar estrutura de `paper_state.json` e locks
- [ ] Entender arquitetura de múltiplas instâncias

---

## Próximos Passos

1. Rodar `testbox white paper-trading`
2. Analisar arquivos em `src/core/paper/`
3. Foco: GAP-1 e GAP-3 (prioridade P1)
```

---

## Fase 2: Modo WHITE

### Comando

```
testbox white paper-trading
```

### Execução do Agente

O agente lê os insights e analisa o código:

1. **Lê** `insights-paper-trading.md`
2. **Abre** arquivos em `src/core/paper/`
3. **Correlaciona** cada gap/bug com implementação
4. **Gera** análise estruturada

### Resultado: analysis-paper-trading.md

```markdown
---
target: paper-trading
mode: white
generated_at: 2026-03-28T16:30:00-03:00
insights_source: insights-paper-trading.md
---

# Análise [WHITE] - Paper Trading M0

## Resumo Executivo

Sistema bem estruturado com fachada clara em `api.app`. Gaps identificados são 
principalmente funcionalidades não implementadas (não bugs). Race condition 
requer atenção imediata.

---

## Arquivos Analisados

| Arquivo | Relevância | Gap/Bug Relacionado |
|---------|------------|---------------------|
| `src/core/paper/facade/api.app.py` | Alta | Todos |
| `src/core/paper/engine.py` | Alta | GAP-1, GAP-3 |
| `src/core/paper/portfolio.py` | Alta | BUG-1, GAP-2 |
| `src/core/paper/state.py` | Média | GAP-3 |
| `paper_state.json` | Baixa | GAP-3 (não analisado diretamente) |

---

## Correlações

| ID | Comportamento (BLACK) | Implementação (WHITE) | Arquivo:Linha | Status |
|----|----------------------|----------------------|---------------|--------|
| C-1 | Compra a mercado funciona | `place_order(type='market')` | `engine.py:45` | ✅ |
| C-2 | Ordem limit não disponível | `place_order()` só aceita market | `engine.py:52` | ⚠️ |
| C-3 | TypeError float/Decimal | Mistura de tipos em cálculos | `portfolio.py:78` | ✅ Fix |
| C-4 | Race condition | Sem lock no acesso ao state | `state.py:23` | ❌ |

---

## Análise de Gaps

### GAP-1: Sem Ordens Limit

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/core/paper/engine.py:52` |
| **Causa Raiz** | Método `place_order()` hardcoded para `type='market'` |
| **Solução Proposta** | Adicionar parâmetro `order_type` e lógica de price |
| **Complexidade** | Média |
| **Dependências** | Nenhuma |

**Código Atual:**
```python
def place_order(self, symbol: str, side: str, quantity: Decimal) -> Order:
    # Hardcoded para mercado
    price = self._get_market_price(symbol)
    return self._execute_order(symbol, side, quantity, price)
```

**Sugestão:**
```python
def place_order(
    self, 
    symbol: str, 
    side: str, 
    quantity: Decimal,
    order_type: str = 'market',  # NOVO
    limit_price: Decimal | None = None  # NOVO
) -> Order:
    if order_type == 'limit' and limit_price is None:
        raise ValueError("limit_price required for limit orders")
    
    price = limit_price if order_type == 'limit' else self._get_market_price(symbol)
    
    if order_type == 'limit':
        return self._register_limit_order(symbol, side, quantity, price)
    return self._execute_order(symbol, side, quantity, price)
```

### GAP-3: Race Condition

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/core/paper/state.py:23` |
| **Causa Raiz** | Acesso direto ao JSON sem lock |
| **Complexidade** | Complexa |
| **Risco** | Alto (perda de dados) |

🔍 **Bug complexo detectado.**

**Motivo:** Multi-componente (state → engine → API), envolve concorrência

**Sugestão:** Usar `systematic-debugging` para investigar:
```
systematic-debugging skill
Contexto: Race condition em paper_state.json
Arquivos: state.py, engine.py
Hipótese: Múltiplos processos escrevendo simultaneamente
```

---

## Recomendações de Complexidade

### Itens Simples → Code Mode Direto

| Item | Ação | Arquivo |
|------|------|---------|
| BUG-1 | ✅ Já corrigido | - |
| BUG-2 | ✅ Já corrigido | - |

### Itens Médios → Backlog

| Item | Ação | Prioridade |
|------|------|------------|
| GAP-1 | Implementar ordens limit | P1 |
| GAP-2 | Adicionar conversão BRL/USD | P2 |
| GAP-4 | Criar endpoint de saque | P3 |

### Itens Complexos → systematic-debugging

| Item | Motivo | Próximo Passo |
|------|--------|---------------|
| GAP-3 | Concorrência, múltiplos componentes | systematic-debugging |

---

## Plano de Ação

### Fase 1: Investigar Race Condition (Imediato)

```
systematic-debugging skill
Contexto: Race condition no acesso a paper_state.json
```

### Fase 2: Implementar Ordens Limit (Curto Prazo)

1. Modificar `engine.py` para aceitar `order_type`
2. Criar estrutura para ordens pendentes
3. Adicionar comando Discord para ordens limit

### Fase 3: Conversão BRL/USD (Médio Prazo)

1. Integrar API de câmbio
2. Adicionar parâmetro de moeda
3. Converter automaticamente

---

## Handoff

### Para systematic-debugging

```markdown
## GAP-3: Race Condition

**Contexto:** Múltiplas instâncias acessando paper_state.json simultaneamente
**Arquivos:** state.py, engine.py
**Comando:** systematic-debugging skill
```

### Para Backlog

```markdown
## Issues para Criar

1. **GAP-1: Implementar ordens limit**
   - Tipo: feature
   - Prioridade: P1
   - Arquivos: engine.py, api.app.py

2. **GAP-2: Conversão automática BRL/USD**
   - Tipo: feature
   - Prioridade: P2
   - Arquivos: portfolio.py

3. **GAP-4: Endpoint de saque**
   - Tipo: feature
   - Prioridade: P3
```
```

---

## Fluxo Visual

```mermaid
sequenceDiagram
    participant U as Usuário
    participant B as testbox:black
    participant I as insights.md
    participant W as testbox:white
    participant D as systematic-debugging
    participant BL as Backlog

    Note over U,BL: Fase 1 - Observação
    U->>B: testbox black paper-trading
    B->>B: Testa via Discord MCP
    B->>B: NÃO lê código
    B->>I: Gera insights
    Note in I: GAP-1 a GAP-4<br/>BUG-1 e BUG-2
    
    Note over U,BL: Fase 2 - Análise
    U->>W: testbox white paper-trading
    W->>I: Lê insights
    W->>W: Analisa src/core/paper/
    W->>W: Correlaciona
    
    Note over U,BL: Fase 3 - Handoff
    W->>BL: GAP-1, GAP-2, GAP-4 → Issues
    W->>D: GAP-3 → systematic-debugging
    D->>BL: Após investigação → Issue detalhada
```

---

## Lições Aprendidas

1. **BLACK primeiro** - Observação sem viés de implementação
2. **Documentar tudo** - Gaps e bugs ficam rastreáveis
3. **Handoff inteligente** - Complexidade determina próximo passo
4. **Rastreabilidade** - Cada item tem ID único para acompanhar
