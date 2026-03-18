# Tasks: Sky Chat Textual UI

## 1. Setup e Infraestrutura

- [x] 1.1 Adicionar `textual` e `textual-dev` ao requirements.txt
- [x] 1.2 Criar estrutura de diretórios `src/core/sky/chat/textual_ui/`
- [x] 1.3 Criar subdiretórios: `screens/`, `widgets/`, `workers/`, `styles/`
- [x] 1.4 Criar arquivo CSS base `assets/sky_chat.css`
- [x] 1.5 Adicionar feature flag `USE_TEXTUAL_UI` ao `.env.example`
- [x] 1.6 Renomear `ui.py` para `legacy_ui.py` (compatibilidade)
- [x] 1.7 Atualizar `__init__.py` para escolher UI baseado em feature flag

## 2. Widgets Customizados

- [x] 2.1 Implementar `SkyBubble` (mensagem da Sky)
- [x] 2.2 Implementar `UserBubble` (mensagem do usuário)
- [x] 2.3 Implementar `AnimatedTitle` com verbo animado (color sweep)
- [x] 2.4 Implementar `ContextBar` (ProgressBar com cores dinâmicas)
- [x] 2.5 Implementar `ThinkingIndicator` animado
- [x] 2.6 Implementar `ToolFeedback` (componente para tools executadas)
- [x] 2.7 Adicionar CSS para widgets em `sky_chat.css`
- [x] 2.8 Escrever testes unitários para widgets

## 3. Workers Assíncronos

- [x] 3.1 Implementar `ClaudeWorker` (chamada Claude SDK assíncrona)
- [x] 3.2 Implementar `RAGWorker` (busca em memória assíncrona)
- [x] 3.3 Implementar `MemorySaveWorker` (salvar memórias aprendidas)
- [x] 3.4 Criar sistema de fila para comunicação worker ↔ UI
- [x] 3.5 Implementar tratamento de erros e timeout
- [x] 3.6 Adicionar métricas de workers (latência, success rate)
- [x] 3.7 Escrever testes unitários para workers

## 4. Screens - Básico

- [x] 4.1 Implementar `WelcomeScreen` (tela de apresentação)
  - [x] 4.1.1 Layout centralizado horizontal/vertical
  - [x] 4.1.2 Letreiro "SkyBridge" animado
  - [x] 4.1.3 Input abaixo do letreiro
  - [x] 4.1.4 Rodapé introdutório
- [x] 4.2 Implementar `ChatScreen` (screen principal)
  - [x] 4.2.1 Header fixo (2 linhas)
  - [x] 4.2.2 ScrollView para mensagens
  - [x] 4.2.3 Footer com input field
  - [x] 4.2.4 Layout Vertical + Horizontal
- [x] 4.3 Conectar WelcomeScreen → ChatScreen na primeira mensagem
- [x] 4.4 Escrever testes unitários para screens

## 5. ChatScreen - Funcionalidades Core

- [x] 5.1 Implementar envio de mensagem via input field
- [x] 5.2 Integrar ClaudeWorker para gerar respostas
- [x] 5.3 Implementar exibição de SkyBubble e UserBubble
- [x] 5.4 Implementar separador visual entre turnos
- [x] 5.5 Implementar auto-scroll para última mensagem
- [x] 5.6 Implementar scroll manual (pausa auto-scroll)
- [x] 5.7 Integrar RAGWorker para busca de memórias
- [x] 5.8 Exibir preview de memórias no header
- [x] 5.9 Atualizar métricas no header a cada resposta

## 6. Header Completo

- [x] 6.1 Implementar linha 1: título dinâmico + barra de contexto
- [x] 6.2 Integrar AnimatedTitle com verbo animado
- [x] 6.3 Integrar ContextBar com cores dinâmicas
- [x] 6.4 Implementar linha 2: métricas (RAG, mems, latência, tokens, modelo)
- [x] 6.5 Implementar geração de título via LLM (a cada 2-3 turnos)
- [x] 6.6 Atualizar barra de contexto (0-100% das 20 msgs)
- [x] 6.7 Implementar cores da barra: verde → amarelo → laranja → vermelho (via ContextBar)

## 7. Tela de Apresentação (WelcomeScreen)

- [x] 7.1 Layout centralizado (usa Dock ou Center)
- [x] 7.2 Animação de letreiro "SkyBridge"
- [x] 7.3 Input field posicionado abaixo
- [x] 7.4 Rodapé introdutório estilizado
- [x] 7.5 Transição suave para ChatScreen ao enviar primeira mensagem

## 8. Screens Secundárias

- [x] 8.1 Implementar `ConfigScreen` (configurações)
  - [x] 8.1.1 Lista de opções toggles (RAG, verbose, modelo)
  - [x] 8.1.2 Navegação via ESC
- [x] 8.2 Implementar `HelpScreen` (ajuda)
  - [x] 8.2.1 Lista de comandos com descrições
  - [x] 8.2.2 Busca por comandos
  - [x] 8.2.3 Navegação via ESC
- [x] 8.3 Implementar comando `/config` para abrir ConfigScreen
- [x] 8.4 Implementar comando `/help` ou `?` para abrir HelpScreen
- [x] 8.5 Escrever testes unitários para screens secundárias

## 9. Modais e Confirmações

- [x] 9.1 Implementar `ConfirmModal` (genérico)
- [x] 9.2 Integrar modal no comando `/new` (confirmar limpeza de sessão)
- [x] 9.3 Implementar modal só com 5+ mensagens (limpeza direta se < 5)
- [x] 9.4 Suportar confirmação: "s", "y", Enter
- [x] 9.5 Suportar cancelamento: "n", ESC, `/cancel`
- [x] 9.6 Implementar overlay (fundo escurecido)
- [x] 9.7 Escrever testes unitários para modais

## 10. Toast Notifications

- [x] 10.1 Implementar `ToastNotification` widget
- [x] 10.2 Posicionar no canto superior direito (Dock)
- [x] 10.3 Auto-descartar após 5 segundos
- [x] 10.4 Permitir dispensar com ESC
- [x] 10.5 Integrar Toast em alertas de latência alta
- [x] 10.6 Integrar Toast em falhas de tools
- [x] 10.7 Integrar Toast ao limpar sessão
- [x] 10.8 Escrever testes unitários para toasts

## 11. Comandos

- [x] 11.1 Implementar comando `/new` (nova sessão - parcial, sem modal)
- [x] 11.2 Implementar comando `/cancel` (cancela operação pendente)
- [x] 11.3 Implementar comando `/sair`, `quit`, `exit` (encerrar chat)
- [x] 11.4 Implementar comando `/config` (abre ConfigScreen)
- [x] 11.5 Implementar comando `/help`, `?` (abre HelpScreen)
- [x] 11.6 Detectar comandos no input field antes de enviar ao chat
- [x] 11.7 Escrever testes para comandos

## 12. Renderização de Markdown

- [x] 12.1 Integrar `MarkdownText` widget do Textual
- [x] 12.2 Implementar syntax highlighting para blocos de código
- [x] 12.3 Customizar cores de markdown via CSS
- [x] 12.4 Suportar links clicáveis
- [x] 12.5 Suportar negrito, itálico, listas
- [x] 12.6 Testar renderização com markdown complexo

## 13. Screen Management

- [x] 13.1 Implementar sistema de pilha (stack) de screens (nativo Textual)
- [x] 13.2 Implementar `push_screen()` (adiciona screen) (nativo Textual)
- [x] 13.3 Implementar `pop_screen()` (remove screen atual) (nativo Textual)
- [x] 13.4 Preservar estado de screens ao navegar (nativo Textual)
- [x] 13.5 Implementar ESC como "voltar para screen anterior" (nativo Textual)
- [x] 13.6 ChatScreen nunca é removida da pilha (base) (comportamento padrão)
- [x] 13.7 Escrever testes para screen management

## 14. Observabilidade

- [x] 14.1 Exibir latência no header (formato "⚡1.2s")
- [x] 14.2 Exibir tokens no header (formato "💰1234/10k")
- [x] 14.3 Exibir contagem de memórias no header ("3 mems")
- [x] 14.4 Exibir status RAG no header ("ON/OFF")
- [x] 14.5 Exibir modelo Claude no header
- [x] 14.6 Implementar resumo de sessão ao encerrar (DataTable)
- [x] 14.7 Integrar métricas do ClaudeChatAdapter

## 15. Testes E2E

- [x] 15.1 Teste: fluxo completo (mensagem → resposta → bubble)
- [x] 15.2 Teste: comando `/new` com modal
- [x] 15.3 Teste: comando `/help` abre HelpScreen
- [x] 15.4 Teste: título é gerado após 3 mensagens
- [x] 15.5 Teste: barra de contexto muda de cor
- [x] 15.6 Teste: workers não travam a UI
- [x] 15.7 Teste: scroll manual pausa auto-scroll
- [x] 15.8 Teste: Markdown é renderizado corretamente

## 16. CSS e Temas

- [x] 16.1 Criar `sky_chat.css` com tema escuro padrão
- [x] 16.2 Definir estilos para SkyBubble
- [x] 16.3 Definir estilos para UserBubble
- [x] 16.4 Definir animação `color-sweep` para verbo
- [x] 16.5 Definir estilos para ProgressBar (verde, amarelo, laranja, vermelho)
- [x] 16.6 Definir estilos para MarkdownText
- [ ] 16.7 Testar em terminais com/suporte a cores
- [x] 16.8 (Opcional) Criar tema claro `sky_chat_light.css`

## 17. Documentação

- [x] 17.1 Atualizar README com nova UI Textual
- [x] 17.2 Adicionar capturas de tela (screenshots)
- [x] 17.3 Documentar feature flag `USE_TEXTUAL_UI`
- [x] 17.4 Documentar comandos disponíveis
- [x] 17.5 Atualizar CLAUDE_CHAT_QUICKSTART.md
- [x] 17.6 Adicionar seção "Customizando CSS" ao quickstart

## 18. Integração e Polimento

- [x] 18.1 Integrar com `scripts/sky_rag.py` (via __init__.py)
- [x] 18.2 Criar script `scripts/sky_textual.bat`
- [ ] 18.3 Testar compatibilidade com Windows Terminal
- [ ] 18.4 Testar em terminais pequenos (80x24 mínimo)
- [ ] 18.5 Testar performance com sessões longas (50+ mensagens)
- [x] 18.6 Corrigir bugs encontrados nos testes
- [x] 18.7 Otimizar latência de workers
- [x] 18.8 Refatorar código duplicado

## 19. Preparação para Lançamento

- [x] 19.1 Atualizar `USE_TEXTUAL_UI=true` como padrão
- [x] 19.2 Testar rollback para `USE_TEXTUAL_UI=false`
- [x] 19.3 Verificar que código legado (`legacy_ui.py`) funciona
- [ ] 19.4 Fazer code review dos PRs
- [ ] 19.5 Merge para branch principal
- [ ] 19.6 Criar tag de release
- [ ] 19.7 Anunciar nova UI na documentação

## 20. Pós-Lançamento

- [ ] 20.1 Monitorar feedback dos usuários
- [ ] 20.2 Corrigir bugs críticos reportados
- [ ] 20.3 Coletar métricas de uso (se implementado)
- [ ] 20.4 Planejar melhorias futuras (persistência, etc.)

---

## Total de Tarefas

- **Total:** ~150 tarefas
- **Estimativa:** 4-5 semanas (1 desenvolvedor)
- **Dependencies:** Tarefas em cada seção devem ser completadas em ordem numérica

---

> "A jornada de mil milhas começa com um único passo" – made by Sky 🚀
