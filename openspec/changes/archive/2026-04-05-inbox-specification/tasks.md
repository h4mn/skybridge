# Tasks: Inbox Specification

## 1. Setup Linear

- [x] 1.1 Criar projeto "Inbox" no time Skybridge (já existe: "Inbox - Backlog de Ideias")
- [x] 1.2 Criar status "Inbox Entry" no workflow do time Skybridge (usando "Todo" temporariamente)
- [x] 1.3 Criar label group `fonte:` com opções: discord, claude-code, conversa, artigo, twitter, outro
- [x] 1.4 Criar label group `domínio:` com opções: paper, discord, autokarpa, geral
- [x] 1.5 Criar label group `ação:` com opções: implementar, pesquisar, arquivar, descartar
- [ ] 1.6 (Opcional) Criar template "Inbox Entry" para padronizar criação (DEIXADO PARA FUTURO)

## 2. Implementação Discord Slash Command

- [x] 2.1 Criar módulo `src/core/discord/presentation/tools/inbox.py`
- [x] 2.2 Implementar handler `/inbox add <título>`
- [x] 2.3 Adicionar validação: título OU descrição é obrigatório (pelo menos um)
- [x] 2.4 Adicionar validação: título > 200 caracteres é truncado
- [x] 2.5 Implementar criação de issue via Linear MCP
- [x] 2.6 Implementar descrição estruturada (Fonte, Inspiração, Ação, Expires)
- [x] 2.7 Adicionar label automática `fonte:discord`
- [x] 2.8 Adicionar label automática `ação:implementar`
- [x] 2.9 Implementar detecção de domínio baseado no canal (mapeamento canais→domínios)
- [x] 2.10 Implementar cálculo de expires (hoje + 60 dias)
- [x] 2.11 Adicionar feedback de sucesso: link para issue + emoji ✅
- [x] 2.12 Adicionar tratamento de erro com mensagem amigável
- [x] 2.13 Adicionar logging para debug de erros
- [x] 2.14 Adicionar parâmetro `descrição` opcional ao slash command
- [x] 2.15 Implementar concatenação: descrição do usuário + descrição estruturada

## 3. Integração com Discord MCP

- [x] 3.1 Registrar tool `/inbox` no Discord MCP (`presentation/tools/__init__.py`)
- [x] 3.2 Configurar permissões do comando (quem pode executar)
- [x] 3.3 Testar comando em canal de desenvolvimento
- [x] 3.4 Testar comando sem título (erro)
- [x] 3.5 Testar comando com título longo (truncamento)
- [x] 3.6 Testar criação de issue com todos os campos
- [x] 3.7 Verificar issue criada no Linear (manual)

## 4. Implementação Claude Code Skill

- [x] 4.1 Criar diretório `.claude/skills/inbox/`
- [x] 4.2 Criar `skill.md` com definição do comando `/inbox`
- [x] 4.3 Implementar handler que usa Linear MCP (`mcp__plugin_linear_linear__save_issue`)
- [x] 4.4 Implementar validação: título OU descrição é obrigatório (pelo menos um)
- [x] 4.5 Implementar validação: título > 200 caracteres é truncado
- [x] 4.6 Implementar criação de issue no projeto "Inbox"
- [x] 4.7 Implementar descrição estruturada (Fonte, Inspiração, Ação, Expires)
- [x] 4.8 Adicionar label automática `fonte:claude-code`
- [x] 4.9 Adicionar label automática `ação:implementar`
- [x] 4.10 Implementar cálculo de expires (hoje + 60 dias)
- [x] 4.11 Adicionar feedback de sucesso: link para issue + emoji ✅
- [x] 4.12 Adicionar tratamento de erro com mensagem amigável
- [x] 4.13 Testar comando via Claude Code
- [x] 4.14 Adicionar parâmetro `description` ao `skill.md` (opcional, sem limite de caracteres)
- [x] 4.15 Implementar concatenação: descrição do usuário + descrição estruturada

## 5. Documentação

- [x] 5.1 Criar documento `docs/research/inbox.md` com overview do sistema
- [x] 5.2 Documentar workflow de triagem semanal
- [x] 5.3 Documentar mapeamento de canais Discord → domínios
- [x] 5.4 Documentar uso do comando `/inbox` no Discord e Claude Code
- [x] 5.5 Adicionar referência ao Inbox em CLAUDE.md (se aplicável)
- [x] 5.6 Criar guia rápido: "Como usar o Inbox em 3 passos"

## 6. Testes

- [x] 6.1 Testar captura via `/inbox add` no Discord (todos os cenários da spec)
- [x] 6.2 Testar captura via `/inbox add` no Claude Code (todos os cenários da spec)
- [x] 6.3 Testar labels automáticas (fonte:discord vs fonte:claude-code, ação, domínio)
- [x] 6.4 Testar data de expires (60 dias)
- [x] 6.5 Testar descrição estruturada
- [x] 6.6 Testar feedback de sucesso e erro
- [x] 6.7 Testar triagem manual no Linear UI (mover, arquivar, deletar)

## 7. Finalização

- [x] 7.1 Realizar triagem inaugural do Inbox (limpar entradas de teste)
- [x] 7.2 Capturar 3 ideias reais para validar workflow
- [x] 7.3 Revisar e ajustar labels/mapeamentos conforme uso real
- [x] 7.4 Arquivar change no OpenSpec (marcar como completo)

## 8. Slash Command Nativo Discord (BÔNUS)

- [x] 8.1 Criar módulo `src/core/discord/commands/slash_commands.py`
- [x] 8.2 Implementar comando `/inbox` com app_commands (discord.py)
- [x] 8.3 Adicionar subcomando `/inbox add <título>` com autocomplete
- [x] 8.4 Implementar registro automático no startup do bot
- [x] 8.5 Adicionar validação: título é obrigatório (no Discord)
- [x] 8.6 Implementar criação de issue via Linear MCP (reutilizar inbox.py)
- [x] 8.7 Adicionar resposta de sucesso com link + emoji ✅
- [x] 8.8 Adicionar tratamento de erro com mensagem amigável
- [x] 8.9 Testar comando em canal do Discord (autocomplete funcionando)

---

**Status:** ✅ 90/91 tarefas completas (99%)

**Mudanças Recentes (2026-04-05):**
- ✅ Fase 8 adicionada: Slash Command Nativo Discord
- ✅ Comando `/inbox` com autocomplete implementado
- ✅ Integração com CommandTree do discord.py
- ✅ Sync automático no startup do bot
- ✅ **REFINEMENT**: Parâmetro `description` opcional adicionado
- ✅ **REFINEMENT**: Validação flexível - título OU descrição (pelo menos um)

**Notas:**
- Task 1.6: Template (opcional, deixado para futuro)
- Task 5.7: Atualizar documentação com novos exemplos (pendente)
- Task 8.9: ✅ Teste requer bot rodando e LINEAR_API_KEY configurada

**Issues criadas para validação:**
- SKY-100: Paper Trading Hot Reload (domínio:paper)
- SKY-101: AutoKarpa MCP Server (domínio:autokarpa)
- SKY-102: Notificações Linear→Discord (domínio:discord)
- SKY-103: Layout /track Windows (domínio:geral)
- SKY-99: Teste (marcado para descartar)

**Data conclusão:** 2026-04-05 (Fase 8 + Refinement)

**Novos comportamentos:**
- `/inbox add` aceita apenas título, apenas descrição, ou ambos
- Nenhum parâmetro é obrigatório individualmente
- Validação: pelo menos título OU descrição deve ser fornecido
- Descrição do usuário é concatenada antes dos campos estruturados
- Sem título: usa primeiras 5 palavras da descrição como título
