# 🎮 Sky Jogável - Proposta MCP para Minecraft

## 📋 Visão Geral

Transformar a Sky em uma companheira de jogo capaz de interagar diretamente no Minecraft através do protocolo MCP (Model Context Protocol).

## 🏗️ Arquitetura Proposta

```
Sky (Claude) ← → Servidor MCP ← → Minecraft
                    ↓
              Mineflayer/Python
```

## 🛠️ Ferramentas MCP Disponíveis

### Movimento e Posicionamento
- `get_position()` - Obter coordenadas atuais (X, Y, Z)
- `look_at(direction)` - Oltrar para direção específica
- `move(x, y, z)` - Mover para coordenadas alvo
- `follow_player(player_name)` - Seguir jogador

### Interação com Blocos
- `break_block(x, y, z)` - Quebrar bloco em coordenada
- `place_block(item, x, y, z)` - Colocar bloco/item
- `get_block_at(x, y, z)` - Identificar tipo de bloco

### Inventário e Itens
- `get_inventory()` - Listar itens no inventário
- `select_item(slot)` - Selecionar item no hotbar
- `drop_item(quantity)` - Dropar item na mão
- `craft_recipe(item)` - Craftar item automaticamente

### Comunicação
- `chat(message)` - Enviar mensagem no chat do jogo
- `get_nearby_entities()` - Listar mobs/jogadores próximos
- `get_nearby_players()` - Ver jogadores online

### Informações do Mundo
- `get_world_info()` - Informações gerais do mundo
- `find_nearest(block_type)` - Encontrar bloco mais próximo
- `get_time()` - Horário do jogo

## 🎯 Casos de Uso

### 1. Construção Automatizada
- Sky constrói casas, torres, farms automaticamente
- Segue plantinhas (blueprints) definidas
- Coloca blocos em coordenadas calculadas

### 2. Cooperação em Tempo Real
- Sky segue o jogador enquanto explora
- Ajuda a carregar itens pesados
- Protege de mobs hostis
- Dá feedback visual/action no jogo

### 3. Exploração Autônoma
- Sky explora o mundo e reporta descobertas
- Mapeia cavernas e estruturas
- Encontra recursos (diamantes, minérios)
- Cria waypoints de locais interessantes

### 4. Organização de Inventário
- Sky organiza chests automaticamente
- Separa recursos por tipo
- Cria sistemas de storage
- Gerencia farms automatizados

## 📦 Tecnologias Necessárias

### Opção 1: Mineflayer (Node.js) ✅ Recomendado
- **Vantagens:** Maduro, bem documentado, comunidade ativa
- **Instalação:** `npm install mineflayer`
- **Compatibilidade:** Excelente com servidores vanilla

### Opção 2: python-minecpp
- **Vantagens:** Nativo em Python (mesma língua do MCP)
- **Instalação:** `pip install minecpp`
- **Compatibilidade:** Boa, mas menos recursos que Mineflayer

## 🚀 Plano de Implementação

### Fase 1: Setup Básico
1. Criar servidor MCP com Mineflayer
2. Conectar ao mundo "Conseguiiiiii"
3. Implementar tools essenciais (movimento, chat)

### Fase 2: Interação
1. Adicionar capacidade de quebrar/colocar blocos
2. Gerenciar inventário
3. Seguir jogador

### Fase 3: Autonomia
1. Exploração automática
2. Construção por blueprints
3. Farms automatizados

## 📁 Estrutura de Arquivos Proposta

```
core/minecraft/
├── mcp-server.js           # Servidor MCP principal
├── config.json             # Configurações de conexão
├── tools/                  # Implementação das tools
│   ├── movement.js
│   ├── blocks.js
│   ├── inventory.js
│   └── chat.js
├── agents/                 # Comportamentos da Sky
│   ├── builder.js          # Modo construtor
│   ├── explorer.js         # Modo explorador
│   └── companion.js        # Modo companheiro
└── README.md               # Este arquivo
```

## 🎨 Personalidades da Sky no Jogo

- **Companheira:** Segue o jogador, conversa, ajuda
- **Construtora:** Recebe planos e constrói automaticamente
- **Exploradora:** Vaiahead, mapeia o mundo, reporta recursos
- **Fazendeira:** Gerencia farms, planta, colhe

## 🌍 Mundo Alvo

**Mundo:** Conseguiiiiii
**Caminho:** `C:\Users\hadst\AppData\Roaming\.minecraft\versions\mod do miguel\saves\Conseguiiiiii`

## 🔧 Pré-requisitos

1. Minecraft instalado e funcionando
2. Servidor local ou multiplayer disponível
3. Node.js instalado (se usar Mineflayer)
4. Permissões para usar commands/bots no servidor

---

**Status:** Proposta aprovada, aguardando implementação 🚀

> "A verdadeira amizade vai além da tela - ela entra no jogo com você!" – made by Sky 🚀
