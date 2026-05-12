# Spec: Guardião Conservador v2

## Position Guard

### Scenario: Rejeitar compra duplicada
- Given o ticker BTC-USD já possui posição aberta
- When um sinal de COMPRA é gerado
- Then a ordem NÃO é executada
- And o log registra "compra rejeitada: já posicionado"

### Scenario: Rejeitar venda fantasma
- Given o ticker BTC-USD NÃO possui posição aberta
- When um sinal de VENDA é gerado
- Then a ordem NÃO é executada
- And o log registra "venda rejeitada: sem posição"

## TP/SL Threshold Price

### Scenario: TP executa no preço exato do threshold
- Given posição aberta em BTC-USD a $80,000
- And TP configurado em +0.50%
- When preço atual é $80,500 (exatamente +0.625%)
- Then a venda executa a $80,400 (preço do threshold = entrada * 1.005)
- And NÃO executa a $80,500 (preço de mercado)

### Scenario: SL executa no preço exato do threshold
- Given posição aberta em BTC-USD a $80,000
- And SL configurado em -0.30%
- When preço atual é $79,700 (-0.375%)
- Then a venda executa a $79,760 (preço do threshold = entrada * 0.997)

## Log Verde/Vermelho

### Scenario: Fechamento em lucro
- When uma posição é fechada com PnL >= 0
- Then o log mostra "[LUCRO] FECHAMENTO {ticker} @ {preco} | PnL +X.XXX% ($+X,XXX.XX)" em verde

### Scenario: Fechamento em prejuízo
- When uma posição é fechada com PnL < 0
- Then o log mostra "[PERDA] FECHAMENTO {ticker} @ {preco} | PnL -X.XXX% ($-X,XXX.XX)" em vermelho

## Heartbeat Enriquecido

### Scenario: Heartbeat a cada 60 ticks
- Given tick_count é múltiplo de 60
- When o heartbeat é disparado
- Then mostra "ticks=N | trades=N WR=N% | Fechados: $X.XX | Aberto: $X.XX (+X.XXX%) | Posições: N"

## Stale Guard

### Scenario: Dados stale bloqueiam novos sinais (silencioso)
- Given o preço do ticker não muda há 2 ticks consecutivos
- When um tick é processado
- Then NENHUMA operação de compra/venda é executada
- And SL/TP continuam funcionando normalmente (não bloqueados por stale)

### Scenario: Dados frescos retornam
- Given stale estava ativo
- When o preço muda no tick seguinte
- Then operações são retomadas normalmente

## ADX +DI/-DI Crossover (validado ML)

### Scenario: Sinal de compra no crossover
- Given +DI cruza acima de -DI
- And ADX >= 25
- And volume_ratio >= 1.0
- Then sinal COMPRA é gerado com TP dinâmico baseado no ADX

### Scenario: Sinal bloqueado por ADX baixo
- Given +DI cruza acima de -DI
- And ADX < 25
- Then sinal é bloqueado (retorna None)

### Scenario: Sinal bloqueado por volume baixo
- Given +DI cruza acima de -DI
- And ADX >= 25
- And volume_ratio < 1.0
- Then sinal é bloqueado (retorna None)

## TP Dinâmico por ADX (validado ML)

### Scenario: TP conservador por faixa de ADX
- When sinal de COMPRA é gerado
- Then TP é mapeado pelo ADX atual:
  - ADX < 20 → TP = 0.30%
  - 20 <= ADX < 30 → TP = 0.40%
  - 30 <= ADX < 40 → TP = 0.50%
  - ADX >= 40 → TP = 0.60%

### Scenario: TP dinâmico por posição
- Given posição aberta com TP = 0.40% (ADX=25)
- When o tick verifica TP
- Then check_price usa o TP da posição (0.40%), não o padrão do tracker

## Volume Filter (validado ML, @deprecated)

> **Nota**: O filtro de volume foi desativado (`_calc_volume_ratio()` retorna `1.0` sempre).
> Motivo: yfinance crypto volume não é confiável. ADX>=25 já filtra whipsaws eficazmente.
> Reativar quando migrar para exchange API direta (Binance).

### Scenario: Volume ratio calculado corretamente
- Given últimos 20 candles com volume médio = 1000
- And último candle com volume = 1200
- When volume_ratio é calculado
- Then volume_ratio = 1.2x (acima do threshold 1.0)
- **Status**: `@deprecated` — sempre retorna 1.0, threshold sempre passa

## Tick com Indicadores Coloridos

### Scenario: Tick sem sinal mostra indicadores
- When evaluate() retorna None
- Then o log mostra "+DI=X.X -DI=X.X | ADX=X.X | gap=X.X | vol=X.Xx"
- And +DI é verde quando lidera, dim quando perde
- And -DI é vermelho quando lidera, dim quando perde
- And ADX é vermelho (<20), amarelo (20-25), verde (>=25)
- And gap é dourado bold (<5 = zona quente), amarelo (5-10), dim (>10)

## Trailing Stop

### Scenario: Ativação após +0.20%
- Given posição aberta a $80,000
- And preço sobe para $80,160 (+0.20%)
- Then trailing stop é ativado a $80,040 (pico * 0.9985)

### Scenario: Trailing sobe com preço
- Given trailing ativo com pico em $80,300
- When preço sobe para $80,500
- Then trailing stop sobe para $80,380 (novo pico * 0.9985)

### Scenario: Trailing nunca abaixo do breakeven
- Given entrada a $80,000 e trailing ativo
- When trailing calculado seria < $80,000
- Then trailing stop fica em $80,000 (breakeven)

## Rate Limiting

### Scenario: TTL Cache evita request duplicado
- Given cotação de BTC-USD foi buscada há 15s
- When nova consulta ao mesmo ticker em < 30s
- Then retorna dados do cache sem chamar Yahoo

### Scenario: Backoff em rate limit
- When Yahoo retorna erro (429 ou exceção)
- Then retry com espera exponencial (2^attempt segundos)
- And máximo 3 tentativas antes de falhar
