# Histórico do Projeto Skybridge

**Última atualização:** 2026-01-06

---

## Linha do Tempo

```
2025-04-23 ──────────────► 2025-05-25 ──────────────► 2025-12-22 ──────────────► 2026-01-06
   Sky_Bridge                  sky-bridge                  ADR000               Atual
 (primeira tentativa)      (segunda tentativa)        (governança)         (skybridge/)
```

---

## Iteração 1: Sky_Bridge (2025-04-23)

**Repositório:** `h4mn/Sky_Bridge`
**Status:** Arquivado (planejado)

### Descrição Original
> "Sky_Bridge é o núcleo que conecta a Sky — uma assistente virtual em constante evolução — com o mundo real."

### Proposta de Valor
- **Conectar diferentes serviços e plataformas** — Ponte entre mundos
- **Executar ações com contexto e intenção** — Não apenas automação cega
- **Aprender e evoluir com o uso** — Evolução contínua

### Roadmap Original

#### 🔌 Integrações e Plataformas
- [ ] Conectar novos módulos de automação
- [ ] Integrar com sistemas externos (Jira, Notion...)
- [ ] Integração com Discord para notificações dos changelogs

#### 🧠 Experiência da Sky
- [ ] Comandos para manipular commits, branches e PRs via SkyBridge
- [ ] Padronizar fluxo: issue → PR → tag, com changelog e release automáticos

#### 🧱 Estrutura e Arquitetura
- [ ] Arquitetura de módulos para extensibilidade
- [ ] Expor docs via FastAPI Swagger

### Aprendizados
- **Nome**: Sky_Bridge (com underscore)
- **Foco**: Conexão com "Sky" (assistente virtual)
- **Princípio**: Evolução constante

---

## Iteração 2: sky-bridge (2025-05-25)

**Repositório:** `h4mn/sky-bridge`
**Status:** Arquivado (planejado)

### Descrição Original
> "Sky Bridge é um hub que apoia a orquestração de serviços para o consumo de LLMs de desenvolvimento. Sky Bridge é o núcleo que conecta agentics como a Sky — uma assistente virtual em constante evolução — com o mundo real."

### Evolução desde a Iteração 1
- **Mudança de foco**: De "conexão" para "orquestração de serviços para LLMs"
- **Conceito de "agentics"**: Agentes + Robotics (IA autônoma)
- **Infraestrutura madura**: Testes, Docker, CI/CD

### Implementações

#### ✅ Já Realizado
- [x] Testes automatizados (pytest)
- [x] Dockerização
- [x] CI/CD
- [x] **SemVer + Commitizen** (cz.yaml, VERSION)
- [x] Padrões de código: black, isort, pylint

#### 🎯 Planejado (mas não implementado)
- [ ] Conexão com LLMs
- [ ] Orquestração de serviços
- [ ] Documentação automatizada

### Estrutura Técnica

```
sky-bridge/
├── doc/              # Documentação do projeto
├── src/              # Código fonte
├── test/             # Testes
├── script/           # Scripts utilitários
├── VERSION           # Versão atual (single source of truth!)
├── pytest.ini        # Configuração do pytest
├── cz.yaml           # Configuração do commitizen
├── pyproject.toml    # Configuração do projeto Python
├── requirements.txt  # Dependências
├── Dockerfile        # Container Docker
├── docker-compose.yml # Orquestração
└── .dockerignore     # Ignorados pelo Docker
```

### Aprendizados
- **Nome**: sky-bridge (com hífen)
- **Arquivo VERSION**: Já previa single source of truth (hoje no ADR012)
- **Commitizen**: Já usava Conventional Commits (hoje no ADR012)
- **Princípio**: Infraestrutura antes de funcionalidade

---

## Iteração 3: skybridge (2025-12-22 — Presente)

**Repositório:** `h4mn/skybridge` (a ser criado)
**Diretório local:** `B:\_repositorios\skybridge`
**Status:** Ativo

### Evolução desde as Iterações Anteriores

#### Governança de Decisões
- **ADR000** (2025-12-22): Discovery via snapshot + scoring
- **ADR001**: Feature mapping por entidade
- **ADR002**: Monólito Modular + DDD + Microkernel
- **ADR003**: Glossário oficial + padrões
- **ADR012**: Estratégia de versionamento (retoma ideia de VERSION)
- **+10 ADRs** cobrindo arquitetura, protocolo, segurança

#### Separação de Conceitos
- **Core vs Plugins**: Microkernel explícito (ADR002)
- **FileOps**: Contexto para operações de arquivo
- **Tasks**: Contexto para tarefas/automação
- **Sky-RPC**: Protocolo de comunicação (evoluído de JSON-RPC)

### Diferenças-chave

| Aspecto | Iteração 1-2 | Iteração 3 (Atual) |
|---------|--------------|-------------------|
| **Nome** | Sky_Bridge / sky-bridge | skybridge |
| **Foco** | Conexão com Sky | Orquestração + Governança |
| **Infra** | Docker + CI/CD | ADRs + PRDs + SPECs |
| **Versionamento** | Commitizen | ADR012 (Semver + CC + Workflows) |
| **Protocolo** | Não definido | Sky-RPC v0.3 |
| **Arquitetura** | Módulos | Monólito Modular + DDD |

---

## Conexões com "Sky"

**Sky** é mencionada como:
- "Uma assistente virtual em constante evolução"
- Motivação para criar uma ponte com o mundo real
- Personagem/entidade que dá nome ao projeto

### Simbologia
- 🌉 **Ponte**: Conexão entre mundos (intenção ↔ execução)
- ☁️ **Nuvem/Sky**: Camada de inteligência/IA
- 🔮 **Agentry**: Agentes autônomos operando a ponte

---

## Princípios que Permaneceram

1. **Evolução constante** — O sistema aprende e melhora com o uso
2. **Conexão com mundo real** — Não é apenas teoria, executa ações reais
3. **Infraestrutura primeiro** — Testes, Docker, CI/CD antes de funcionalidades
4. **Contexto e intenção** — Não é automação cega, executa com propósito
5. **Extensibilidade** — Plugins, módulos, integrações

---

## Próximos Passos

- [ ] Criar repositório `h4mn/skybridge`
- [ ] Mover ADRs, PRDs, SPECs para o novo repositório
- [ ] Configurar GitHub Actions para workflows do ADR012
- [ ] Implementar Fase 1 do PRD012 (inventário de versões)
- [ ] Arquivar/privar repositórios antigos (Sky_Bridge, sky-bridge)

---

## Referências Históricas

- [Sky_Bridge (GitHub)](https://github.com/h4mn/Sky_Bridge) — Primeira tentativa
- [sky-bridge (GitHub)](https://github.com/h4mn/sky-bridge) — Segunda tentativa
- [skybridge (local)](B:\_repositorios\skybridge) — Iteração atual

---

> "O passado é o pré-rendering do futuro."
> "Cada tentativa anterior foi um commit na direção certa."
> — made by Sky 📜✨
