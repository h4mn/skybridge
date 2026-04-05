# MEMORY - Sandbox Paper Bot

## [2026-04-01 01:24 UTC] - Sky usando Roo Code via GLM-5

**Tarefa:** Adicionar comando !paper.

**Arquivos Modificados:**
- `src/core/paper/facade/sandbox/paper.py`

**Resumo das Alterações:**
- Adicionado método `_setup_commands()` para registrar comandos do bot
- Comando `!paper` responde "PortfolioPanelView:MAIN"
- Chamada de `_setup_commands()` adicionada ao `__init__`

---

## [2026-04-01 01:15 UTC] - Sky usando Roo Code via GLM-5

**Tarefa:** Adicionar perfil de depuração VSCode (F5).

**Arquivos Criados:**
- `.vscode/launch.json`

**Resumo das Alterações:**
Criada configuração de debug para executar o Paper Bot como módulo Python:
- Nome: "Paper Bot (módulo)"
- Tipo: debugpy
- Executa: `python -m src.core.paper.facade.sandbox.paper`
- Console integrado do terminal

---

## [2026-04-01 01:13 UTC] - Sky usando Roo Code via GLM-5

**Tarefa:** Adicionar carregamento do token via python-dotenv.

**Arquivos Modificados:**
- `src/core/paper/facade/sandbox/paper.py`

**Resumo das Alterações:**
- Adicionado import do `dotenv.load_dotenv`
- Token agora lido de `DISCORD_PAPER_BOT_TOKEN` via `.env` na raiz do projeto
- Usa `Path.cwd()` para compatibilidade com execução modular (`python -m src.core.paper.facade.sandbox.paper`)

---

## [2026-04-01 01:08 UTC] - Sky usando Roo Code via GLM-5

**Tarefa:** Refatoração do bot Discord para orientação a objetos.
**Arquivos Modificados:**
- `src/core/paper/facade/sandbox/paper.py`

**Resumo das Alterações:**
Refatoração completa do código procedural para OOP:
- Criada classe `PaperBot` encapsulando toda a lógica do bot Discord
- Configuração de intents movida para método estático `_configure_intents()`
- Event handlers (`on_ready`, `on_message`) transformados em métodos de instância privados
- Setup de events centralizado no método `_setup_events()`
- Classe `PaperAppHelloWorld` agora atua como fachada para a aplicação
- Token pode ser injetado via construtor (útil para testes)
- Propriedade `bot` expõe a instância do Discord bot
- Correção de tipo com `getattr()` para acessar `channel.name`

**Próximos Passos (se aplicável):**
- Considerar adicionar type hints para `discord.abc.GuildChannel` se necessário
- Avaliar extração de `CHANNEL_ID` para configuração externa

---

## [2026-03-31 23:59 UTC] - Sky usando Claude Code

**Tarefa:** POC Binance Public Feed + Heartbeat Command + Real-time Data Integration

**Arquivos Modificados:**
- `src/core/paper/facade/sandbox/paper.py`

**Resumo das Alterações:**

### ✅ Implementado

#### 1. BinancePublicFeed Class
```python
class BinancePublicFeed:
    """Feed de dados públicos da Binance - sem autenticação."""
    BASE_URL = "https://api.binance.com"

    @classmethod
    def get_ticker(cls, symbol: str) -> dict
    @classmethod
    def get_price(cls, symbol: str) -> float
    @classmethod
    def get_klines(cls, symbol: str, interval: str, limit: int) -> list
    @classmethod
    def get_portfolio_value(cls, holdings: dict[str, float]) -> dict
```

#### 2. Comando !heartbeat
- Mostra dados em tempo real da Binance (BTC/ETH)
- Calcula valor do portfólio
- Exibe latência da API
- Status do sistema (operacional/degradado)
- Discord Embed colorido (verde)

#### 3. Dados Reais em Todos os Estados
| Estado | Dados da Binance |
|--------|------------------|
| MAIN | Preços BTC/ETH, valor portfolio, variações 24h |
| EXPANDED | Posições detalhadas, PnL, contagem de ativos |
| ASSET_DETAIL | Ticker 24h por ativo (preço, %, volume) |

#### 4. Holdings Mock Constants
```python
HOLDINGS = {"BTC": 0.01234, "ETH": 0.45678, "USDT": 500.00}
```

#### 5. API Endpoints Utilizados
| Endpoint | Propósito |
|----------|-----------|
| `/api/v3/ticker/24hr` | Dados de ticker 24h |
| `/api/v3/klines` | Candles para gráficos |
| `/api/v3/ticker/price` | Preço atual |

### ⏳ Pendente

#### Gráficos (POC)
- [ ] Gerar chart matplotlib com klines Binance
- [ ] Enviar imagem para Discord
- [ ] Botão "Gráfico" no estado ASSET_DETAIL

### 📋 Comandos Disponíveis
| Comando | Descrição | Estado |
|---------|-----------|--------|
| `!paper` | Abre painel de portfólio | ✅ |
| `!heartbeat` | Mostra pulsação do sistema | ✅ |

### 🎨 Cores dos Embeds
| Cor | Hex | Uso |
|-----|-----|-----|
| Verde | 0x2ECC71 | MAIN, Heartbeat |
| Azul | 0x3498DB | EXPANDED |
| Laranja | 0xF39C12 | ASSET_DETAIL |
| Vermelho | 0xE74C3C | Erros |

### 🔄 Máquina de Estados
```
MAIN (dashboard) → EXPANDED (detalhes) → ASSET_DETAIL (ativo)
     ↑___________________________↓
```

### 📦 Dependencies
- `requests` - HTTP client para Binance API
- `discord.py` - Discord bot framework
- `python-dotenv` - Carregamento de .env

### 📊 Progresso: 85%
- ✅ BinancePublicFeed implementado
- ✅ Heartbeat command funcional
- ✅ Dados reais em todos os estados
- ⏳ Gráficos (15% restante)

### 🐛 Bugfixes Aplicados (2026-03-31 → 2026-04-01)
| Issue | Linha | Correção |
|-------|-------|----------|
| eth_price recebia priceChangePercent | 212 | Corrigido para lastPrice |
| eth_price_float desnecessário | 213 | Removido, eth_price agora correto |
| eth_price_float referência residual | 241 | Corrigido para eth_price |
| RequestException não captura NameError | 266, 351 | Mudado para Exception genérica |
| Edit duplicado | 279 | Removido linha duplicada |
| **Indentação do try interno** | 210-296 | Adicionado 4 espaços (try interno não estava indentado dentro do try externo) |
| **set_timestamp() não existe (discord.py 2.7.1)** | 267, 358, 687, 774, 845, 859, 964 | Todas as 7 chamadas removidas/comentadas |

### ✨ Funcionalidades Implementadas (2026-04-01)
| Feature | Descrição | Status |
|---------|-----------|--------|
| Seleção de ativos individuais | Botões BTC/ETH no estado ASSET_DETAIL | ✅ |
| Gráfico por ativo | Candlestick específico para cada ativo | ✅ |
| Detalhes do ativo | Preço, variação, volume, máxima/mínima | ✅ |
| Navegação melhorada | Voltar para lista de ativos | ✅ |

### 📦 Dependencies Adicionadas (2026-04-01)
- `matplotlib >= 3.7.0` - Para geração de gráficos candlestick
- `requests >= 2.31.0` - Para API Binance (já estava em uso)

### 🔬 Debug Logs Adicionados (2026-04-01)
- Log antes/durante busca Binance
- Log de sucesso/erro na criação do embed
- Log com traceback completo de exceções
- Try-except geral no comando !paper
- Log detalhado após edit() (verifica embeds e components)

### 📝 Canais Configurados (2026-04-01)
| Canal ID | Nome | Status |
|----------|------|--------|
| 1488702077747068959 | Teste-01 | ✅ |
| 1488599448882909204 | Canal adicional | ✅ |

---
