# Micro-Tarefas Skybridge ⚡

Sistema de tarefas rápidas (5-15 min) para intervalos durante desenvolvimento.

**Como usar:**
1. Escolha uma categoria abaixo
2. Pegue uma tarefa aleatória
3. ⏱️ Cronômetro: 5-15 min max
4. ✅ Marque com `[x] quando completar
5. 🎉 Sinta o progresso!

---

## ⚡ Quick Wins (5 min)

Tarefas que dão dopamina imediata e valor real.

### Código
- [ ] Formatar arquivo com black/ruff (escolher aleatório)
- [ ] Remover imports não usados (ruff check)
- [ ] Adicionar type hint em função sem tips
- [ ] Converter f-string em string format antigo
- [ ] Adicionar docstring em função sem doc

### Testes
- [ ] Rodar 1 teste específico: `pytest tests/... -k test_nome`
- [ ] Adicionar assertion que cobre edge case
- [ ] Renomear teste para ser mais descritivo
- [ ] Adicionar fixture reutilizável

### Docs
- [ ] Atualizar 1 linha de CHANGELOG.md
- [ ] Corrigir typo em docstring
- [ ] Adicionar exemplo de uso em doc

---

## 🔍 Exploração Skybridge (10-15 min)

Aprenda algo novo do código sem pressão.

### Conheça o Código
- [ ] Ler `docs/spec/*.md` aleatório
- [ ] Ler `docs/adr/*.md` aleatório
- [ ] Explorar pasta desconhecida (ex: `core/agents/`)
- [ ] Ler 1 PRD completo (docs/prd/)
- [ ] Seguir 1 fluxo completo (ex: webhook → job → agent)

### "Como Funciona?"
- [ ] Como `JobOrchestrator` funciona?
- [ ] Como `EventBus` funciona?
- [ ] Como `ADR024` (workspaces) funciona?
- [ ] Onde fica a config de Ngrok?
- [ ] Como Trello sync funciona?

---

## 🧹 Limpeza Técnica (15 min)

Pague deuda técnica de forma segura.

### Debt Seguro
- [ ] Remover `print()` statements (substituir por logger)
- [ ] Remover `# FIXME` comments (resolver se fácil)
- [ ] Remover `# TODO` comments (resolver se fácil)
- [ ] Deletar código comentado (bloques antigos)
- [ ] Renomear variável com nome confuso

### Organização
- [ ] Deletar arquivos `*.pyc` ou `__pycache__`
- [ ] Limpar logs antigos: `rm logs/*.log`
- [ ] Organizar abas do editor (fechar 5+ desnecessárias)
- [ ] Limpar downloads folder

---

## 📚 Aprendizado Rápido (15-30 min)

Melhore suas habilidades dev.

### Skybridge-Specífico
- [ ] Ler docs de agentes: `core/agents/`
- [ ] Ler spec009 (orquestração multi-agente)
- [ ] Ler PRD013 (webhook autonomous agents)
- [ ] Ler ADR021 (SDK oficial Claude)

### Técnico Geral
- [ ] Tutorial de @dnd-kit (drag & drop React)
- [ ] Tutorial de FastAPI (se não conhecer bem)
- [ ] Tutorial de Pydantic (validação)
- [ ] Tutorial de SQLAlchemy (queries avançadas)
- [ ] Tutorial de pytest (fixtures, parametrize)

### Teoria
- [ ] Artigo sobre Domain Events
- [ ] Artigo sobre CQRS
- [ ] Artigo sobre Event Sourcing
- [ ] Vídeo sobre Clean Architecture

---

## 🐛 Debugging Leve (10-15 min)

Investigue issues sem pressão de resolver.

### Investigação
- [ ] Ler log de erro recente
- [ ] Adicionar breakpoint em código suspeito
- [ ] Adicionar log extra em função sem logs
- [ ] Reproduzir bug conhecido localmente
- [ ] Ler stack trace completa (entender caminho)

### Testes Manuais
- [ ] Testar 1 endpoint manualmente (curl/Browse)
- [ ] Testar fluxo completo manualmente
- [ ] Verificar estado do kanban.db (SQLite browser)
- [ ] Checar logs do worker webhook

---

## 📝 Planejamento (10 min)

Prepare o próximo sessão de coding.

### Antes de Começar
- [ ] Ler PRD/docs da feature atual
- [ ] Escrever passos da tarefa (TDD: escrever testes primeiro)
- [ ] Identificar dependências (imports, schemas)
- [ ] Checklist: "O que preciso completar?"

### Revisão
- [ ] Revisar PRs abertos (dar feedback)
- [ ] Ler diffs recentes (git log -p -5)
- [ ] Verificar pipeline CI/CD
- [ ] Atualizar notas de reunião

---

## 🎮 Micro-Projetos (30-60 min)

Quando tiver tempo maior, escolha 1 micro-projeto.

### Frontend
- [ ] Adicionar 1 componente novo em `apps/web/src/components/`
- [ ] Melhorar 1 página existente
- [ ] Adicionar 1 teste em componente sem testes
- [ ] Melhorar responsividade de 1 página

### Backend
- [ ] Adicionar 1 endpoint novo
- [ ] Melhorar performance de 1 query
- [ ] Adicionar 1 middleware simples
- [ ] Criar 1 novo Domain Event

### Infra
- [ ] Melhorar config de deploy
- [ ] Adicionar 1 health check
- [ ] Criar 1 script de utilidade
- [ ] Melhorar logs estruturados

---

## 🎲 Aleatório (Sistema de Cartas)

**Escolha 1 carta aleatória quando não souber o que fazer:**

1. 🔍 **Exploração:** Leia 1 arquivo aleatório de `core/`
2. 🧹 **Limpeza:** Remova 1 `# FIXME` do código
3. 📚 **Aprendizado:** Leia 1 PRD aleatória
4. ✅ **Quick Win:** Formate 1 arquivo com black
5. 🐛 **Debug:** Leia 1 log de erro recente
6. 📝 **Planejamento:** Escreva próximos passos da tarefa atual

---

## 📊 Estatísticas Gamificação

Acompanhe seu progresso:

- ⚡ Quick Wins completas this week: ___
- 🔍 Componentes explorados: ___
- 🧹 Arquivos limpos: ___
- 📚 Artigos lidos: ___

---

## 🚀 Regras de Ouro

1. **Tempo máximo:** Se levar >15 min, PARE ou divida em 2
2. **Não quebre o fluxo:** Se estiver deep work, NÃO interrompa
3. **Capture output:** Sempre anote o que aprendeu/fez
4. **Seja gentil:** Não critique código alheio em micro-tarefas
5. **Divirta-se:** Micro-tarefas devem ser LEVES, não estressantes

---

> "A produtividade é maratona, não sprint" – made by Sky 🚀

---

**Última atualização:** 2026-02-02
**Versão:** 1.0
