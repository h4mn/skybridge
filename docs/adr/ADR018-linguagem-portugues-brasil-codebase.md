---
status: aceito
data: 2026-01-11
---

# ADR018 — Textos legíveis por humanos em Português Brasileiro

**Status:** Aceito
**Data:** 2026-01-11

## Contexto

O time de desenvolvimento da Skybridge é brasileiro e a maioria dos textos no código
(comentários, logs, mensagens de erro) está em inglês. Isso cria uma barreira desnecessária
para compreensão e manutenção do código, já que desenvolvedores precisam traduzir mentalmente
termos técnicos que poderiam estar em sua língua nativa.

Textos legíveis por humanos incluem:
- Logs de aplicação (logger.info, logger.error, etc)
- Mensagens de erro
- Comentários de código
- Strings de exceção
- Mensagens de validação
- Documentação inline

**NÃO incluem:**
- Nomes de variáveis, funções, classes (identificadores)
- Keywords da linguagem de programação
- Nomes de protocolos, formatos e padrões técnicos (JSON, HTTP, REST, etc)
- Terminologia técnica sem tradução direta aceita (middleware, endpoint, etc)

## Decisão

1. **Português Brasileiro para textos legíveis**
   - Todo texto legível por humano em Python deve estar em português brasileiro (pt-BR)
   - Logs de aplicação devem usar pt-BR nas mensagens
   - Mensagens de erro devem ser em pt-BR
   - Comentários de código devem ser em pt-BR

2. **Identificadores mantêm inglês**
   - Nomes de variáveis, funções, classes permanecem em inglês
   - Nomes de módulos e pacotes permanecem em inglês
   - Isso mantém consistência com ecossistema Python/bibliotecas

3. **Terminologia técnica**
   - Termos sem tradução aceita permanecem em inglês
   - Exemplos: middleware, endpoint, payload, webhook, snapshot, etc
   - Mas frases around esses termos devem ser em pt-BR

## Exemplos

### ✅ Correto

```python
# Executa agente Claude Code
logger.info("Executando agente Claude Code", extra={"job_id": job_id})

# Cria diretório .sky/ para log interno do agente
os.makedirs(sky_dir, exist_ok=True)

if not os.path.exists(path):
    raise FileNotFoundError(f"Arquivo não encontrado: {path}")

# Processa job e retorna resultado
result = process_job(job)
```

### ❌ Incorreto

```python
# Execute Claude Code agent
logger.info("Executing Claude Code agent", extra={"job_id": job_id})

# Create .sky/ directory for agent log
os.makedirs(sky_dir, exist_ok=True)

if not os.path.exists(path):
    raise FileNotFoundError(f"File not found: {path}")

# Process job and return result
result = process_job(job)
```

## Alternativas Consideradas

1. **Manter tudo em inglês**
   - Rejeitada: cria barreira desnecessária para time brasileiro
   - Dificulta onboarding de novos desenvolvedores
   - Reduz velocidade de desenvolvimento

2. **Traduzir identificadores também**
   - Rejeitada: quebraria compatibilidade com ecossistema Python
   - Bibliotecas e frameworks usam inglês
   - Código ficaria inconsistente

## Consequências

### Positivas

- Desenvolvedores brasileiros leem código sem barreira linguística
- Onboarding mais rápido para novos membros do time
- Logs mais claros para debug em produção
- Comentários mais úteis para contexto

### Negativas / Trade-offs

- Código não é imediatamente compreensível para desenvolvedores estrangeiros
- Requer disciplina para manter consistência

## DoD

- Todos os logs de aplicação em pt-BR
- Mensagens de erro em pt-BR
- Comentários de código em pt-BR
- Identificadores (variáveis, funções) em inglês
- Esta ADR referenciada em guias de estilo

> Clareza para quem constrói, não para quem lê passivamente. – made by Sky 🚀
