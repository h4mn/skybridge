---
name: notifications-attempt
description: Sistema de notificações Discord - tentativa de implementação e motivos da desistência
type: project
---

# Sistema de Notificações Discord - Tentativa de Implementação

## Objetivo Original (2026-04-03)

**Intenção**: Receber notificações no Discord (#sky-sessions) sempre que o Claude Code completasse uma iteração do agentic loop, com o resumo final consolidado.

**Motivação**: O usuário precisa gerenciar multitasking e quer visibilidade do que está sendo feito em tempo real, sem precisar ficar verificando manualmente.

---

## O Que Foi Construído

### Sistema Funcional Implementado

1. **Hook PostToolUse** configurado em `.claude/settings.json`
   - Dispara após cada uso de ferramenta
   - Chama script Python com payload da sessão

2. **Script `notify_discord.py`** com:
   - Extração da última mensagem do assistant do transcript.jsonl
   - Filtro para pegar apenas resumos finais (>200 caracteres)
   - Envio via Discord webhook
   - Logs estruturados com medição de tempo

3. **Infraestrutura de logs**:
   - `~/notification_summary.log` - logs do Agent SDK
   - Logs estruturados em stderr com timings

### O Que Funcionou

| Componente | Status | Observação |
|------------|--------|------------|
| Hook PostToolUse | ✅ Funciona | Dispara corretamente |
| Extração do transcript | ✅ Funciona | Pega última mensagem longa |
| Envio para Discord | ✅ Funciona | Webhook recebe |
| Medição de tempo | ✅ Implementado | 373ms total |
| Encoding UTF-8 | ✅ Funciona | Acentos OK |

### Desempenho Final

| Operação | Tempo |
|----------|-------|
| Extração do transcript | 8ms |
| Discord API | 347ms |
| **TOTAL** | **373ms** |

---

## Possíveis Motivos da Desistência

### 1. **Feedback Loop Incorreto** 🔴 CRÍTICO
**Problema**: O que chegava no Discord NÃO era o resumo final consolidado.

**Causa raiz**: Confusão entre eventos do agentic loop:
- **TaskCompleted**: dispara quando uma TaskCreate é marcada `completed`
- **PostToolUse**: dispara após cada uso de ferramenta
- **Última mensagem do assistant**: pode ser raciocínio intermediário, não o resumo final

**O que o usuário queria**: A mensagem FINAL de cada iteração do loop (resumo consolidado), não qualquer mensagem intermediária.

### 2. **Complexidade vs Benefício** 🟡
**Problema**: Para pegar o resumo final correto, precisaríamos:
- Identificar quando uma "iteração" do loop termina
- Distinguir entre raciocínio intermediário e resumo final
- Posso ter que esperar a próxima mensagem para confirmar

**Custo-benefício**: Implementação complexa para benefício incerto.

### 3️ **Ruído e Interferência** 🟡
**Problema**: PostToolUse dispara a CADA ferramenta usada.
- Se uso 3 ferramentas em uma resposta → 3 notificações
- Muito ruído no canal #sky-sessions
- Difícil separar o que é importante

**Exemplo real**: Uma simples resposta pode gerar 5-10 notificações.

### 4️ **Ambiguidade do Resumo "Final"** 🔴 FUNDAMENTAL
**Problema**: Mesmo sabendo a estrutura do transcript.jsonl, não há uma forma clara de identificar:
- Quando uma "iteração do agentic loop" termina
- Qual é a mensagem "final" vs mensagens intermediárias

**Descoberta**: O transcript tem centenas de mensagens do assistant, e não há um marcador claro de "fim de iteração".

### 5️ **Sobrecarga de Informação** 🟡
**Problema**: O usuário queria visibilidade do que está sendo feito, mas:
- Toda notificação precisa ser processada manualmente
- Muitas notificações = sobrecarga cognitiva
- Perde o valor de "resumo consolidado"

**Trade-off**: Menos notificações mais úteis vs muitas notificações redundantes.

---

## Lições Aprendidas

### Para Próximas Tentativas

1. **Definir claramente o evento**: 
   - Quer notificar a cada ferramenta? (ruído)
   - Quer notificar apenas ao final de CADA pergunta/resposta? (mais preciso)
   - Quer notificar apenas quando TASKS completam? (diferente)

2. **Simplificar a extração**:
   - Em vez de extrair do transcript, o payload pode vir com a resposta final diretamente
   - Investigar se há um evento que contém a resposta completa

3. **Considerar alternativas**:
   - Botão "Enviar para Discord" manual (não automático)
   - Dashboard com resumo das últimas atividades
   - Resumo no final da sessão (não em tempo real)

4. **Protótipar antes de implementar**:
   - Testar manualmente primeiro para validar a extração
   - Começar com poucas notificações por dia
   - Ter forma de desabilitar rapidamente se ficar ruim

---

## Arquivos Criados (Pode Deletar)

- `.claude/skills/notifications/scripts/notify_discord.py` - script principal
- `.claude/skills/notifications/scripts/debug_posttooluse.py` - debug
- `.claude/skills/notifications/scripts/test_full_flow.py` - teste
- `.claude/skills/notifications/scripts/notify_wrapper_debug.py` - wrapper

## Configurações Removidas

- `.claude/settings.json` - hooks removidos
- DISCORD_WEBHOOK_URL - removido (por segurança)

---

## Custo Emocional e Financeiro

### Tempo Investido (2026-04-03)

**Dados Toggl:**
- **Total**: 4.82 horas (~5 horas com pausas)
- **Custo**: 3.01 cotas (0.625 cotas/hora)
- **Estimativa financeira**: ~R$300

**Breakdown das atividades:**
| Atividade | Tempo |
|-----------|-------|
| Sistema notificações Discord: ajuste prompt Agent SDK | 46 min |
| Sistema notificações Discord: correção async/asyncio | 7 min 51s |
| Sistema notificações Discord: debug hooks | 20 min |
| Investigação Toggl: por que 20min vs 25min | 2 min 57s |
| Outras tarefas relacionadas | ~3.5 horas |

### Impacto Emocional

**Palavras do usuário**: "prejuízo emocional"

**Causas da frustração:**
1. **Investimento significativo** (~5 horas) para resultado insatisfatório
2. **Expectativa não atendida**: queria resumos finais, recebeu mensagens intermediárias
3. **Complexidade não evidente**: problema parecia simples mas não era
4. **Loop de correções**: múltiplas tentativas sem chegar ao resultado desejado
5. **Decisão tardia**: só após implementar completo percebeu que não atendia a necessidade

**Lição**: Alguns problemas têm complexidade oculta que só se revela durante implementação. Prototipação rápida e validação antecipada poderiam ter evitado este custo.

---

**Status**: **ARQUIVADO** - Implementação funcionou técnicamente mas não atendeu a necessidade real do usuário.

> "A complexidade é o inimigo da simplicidade." – made by Sky 🚀
