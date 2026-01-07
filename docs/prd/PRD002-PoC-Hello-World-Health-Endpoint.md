---
status: aceito
data: 2025-12-24
---

# PRD002 — PoC Hello World: Health Endpoint com Ngrok

## 1. Objetivo

Criar uma prova de conceito mínima (Hello World) que valide a estrutura do ADR002 funcionando de verdade: uma rota `/qry/health` acessível via Ngrok, baseada na skybridge legada.

## 2. Problema

A estrutura está planejada e criada, mas ainda não há código executável que valide que:
- O Kernel funciona como SDK
- O Platform bootstrap funciona
- CQRS (/qry/*) é viável
- Integração com Ngrok funciona

Sem um PoC rodando, permanecemos apenas no papel.

## 3. Escopo

### Dentro do escopo
- **Kernel base**: Result type, Envelope básico, registry simples
- **Platform**: Bootstrap básico com FastAPI
- **CQRS**: Uma Query `/qry/health` que retorna status do sistema
- **Apps**: Thin adapter API que expõe o endpoint
- **Ngrok**: Integração para expor o serviço localmente
- **Config**: Config base (sem profiles complexos ainda)
- **Observabilidade**: Logging básico + correlation ID

### Fora do escopo
- Commands (/cmd/*)
- Domínios FileOps e Tasks completos
- Event Sourcing
- Plugins reais
- Autenticação/autorização
- Frontend/Web UI

## 4. Usuários / Stakeholders

- Desenvolvedor (validação da arquitetura)
- Sky (agente IA, para evoluir a partir de código funcional)

## 5. Requisitos

### Funcionais

#### RF001 — Kernel Base
- `Result<T, E>` type para retornos typed
- `Envelope` com correlation_id, timestamp, status
- `QueryRegistry` simples para registrar handlers

#### RF002 — Platform Bootstrap
- Inicialização do FastAPI app
- Logging básico configurado
- Correlation ID middleware

#### RF003 — Health Query
- GET `/qry/health` retornando:
  ```json
  {
    "status": "healthy",
    "version": "0.1.0",
    "timestamp": "2025-12-24T17:00:00Z",
    "correlation_id": "uuid"
  }
  ```

#### RF004 — Ngrok Integration
- Script para iniciar Ngrok apontando para porta 8000
- URL pública exibida no log

#### RF005 — Config Base
- Arquivo `config/base.yaml` com porta, host, log level
- Environment variables podem sobrescrever

### Não Funcionais

- Python 3.11+
- FastAPI + Uvicorn
- Código seguindo fronteiras do ADR002
- Logs estruturados (JSON)

## 6. Critérios de Sucesso

- [ ] `python -m apps.api.main` inicia sem erros
- [ ] `GET http://localhost:8000/qry/health` retorna 200 com JSON válido
- [ ] Ngrok expõe URL pública acessível
- [ ] Logs mostram correlation_id
- [ ] Código respeita fronteiras (não viola ADR002)
- [ ] README com instruções de como rodar

## 7. Dependências e Restrições

### Dependências
- Estrutura ADR002 criada
- Skybridge legada em `B:\_repositorios\Hadsteca\modules\skybridge` (referência)

### Restrições
- Não copiar cegamente da legada — adaptar para nova estrutura
- Mínimo viable para validar arquitetura
- Código deve ser limpo, mas não over-engineered

## 8. Entregáveis

- Kernel base (`src/skybridge/kernel/`)
- Platform bootstrap (`src/skybridge/platform/`)
- Health query handler (`src/skybridge/core/contexts/...` ou `shared/`)
- API app (`apps/api/`)
- Ngrok script (`scripts/ngrok.py` ou similar)
- Config base (`config/base.yaml`)
- README com instruções (`README.md` na raiz ou em `apps/api/`)

## 9. Próximos Passos

1. Explorar skybridge legada para entender patterns usados
2. Implementar Kernel base (Result, Envelope)
3. Implementar Health Query
4. Implementar Platform bootstrap + FastAPI
5. Configurar Ngrok
6. Testar e validar
7. Documentar

---

## ADRs Relacionados

- [ADR002](../adr/ADR002-Estrutura.md) — Estrutura do Repositório
- [ADR003](../adr/ADR003-Glossário.md) — Glossário, Arquiteturas e Padrões

## SPECs a Serem Criadas

- SPEC000 — Envelope CQRS (payload, erros, correlation)
- SPEC001 — Config (formatos, merge, env naming)

---

> "A prova de conceito é a verdade que valida o papel." – made by Sky ✨
