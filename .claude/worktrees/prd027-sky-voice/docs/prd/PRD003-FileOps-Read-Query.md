---
status: aceito
data: 2025-12-24
---

# PRD003 — FileOps Read Query com Allowlist

## 1. Objetivo

Implementar o primeiro caso de uso completo do FileOps Context: **leitura de arquivo com allowlist de segurança**, validado através de uma rota `/qry/fileops/read`.

## 2. Problema

Temos a estrutura do FileOps definida mas nenhum caso de uso implementado. Precisamos validar:
- A arquitetura DDD funcionando na prática
- Ports e Adapters pattern
- Allowlist de segurança (paths permitidos)
- Integração real com CQRS
- Testabilidade

## 3. Escopo

### Dentro do escopo
- **FileOps Context completo** (domain, application, ports, adapters)
- **ReadFile Query** — Ler arquivo com validação de allowlist
- **Allowlist configurável** — Duas políticas: dev e production
- **Query handler** registrado no registry
- **Rota `/qry/fileops/read`** — Com path como query parameter
- **Erro handling** — Arquivo não encontrado, path não permitido, etc.

### Fora do escopo
- Escrita de arquivos (write, delete, move)
- Operações de diretório (list, mkdir)
- Secret scanning
- Auditoria persistente
- Commands (/cmd/*)

## 4. Usuários / Stakeholders

- Desenvolvedor (teste da arquitetura)
- Sky (agente IA, para evoluir FileOps)

## 5. Requisitos

### Funcionais

#### RF001 — Allowlist de Paths
- **Dev policy**: Permite ler qualquer arquivo dentro do repositório skybridge
- **Production policy**: Permite ler apenas dentro de `\workspace`
- Configuração via environment variable

#### RF002 — ReadFile Query
- Input: `path` relativo ao allowlist root
- Output: conteúdo do arquivo como string
- Validações:
  - Path deve estar dentro do allowlist
  - Arquivo deve existir
  - Arquivo deve ser legível

#### RF003 — Rota /qry/fileops/read
- GET `/qry/fileops/read?path=README.md`
- Retorna envelope com conteúdo do arquivo
- Erros retornam com status apropriado

#### RF004 — FileOps Domain
- Entidade `AllowedPath` com regras de validação
- Value objects para paths
- Invariantes: path não pode ser vazio, deve ser relativo

### Não Funcionais

- Tipo seguro com Result
- Logs estruturados com correlation_id
- Proteção contra path traversal (`../`)
- Mensagens de erro claras

## 6. Casos de Uso

### UC001 — Ler arquivo README.md (Dev)

```
GET /qry/fileops/read?path=README.md

Response:
{
  "correlation_id": "uuid",
  "status": "success",
  "data": {
    "path": "README.md",
    "content": "# Skybridge..."
  }
}
```

### UC002 — Path fora do allowlist (Erro)

```
GET /qry/fileops/read?path=../../etc/passwd

Response:
{
  "correlation_id": "uuid",
  "status": "error",
  "error": "Path not allowed: ../../etc/passwd"
}
```

### UC003 — Arquivo não encontrado (Erro)

```
GET /qry/fileops/read?path=nao-existe.txt

Response:
{
  "correlation_id": "uuid",
  "status": "error",
  "error": "File not found: nao-existe.txt"
}
```

## 7. Configuração

### Dev (default)
```env
FILEOPS_ALLOWLIST_MODE=dev
FILEOPS_DEV_ROOT=B:\_repositorios\skybridge
```

### Production
```env
FILEOPS_ALLOWLIST_MODE=production
FILEOPS_PROD_ROOT=\workspace
```

## 8. Arquitetura

```
Request → /qry/fileops/read
        → QueryRouter
        → ReadFileHandler (application)
        → ReadFileQuery (domain)
        → FileSystemPort (interface)
        → FileSystemAdapter (infra)
        → Result<Content, Error>
        → Envelope
        → Response
```

## 9. Critérios de Sucesso

- [ ] GET `/qry/fileops/read?path=README.md` retorna conteúdo
- [ ] Path traversal (`../`) é bloqueado
- [ ] Paths fora do allowlist retornam erro
- [ ] Arquivos não existentes retornam erro
- [ ] Código segue fronteiras DDD (domain → application → port → adapter)
- [ ] Logs mostram path e correlation_id
- [ ] Testes cobrem cenários happy path e erros

## 10. Dependências e Restrições

### Dependências
- Estrutura ADR002 criada
- Kernel (Result, Envelope, Registry)
- Platform (Config, Logger, Bootstrap)

### Restrições
- Domain não pode importar Infra
- Application não depende de implementações concretas
- Allowlist validado ANTES de acessar disco

## 11. Entregáveis

- `src/skybridge/core/contexts/fileops/domain/` — Entidades e VOs
- `src/skybridge/core/contexts/fileops/application/` — Query handler
- `src/skybridge/core/contexts/fileops/ports/` — Interfaces (FileSystemPort)
- `src/skybridge/infra/contexts/fileops/` — Implementações
- `src/skybridge/platform/delivery/routes.py` — Nova rota
- Atualização de `.env.example` com config FileOps

## 12. Próximos Passos

1. Implementar domain (AllowedPath, FilePath)
2. Implementar FileSystemPort
3. Implementar ReadFileQuery handler
4. Implementar FileSystemAdapter
5. Adicionar rota /qry/fileops/read
6. Testar localmente e via ngrok
7. Documentar

---

## ADRs Relacionados

- [ADR002](../adr/ADR002-Estrutura.md) — Estrutura do Repositório
- [ADR003](../adr/ADR003-Glossário.md) — Glossário, DDD, Ports/Adapters

## SPECs Relacionadas

- SPEC000 — Envelope CQRS (já usado)
- SPEC001 — Config (já usado)

---

> "Segurança sem validação é ilusão; validação sem bloqueio é inútil." – made by Sky 🔒✨
