## Context

O módulo `core/paper` segue DDD com 4 camadas (domain, application, ports/adapters, facade). O StrategyWorker atual é um stub no facade/sandbox que só faz log. O pipeline de execução real (ExecutorDeOrdem → BrokerPort → EventBus) já está implementado no domain layer. Faltam: (1) estratégias como domain objects puros, (2) conexão do StrategyWorker ao pipeline, (3) wiring no orchestrator.

Ticker padrão: BTC-USD (mercado 24/7, sem dependência de horário de bolsa).

## Goals / Non-Goals

**Goals:**
- Primeiro trade automático funcional (Missão A do roadmap)
- Estratégias como domain objects testáveis sem infraestrutura
- StrategyProtocol pluggable para futuras estratégias (Sniper, Momentum)
- Stop Loss / Take Profit automatizados por posição

**Non-Goals:**
- Backtesting (Missão D — futuro)
- Múltiplas estratégias competindo (Missão E — futuro)
- Painel Discord (Missão B/C — futuro)
- Otimização de parâmetros de SMA

## Decisions

### D1: Estratégias no domain layer (não na facade)

**Decisão:** `domain/strategies/` como pacote de domain objects puros.

**Razão:** Estratégias são regras de negócio — recebem DadosMercado (VO) e retornam SinalEstrategia (VO). Não dependem de async, ports, ou infraestrutura. Testáveis com dados sintéticos sem mocks.

**Alternativa descartada:** Estratégias no facade/sandbox — acoplaria regras de negócio à infraestrutura de workers.

### D2: StrategyProtocol como typing.Protocol (não ABC)

**Decisão:** Usar `typing.Protocol` para o contrato de estratégia.

**Razão:** Duck typing — qualquer objeto com `name: str` e `evaluate(dados) → SinalEstrategia | None` é uma estratégia. Sem herança obrigatória, sem imports acoplados.

### D3: SMA crossover com detecção de cruzamento (não apenas posição)

**Decisão:** Guardião Conservador detecta quando SMA curta cruza SMA longa (comparando período atual vs anterior).

**Razão:** Apenas verificar "SMA5 > SMA15" gera sinais repetidos a cada tick. Detectar o cruzamento (SMA5 estava abaixo e agora está acima) gera um sinal único por evento.

### D4: PositionTracker separado da estratégia

**Decisão:** PositionTracker é um component independente que gerencia SL/TP, não parte do GuardiãoConservador.

**Razão:** Separação de responsabilidades — a estratégia decide entrada/saída por sinal; o tracker decide saída por preço-limite. Qualquer estratégia pode usar o mesmo tracker.

### D5: Quantidade fixa (100 unidades) por ordem

**Decisão:** Quantidade fixa de 100 unidades por ordem no primeiro MVP.

**Razão:** Simplifica o MVP. Evita complexidade de dimensionamento de posição (fractional shares, risk-based sizing). Evolui posteriormente.

## Metodologia: TDD Estrito

Este change SHALL seguir **Test-Driven Development (TDD) Estrito** — `Red → Green → Refactor`.

**Regras:**
1. **RED** — Cada `#### Scenario:` do spec vira um teste. O teste DEVE falhar antes da implementação.
2. **GREEN** — Implementar o código mínimo para passar. Sem otimização, sem refatoração.
3. **REFACTOR** — Limpar código mantendo todos os testes verdes.
4. **NUNCA** implementar código de produção sem um teste falhando antes.
5. **NUNCA** pular a etapa RED.

**Ordem de implementação por grupo de tasks:**
- Grupo 1 (estrutura + VOs): escrever testes 2.1–2.4 → RED → implementar 1.1–1.5 → GREEN → REFACTOR
- Grupo 2 (tracker): escrever testes 3.2–3.5 → RED → implementar 3.1 → GREEN → REFACTOR
- Grupo 3 (guardião): escrever testes 4.4–4.6 → RED → implementar 4.1–4.3 → GREEN → REFACTOR
- Grupo 4 (worker): escrever testes 5.4–5.6 → RED → implementar 5.1–5.3 → GREEN → REFACTOR
- Grupo 5 (wiring): atualizar 6.1–6.2 → teste de integração 6.3

**Estrutura de testes:**
```
tests/unit/paper/domain/strategies/
├── test_signal.py
├── test_position_tracker.py
├── test_guardiao_conservador.py
└── test_strategy_worker.py
```

## Risks / Trade-offs

- **[Yahoo Finance rate limiting]** → O PaperBroker já usa YahooFinanceFeed que tem delay. Para BTC-USD o impacto é menor (dados disponíveis 24/7). Intervalo do orchestrator em 60s é seguro.
- **[Crossover em dados estáticos]** → SMA crossover em dados de 30 períodos com tick a cada 60s pode demorar para gerar primeiro sinal. Aceitável para MVP — o objetivo é validar o pipeline, não a lucratividade.
- **[Posição única por ticker]** → O tracker mantém apenas 1 posição por ticker. Se a estratégia gerar COMPRA duas vezes seguidas, a segunda é ignorada. Protege contra sobreposição.

> "Decisões de arquitetura são apostas informadas" – made by Sky 🎯
