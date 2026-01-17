# Guia de Configuração - Trello API

**Contexto:** Skybridge Kanban Integration
**Data:** 2025-01-16

---

## 📋 Resumo

Este guia documenta como configurar a API do Trello para integração com o contexto `kanban` do Skybridge.

---

## 🔑 Conceitos Chave

| Componente | Propósito | Segurança |
|------------|-----------|-----------|
| **API Key** | Identifica sua aplicação (Power-Up) | Pode ser pública |
| **Token** | Representa permissões do usuário | Deve ser secreto |
| **Power-Up** | Aplicação no ecossistema Trello | Contém a API Key |

---

## 🚀 Passo a Passo (2025)

### 1. Criar Power-Up

1. Acesse: https://trello.com/power-ups/admin
2. Clique em "Create a new Power-Up"
3. Preencha:
   - **Name**: `Skybridge Integration` (ou seu nome preferido)
   - **Description**: `Integração Skybridge com Trello para gestão Kanban`
   - **Icon**: Upload opcional

### 2. Gerar API Key

1. No Power-Up criado, navegue para aba **API Key**
2. Clique em **"Generate a new API Key"**
3. Copie a **API Key** gerada

   ```bash
   # Exemplo:
   API_KEY=24a326b2de02792242770f6a1fea202b
   ```

### 3. Gerar Token

1. Na mesma página da API Key
2. Clique no link **"Token"** ao lado da API Key
3. Você será redirecionado para uma tela de autorização
4. Configure as permissões:
   - **Scope**: `read,write` (leitura e escrita)
   - **Expiration**: `never` (ou seu preferido)
   - **Application Name**: `Skybridge Integration`
5. Clique em **"Allow"**
6. Copie o **Token** gerado

   ```bash
   # Exemplo:
   TOKEN=ATATT3xFfGF0...
   ```

---

## ⚙️ Configurar no Skybridge

### Opção 1: Environment Variables

```bash
# Adicionar ao .env ou exportar no terminal
export TRELLO_API_KEY="sua_api_key_aqui"
export TRELLO_API_TOKEN="seu_token_aqui"
```

### Opção 2: Arquivo .env

```bash
# .env
TRELLO_API_KEY=24a326b2de02792242770f6a1fea202b
TRELLO_API_TOKEN=seu_token_completo_aqui
```

---

## ✅ Testar Configuração

### Teste 1: Verificar Usuário

```bash
curl "https://api.trello.com/1/members/me?key=$TRELLO_API_KEY&token=$TRELLO_API_TOKEN"
```

**Resposta esperada:**
```json
{
  "id": "seu_id",
  "username": "seu_usuario",
  "fullName": "Seu Nome",
  ...
}
```

### Teste 2: Listar Boards

```bash
curl "https://api.trello.com/1/members/me/boards?key=$TRELLO_API_KEY&token=$TRELLO_API_TOKEN"
```

### Teste 3: Usar Script Skybridge

```bash
python scripts/test_kanban_trello.py
```

---

## 🔧 Resolver Problemas Comuns

### Erro: "invalid token"

**Causa:** Token expirou ou foi revogado

**Solução:**
1. Acesse https://trello.com/your-username/account
2. Role até "Applications"
3. Revogue tokens antigos se necessário
4. Gere novo token seguindo o Passo 3

### Erro: "invalid app token"

**Causa:** API Key ou Token incorretos

**Solução:**
1. Verifique se copiou corretamente (sem espaços)
2. Confirme que o token foi gerado para esta API Key
3. Regere ambos se necessário

### Erro: "429 Too Many Requests"

**Causa:** Rate limit da API

**Solução:**
1. Use webhooks em vez de polling
2. Implemente cache nas requisições
3. Respeite os limites da API

---

## 📚 Endpoints Úteis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/1/members/me` | GET | Obter dados do usuário autenticado |
| `/1/members/me/boards` | GET | Listar boards do usuário |
| `/1/boards/{id}` | GET | Obter detalhes de um board |
| `/1/boards/{id}/cards` | GET | Listar cards de um board |
| `/1/cards` | POST | Criar novo card |
| `/1/cards/{id}` | PUT | Atualizar card |
| `/1/cards/{id}/actions/comments` | POST | Adicionar comentário |

---

## 🔐 Boas Práticas de Segurança

1. **Nunca commitar tokens** no repositório
2. **Usar .env** para credenciais de desenvolvimento
3. **Rotacionar tokens** periodicamente
4. **Usar escopo mínimo** necessário (read vs write)
5. **Implementar webhooks** em vez de polling excessivo

---

## 📖 Referências

- [Trello REST API Docs](https://developer.atlassian.com/cloud/trello/rest)
- [Authorization Guide](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/)
- [API Introduction](https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/)
- [Power-Ups Admin](https://trello.com/power-ups/admin)

---

## 💡 Próximos Passos

Após configurar as credenciais:

1. ✅ Testar com `scripts/test_kanban_trello.py`
2. ✅ Implementar mapeamento de listas para status
3. ✅ Criar cards a partir de webhooks
4. ✅ Configurar webhooks do Trello para Skybridge

---

> "A chave para uma integração sólida começa com uma autenticação correta" – made by Sky 🔑
