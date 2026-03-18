# Visão de Produto — Skybridge (embrionária → multi-tenant)

## 0) Essência
Skybridge é uma ponte prática entre intenção humana e execução assistida por IA: automatiza operações (arquivos, tarefas, publicação) com segurança, rastreabilidade e múltiplas interfaces (API/CLI/REPL/UI).

## 1) Forma 1 — Tooling Local (Hoje)
**O que é (hoje)**
- Ferramenta local para produtividade do desenvolvedor: **FileOps + Tasks + Versionar/Entregar**.
- Roda na sua máquina (single-user), com API local + CLI/REPL.
- Prioriza: velocidade de uso, segurança (allowlist/secret scan), logs e evidências.

**O que não é (ainda)**
- Não é SaaS, não tem billing, nem multi-tenant.
- Não promete “marketplace”; plugins existem apenas como organização interna.

## 2) Forma 2 — Plataforma Pessoal de Agentes (Próxima)
**O que é**
- Um “runtime” para agentes e automações com **contratos estáveis** (CQRS/tools), permissões e auditoria.
- Plugins internos para integrações (Discord/Trello/Spotify/VSCode/MCP) com configuração declarativa.
- Governança forte: ADR/PRD/SPEC + promoção de rascunhos para docs.

**O que não é (ainda)**
- Não é produto para terceiros; ainda é “dev platform” para você.
- Não exige alta disponibilidade nem operações em cloud.

## 3) Forma 3 — Produto para Times (Single-tenant / Self-host)
**O que é**
- Skybridge empacotada para um time pequeno: um servidor por time (self-host).
- Controle de acesso, auditoria, rotinas de release, e um painel simples (frontend).
- Integrações como plugins instaláveis e versionadas.

**O que não é (ainda)**
- Não é multi-tenant; não há isolamento por cliente na mesma instância.
- Não há marketplace público; distribuição pode ser por git/zip/registry privado.

## 4) Forma 4 — Ecossistema de Plugins (Pré-market)
**O que é**
- Contrato de plugin estabilizado (manifest, permissões, compatibilidade por versão).
- Catálogo curado (inicialmente privado) de “packs” de automação e integrações.
- Métricas e telemetria controladas para qualidade dos plugins (opt-in).

**O que não é (ainda)**
- Não é um marketplace aberto com pagamento automático.
- Não tem suporte amplo; foco em curadoria e qualidade.

## 5) Forma 5 — SaaS Multi-tenant (Futuro)
**O que é**
- Skybridge como serviço: múltiplos clientes na mesma infraestrutura, com isolamento e limites.
- Autenticação robusta, rate limiting, billing, painel admin, e observabilidade completa.
- Plugins instaláveis por tenant com permissões, quotas e auditoria.

**O que não é (ainda)**
- Não é prioridade enquanto o core (FileOps/Tasks/Release) não estiver maduro e comprovado em uso real.
- Não assume arquitetura cloud complexa antes de validar valor e repetibilidade.

## Princípios orientadores (válidos em todas as formas)
- **Local-first → depois cloud** (provar valor antes de escalar operação).
- **Core pequeno, extensões plugáveis** (evitar monólito inchado).
- **Rastreabilidade por padrão** (eventos, logs, evidências, diff/snapshots).
- **Segurança como camada** (allowlist, secret scan, auth, permissões).
- **Interfaces finas** (API/CLI/REPL/UI chamam o mesmo núcleo).

---
> "Visão clara evita engenharia cedo demais." – made by Sky ✨
