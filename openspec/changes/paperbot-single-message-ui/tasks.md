# Tasks - PaperBot Single-Message UI

Lista de implementação para refatorar o PaperBot para arquitetura single-message.

## 1. Foundation - Single Message Architecture

- [ ] 1.1 Modificar comando `!paper` para usar `edit(content=None, embed=..., view=...)`
- [ ] 1.2 Validar que embed aparece corretamente (sem texto residual)
- [ ] 1.3 Garantir que apenas 1 mensagem existe no tópico (thread criada, mensagem editada)
- [ ] 1.4 Testar que `content=None` é compatível com discord.py 2.7.1

## 2. State Machine & ViewContext

- [ ] 2.1 Criar enum `ViewState` com estados: DASHBOARD, ASSET_LIST, POSITION, ASSET_DETAIL
- [ ] 2.2 Criar dataclass `ViewContext` com: state, selected_asset, message_id, channel_id, user_id
- [ ] 2.3 Criar classe `PortfolioStateMachine` para gerenciar transições de estado
- [ ] 2.4 Implementar método `transition(ctx, action)` que retorna novo estado
- [ ] 2.5 Implementar método `register(message_id, channel_id, user_id)` que cria ViewContext

## 3. View Dinâmica por Estado

- [ ] 3.1 Criar classe `PortfolioPanelView(View)` com botões dinâmicos
- [ ] 3.2 Implementar `_add_dashboard_buttons()` - botões: 💰 Ativos, 📊 Posição
- [ ] 3.3 Implementar `_add_asset_list_buttons()` - botões: 🏠 Home + botões por ativo
- [ ] 3.4 Implementar `_add_position_buttons()` - botão: 🏠 Home
- [ ] 3.5 Implementar `_add_asset_detail_buttons()` - botões: 🏠 Home, ⬅️ Voltar, 📈 Gráfico
- [ ] 3.6 Implementar lógica de seleção de ativo (BTC, ETH, PETR4F, etc.)

## 4. Dashboard View Implementation

- [ ] 4.1 Criar callback `_on_dashboard()` para renderizar painel Dashboard
- [ ] 4.2 Integrar `BinancePublicFeed.get_ticker()` para dados em tempo real
- [ ] 4.3 Criar embed com cards de Resumo de Corretoras (Binance/Yahoo)
- [ ] 4.4 Criar embed com card de Desempenho (Maior Alta, Maior Lucro, Sharpe)
- [ ] 4.5 Implementar fallback para dados mockados se API falhar

## 5. Asset List View Implementation

- [ ] 5.1 Criar callback `_on_assets()` para transitar para ASSET_LIST
- [ ] 5.2 Criar tabela de ativos com dados de múltiplas fontes
- [ ] 5.3 Implementar botão para cada ativo (BTC, ETH, etc.) que chama `_on_select_asset()`
- [ ] 5.4 Criar `_on_back_to_assets()` para voltar da seleção para a lista
- [ ] 5.5 Buscar dados em tempo real de Binance, Yahoo Finance, etc.

## 6. Asset Detail View Implementation

- [ ] 6.1 Criar callback `_on_select_asset(asset)` para selecionar ativo específico
- [ ] 6.2 Criar callback `_on_asset_chart()` para gerar gráfico candlestick
- [ ] 6.3 Integrar `BinancePublicFeed.get_klines()` para dados de candlestick
- [ ] 6.4 Implementar geração de gráfico com matplotlib
- [ ] 6.5 Enviar gráfico como anexo via `interaction.followup.send()`
- [ ] 6.6 Criar embed com dados de 24h (preço, variação, volume, máxima, mínima)

## 7. Persistent Menu Implementation

- [ ] 7.1 Modificar `_add_*_buttons()` para sempre incluir botões do menu
- [ ] 7.2 Garantir que botões de navegação (Dashboard, Posição, Configuração) estão sempre visíveis
- [ ] 7.3 Implementar callback para botão "🏠 Home" que volta para DASHBOARD
- [ ] 7.4 Implementar callback para botão "⬅️ Voltar" (context-aware)

## 8. Integration & Data Sources

- [ ] 8.1 Verificar que `BinancePublicFeed` está funcionando corretamente
- [ ] 8.2 Adicionar cache simples (30s) para evitar rate limiting da API Binance
- [ ] 8.3 Implementar fallback para dados mockados se Binance falhar
- [ ] 8.4 Adicionar handling para exceções de rede (requests.exceptions)

## 9. Testing & Validation

- [ ] 9.1 Testar comando `!paper` cria tópico com 1 mensagem
- [ ] 9.2 Testar navegação Dashboard → Asset List → Dashboard sem criar mensagens extras
- [ ] 9.3 Testar seleção de ativo (BTC/ETH) → Asset Detail → Asset List
- [ ] 9.4 Testar geração de gráfico candlestick
- [ ] 9.5 Validar que content=None limpa texto anterior corretamente
- [ ] 9.6 Testar compatibilidade com discord.py 2.7.1

## 10. Code Quality & Documentation

- [ ] 10.1 Remover código mock/placeholder
- [ ] 10.2 Adicionar docstrings em todos os métodos públicos
- [ ] 10.3 Atualizar MEMORY.md com progresso e learnings
- [ ] 10.4 Remover debug logs desnecessários
- [ ] 10.5 Garantir que todos os estados têm testes

---

> "Especificações prontas, implementation começando" – made by Sky 🚀
