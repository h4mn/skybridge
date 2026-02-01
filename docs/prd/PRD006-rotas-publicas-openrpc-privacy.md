---
status: substituido
data: 2025-12-26
---

# PRD006 — Rotas públicas para OpenAPI e Privacy (Substituído pelo PRD007)

## 1) Problema

Para configurar GPTs personalizados, precisamos de duas rotas públicas: uma para
expor o contrato (OpenAPI) e outra para a política de privacidade.
Hoje, essas informações não estão disponíveis em endpoints dedicados e sem
autenticação.

## 2) Objetivo

Disponibilizar duas rotas públicas, estáveis e sem autenticação:

- **Contrato**: `GET /openapi`.
- **Privacidade**: `GET /privacy`.

Essas rotas serão usadas por GPTs personalizados e validações externas.

## 3) Escopo

### Inclui

- Endpoint público para retorno do documento OpenAPI.
- Endpoint público para retorno do texto de política de privacidade.
- Documentação básica das rotas e exemplos de resposta.

### Não inclui

- UI para gestão de privacidade.
- Multi-tenant ou versões por tenant.
- Autenticação específica para essas rotas (são públicas por design).

## 4) Requisitos Funcionais

* **RF1 (OpenAPI):** `GET /openapi` retorna JSON válido do contrato atual.
* **RF2 (Privacy):** `GET /privacy` retorna texto claro de política de privacidade.
* **RF3 (Public):** ambas as rotas são acessíveis sem autenticação.
* **RF4 (Método):** apenas `GET` é permitido nessas rotas.

## 5) Requisitos Não Funcionais

* Resposta rápida (payload pequeno).
* Conteúdo versionado junto ao repositório.
* Evitar dados sensíveis no conteúdo exposto.

## 6) DoD (Critérios de Aceite)

* `GET /openapi` responde `200` com JSON válido.
* `GET /privacy` responde `200` com texto legível.
* Chamadas sem credencial funcionam.
* Testes automatizados cobrindo as duas rotas.

## 7) Plano de Implementação

1. Definir as rotas públicas no adapter HTTP.
2. Reusar gerador OpenAPI existente (ou expor snapshot atual).
3. Criar arquivo de política de privacidade em `docs/` e servir conteúdo.
4. Adicionar testes de integração para `GET /openapi` e `GET /privacy`.

> "Clareza primeiro, execução depois." – made by Sky ✨

## Nota de substituição

Este PRD foi substituído pelo **PRD007 — Sky-RPC Ticket + Envelope**, alinhado
à ADR010.
