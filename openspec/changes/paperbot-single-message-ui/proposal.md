# PaperBot Single-Message UI

## Why

O PaperBot atual tem problemas de usabilidade no Discord: cada interação cria novas mensagens no tópico, deixando o histórico poluído e confuso. O usuário quer uma interface limpa onde apenas uma mensagem existe sempre, sendo atualizada dinamicamente conforme a navegação.

## What Changes

- **Single Message Architecture**: Apenas 1 mensagem permanente no tópico do Discord, atualizada via `edit()` a cada interação
- **Menu Persistente**: Botões de navegação sempre visíveis no topo (Dashboard, Posição, Configuração)
- **Substituição de Conteúdo**: O conteúdo principal é substituído dinamicamente sem criar novas mensagens
- **4 Telas Principais**: Dashboard (resumo), Select Ativos (tabela), Posição (lucro/prejuízo), Ativo Detalhe (gráfico)

## Capabilities

### New Capabilities
- `discord-single-message`: Sistema de UI que mantém apenas 1 mensagem no tópico, atualizada via `edit()` com `content=None` para limpar texto anterior
- `discord-persistent-menu`: Menu de navegação sempre presente no topo da view (Dashboard, Posição, Configuração)
- `dashboard-view`: Tela inicial com resumo de corretoras (Binance/Yahoo) e desempenho (maior alta, maior lucro, Sharpe)
- `asset-list-view`: Tela com tabela de ativos (BTCUSDT, PETR4F, MNQ1!, etc) com preços em tempo real
- `position-view`: Tela com posições abertas/fechadas, lucro/prejuízo total e por ativo
- `asset-detail-view`: Tela com gráfico candlestick do ativo selecionado + menu de negociação (Comprar/Vender)

### Modified Capabilities
- `SPEC015-discord-portfolio-components`: Adiciona princípio de single-message (apenas 1 mensagem ativa no tópico)

## Impact

**Código afetado:**
- `src/core/paper/facade/sandbox/paper.py` - Refatorar para single-message architecture

**Novas dependências:**
- Nenhuma (usa discord.py existente)

**Sistemas afetados:**
- PaperBot Sandbox (bot Discord)

**Breaking Changes:**
- Nenhum (mudança apenas de UX, não de API)

---

> "Uma mensagem para governar todas" – made by Sky 🎯
