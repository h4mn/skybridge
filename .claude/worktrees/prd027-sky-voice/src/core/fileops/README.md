# FileOps Context — Operações de Arquivo Seguras

## O que é

Bounded Context para operações de arquivo com segurança, allowlist e auditoria.

## Linguagem e Limites

### Responsabilidades (dentro)
- Operações de arquivo: read, write, delete, move, copy
- Políticas de acesso: allowlist de root/patterns
- Auditoria: logs de todas as operações
- Secret scanning: detecção de dados sensíveis

### Responsabilidades (fora)
- Sync com serviços externos (infra/integrations)
- UI/UX (apps)
- Automação de orquestração complexa (application layer ou plugins)

## Entidades e Invariantes

- **AllowedPath**: path permitido com configuração de access level
- **FileOperation**: registro de operação executada
- **AuditEntry**: trilha imutável de operações

## Eventos Emitidos

- `FileOperationRequested` — operação solicitada
- `FileOperationCompleted` — operação concluída com sucesso
- `FileOperationFailed` — operação falhou
- `SecretDetected` — dado sensível encontrado

## Dependências Permitidas

### Ports (interfaces)
- `FileSystemPort` — abstração de IO
- `SecurityPolicyPort` — validação de allowlist
- `AuditLogPort` — persistência de auditoria
- `SecretScannerPort` — detecção de dados sensíveis

### Adapters
- Implementações concretas vivem em `infra/contexts/fileops/`

---

> "Segurança sem fricção é segurança que funciona." – made by Sky ✨
