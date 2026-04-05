# Spec: Discord Persistent Menu

Menu de navegação sempre presente no topo da view, permitindo transição entre diferentes telas.

## ADDED Requirements

### Requirement: Menu visível em todos os estados

O sistema SHALL exibir um menu de navegação em todos os estados da view.

#### Scenario: Menu no Dashboard
- **GIVEN** o estado atual é DASHBOARD
- **WHEN** a view é renderizada
- **THEN** o menu com botões "Dashboard", "Posição", "Configuração" está visível
- **AND** o botão "Dashboard" está desabilitado (estado atual)

#### Scenario: Menu no Asset List
- **GIVEN** o estado atual é ASSET_LIST
- **WHEN** a view é renderizada
- **THEN** o menu com botões "Dashboard", "Posição", "Configuração" está visível
- **AND** o botão "Posição" é desabilitado (futuro)

#### Scenario: Menu no Asset Detail
- **GIVEN** o estado atual é ASSET_DETAIL
- **WHEN** a view é renderizada
- **THEN** o menu com botões "Dashboard", "Posição", "Configuração" está visível
- **AND** botões de ação específicos (ex: "Voltar", "Gráfico") também estão visíveis

### Requirement: Navegação entre telas

O sistema SHALL permitir transição entre as 3 telas principais via menu.

#### Scenario: Navegação Dashboard → Asset List
- **GIVEN** o usuário está no DASHBOARD
- **WHEN** clica no botão "💰 Ativos" no menu
- **THEN** o estado muda para ASSET_LIST
- **AND** a view é editada com conteúdo de Asset List

#### Scenario: Navegação Asset List → Dashboard
- **GIVEN** o usuário está em ASSET_LIST
- **WHEN** clica no botão "🏠 Home" no menu
- **THEN** o estado muda para DASHBOARD
- **AND** a view é editada com conteúdo de Dashboard

#### Scenario: Navegação para Posição (futuro)
- **GIVEN** o usuário está em qualquer tela
- **WHEN** clica no botão "📊 Posição" no menu
- **THEN** o estado muda para POSITION
- **AND** a view é editada com conteúdo de Posição
