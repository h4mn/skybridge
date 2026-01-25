---
name: Create Issue
description: Analisa requisitos do usuário e cria uma issue estruturada seguindo o template do workflow multi-agente Skybridge. Use esta skill quando um usuário submete um novo requisito que precisa ser rastreado e resolvido através do workflow automatizado.
version: 1.0.0
---

# Create Issue

Esta skill analisa requisitos do usuário e cria uma issue estruturada seguindo o template definido em SPEC009.

## Objetivo

Criar uma issue bem estruturada para o workflow de orquestração multi-agente (SPEC009), permitindo que os agentes subsequentes (Resolvedor, Testador, Desafiador) trabalhem de forma coordenada.

## Quando Usar

Use esta skill quando:
- Usuário descreve um novo requisito ou problema
- Há necessidade de criar uma issue rastreável
- Requisito precisa passar pelo workflow automatizado
- Issue deve seguir template estruturado para orquestração

## Não Usar

Não use esta skill quando:
- Requisito é ambíguo demais para criar issue estruturada
- Usuário está apenas explorando ideias sem intenção de implementação
- Issue já existe no repositório

## Análise de Requisito

### 1. Extrair Informações Chave

Analise a requisição do usuário e identifique:

| Informação | Como Identificar |
|-----------|-----------------|
| **Tipo** | Bug fix, feature, refatoração, documentação |
| **Título** | Descrição sucinta do problema |
| **Descrição** | Detalhes do requisito, contexto, exemplos |
| **Prioridade** | High, medium, low (baseado em urgência/impacto) |
| **Etiquetas** | Tags relevantes (bug, enhancement, documentation, etc) |

### 2. Classificar Tipo de Issue

| Tipo | Descrição | Exemplos |
|------|-----------|----------|
| **Bug** | Comportamento inesperado ou erro | "API retorna 500 ao buscar usuário" |
| **Feature** | Nova funcionalidade solicitada | "Adicionar endpoint de busca" |
| **Refactor** | Melhoria de código sem mudar comportamento | "Refatorar método user_service para usar padrão strategy" |
| **Documentation** | Correção ou adição de documentação | "Atualizar README com instruções de deployment" |

### 3. Validar Completude

Verifique se a requisição possui:
- ✅ Título claro
- ✅ Descrição detalhada
- ✅ Contexto suficiente (por que é necessário?)
- ✅ Exemplos (quando aplicável)
- ✅ Critérios de aceitação claros

Se faltar informações:
1. Pergunte ao usuário para esclarecer
2. Não crie issue até ter informações suficientes

## Template de Issue

Seguir o template definido em SPEC009 seção 5:

```markdown
# [tipo]: [descrição sucinta]

## Labels
`automated`, `[tipo]`

## 1. Requisito Original

[Descrição completa do requisito fornecido pelo usuário]

## 2. Análise (Criador)

### 2.1 Tipo de Issue
- Tipo: `[bug/feature/refactor/documentation]`
- Prioridade: `[high/medium/low]`
- Complexidade estimada: `[baixa/média/alta]`

### 2.2 Contexto
[Explicação do contexto por que isso é necessário]

### 2.3 Critérios de Aceitação
- [ ] Critério 1
- [ ] Critério 2
- [ ] Critério 3

### 2.4 Notas Técnicas
[Informações técnicas relevantes, dependências, considerações de arquitetura]

---

## 3. Desenvolvimento (Resolvedor)

[Esta seção será preenchida pelo Resolvedor de Issue]

## 4. Testes (Testador)

[Esta seção será preenchida pelo Testador de Issue]

## 5. Desafio (Desafiador)

[Esta seção será preenchida pelo Desafiador de Qualidade]

---

**Agentes:** criador=<id>, resolvedor=<id>, testador=<id>, desafiador=<id>
```

## Criação da Issue

### 1. Criar Issue no GitHub

Use a API do GitHub para criar a issue:

```python
# Pseudocódigo
import github

gh = github.GitHub(token=GH_TOKEN)
repo = gh.get_repo("h4mn/skybridge")

issue = repo.create_issue(
    title="[tipo]: [descrição]",
    body=issue_body_formatado,
    labels=["automated", tipo]
)
```

### 2. Adicionar Labels Obrigatórias

Labels obrigatórias:
- `automated` — Indica que issue faz parte do workflow automatizado
- `[tipo]` — Tipo da issue (bug, feature, refactor, documentation)

Labels opcionais:
- `high-priority` — Para issues urgentes
- `help wanted` — Para issues que podem receber contribuições
- `good first issue` — Para issues boas para iniciantes

### 3. Postar Webhook

Após criar a issue, postar webhook para iniciar o workflow:

```json
POST /webhooks/github
{
  "action": "issues.opened",
  "issue": {
    "number": <issue_number>,
    "title": "<título>",
    "body": "<corpo formatado>",
    "labels": ["automated", "<tipo>"]
  },
  "repository": {
    "name": "skybridge",
    "full_name": "h4mn/skybridge"
  }
}
```

## Exemplo Prático

### Requisição do Usuário

> "Preciso corrigir um bug na API de usuários. Quando busco um usuário inexistente, a API retorna 404 com corpo HTML em vez de JSON."

### Análise

| Campo | Valor |
|-------|-------|
| **Tipo** | Bug |
| **Título** | Bug: API de usuários retorna HTML ao buscar usuário inexistente |
| **Prioridade** | High |
| **Complexidade** | Baixa |
| **Labels** | `automated`, `bug` |

### Issue Criada

```markdown
# Bug: API de usuários retorna HTML ao buscar usuário inexistente

## Labels
`automated`, `bug`

## 1. Requisito Original

Preciso corrigir um bug na API de usuários. Quando busco um usuário inexistente, a API retorna 404 com corpo HTML em vez de JSON.

## 2. Análise (Criador)

### 2.1 Tipo de Issue
- Tipo: bug
- Prioridade: high
- Complexidade estimada: baixa

### 2.2 Contexto
API de usuários (`GET /api/users/{id}`) deve retornar resposta JSON consistente mesmo para erros. Atualmente retorna HTML ao buscar usuário inexistente, que quebra consumidores que esperam JSON.

### 2.3 Critérios de Aceitação
- [ ] API retorna status 404 ao buscar usuário inexistente
- [ ] Corpo da resposta é JSON, não HTML
- [ ] Estrutura JSON é consistente com outras respostas de erro

### 2.4 Notas Técnicas
- Endpoint: `GET /api/users/{id}`
- Comportamento esperado: 404 com JSON `{ "error": "User not found" }`
- Comportamento atual: 404 com HTML de erro do servidor

---

## 3. Desenvolvimento (Resolvedor)

[Esta seção será preenchida pelo Resolvedor de Issue]

## 4. Testes (Testador)

[Esta seção será preenchida pelo Testador de Issue]

## 5. Desafio (Desafiador)

[Esta seção será preenchida pelo Desafiador de Qualidade]

---

**Agentes:** criador=sky-creator-001, resolvedor=<pendente>, testador=<pendente>, desafiador=<pendente>
```

## Validação

Antes de postar webhook, verifique:

- ✅ Título é claro e conciso
- ✅ Tipo de issue está identificado corretamente
- ✅ Descrição contém contexto suficiente
- ✅ Critérios de aceitação estão claros e mensuráveis
- ✅ Labels incluem `automated`
- ✅ Template segue estrutura de SPEC009 seção 5

## Transição de Estado

Após criar a issue:
1. Issue entra no estado: `OPEN`
2. Webhook é postado para `/webhooks/github`
3. Próximo agente (Resolvedor de Issue) é ativado
4. Estado da issue: `OPEN` → `IN_PROGRESS`

## Referências

- [SPEC009 — Orquestração de Workflow Multi-Agente](../../../../docs/spec/SPEC009-orchestracao-workflow-multi-agente.md)
- [PRD013 — Webhook Autonomous Agents](../../../../docs/prd/PRD013-webhook-autonomous-agents.md)
- [GitHub API Documentation](https://docs.github.com/en/rest/reference/issues)

---

> "Uma issue bem estruturada é metade do caminho para uma solução eficiente." – made by Sky 📋
