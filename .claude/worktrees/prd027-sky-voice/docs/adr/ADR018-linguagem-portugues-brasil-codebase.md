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

## Motivação: Alinhamento com Práticas Internacionais

Esta decisão não é isolada — ela se alinha com padrões adotados por comunidades de desenvolvimento ao redor do mundo que enfrentam os mesmos desafios de trabalhar com idiomas não-ingleses.

### Consenso Global

Pesquisa com desenvolvedores de diversas comunidades (chinesa, árabe, russa, europeia) revela um **consenso claro** sobre melhores práticas para projetos em idiomas não-ingleses:

| Componente | Consenso Global | Decisão Skybridge |
|------------|-----------------|-------------------|
| Nomes de variáveis, funções, classes | 🇺🇸 Inglês (100%) | 🇺🇸 Inglês ✅ |
| Comentários de código | 🌐 Idioma nativo | 🇧🇷 PT-BR ✅ |
| Logs de aplicação | 🌐 Idioma nativo | 🇧🇷 PT-BR ✅ |
| Mensagens de erro/validação | 🌐 Idioma nativo | 🇧🇷 PT-BR ✅ |
| Termos técnicos sem tradução | 🇺🇸 Inglês (middleware, endpoint) | 🇺🇸 Inglês ✅ |

### Exemplos de Outras Comunidades

**Comunidade Chinesa (🇨🇳 Alibaba):**
> "【强制】所有编程相关的命名严禁使用拼音与英文混合的方式，更不允许直接使用中文的方式。说明：正确的英文拼写和语法可以让阅读者易于理解，避免歧义。"

*Tradução:* "É **obrigatório** que todos os nomes relacionados à programação sejam em inglês. O inglês correto torna o código compreensível e evita ambiguidade."

**Comunidade Árabe (🇸🇦):**
Devido a questões técnicas de scripts RTL (Right-to-Left), desenvolvedores árabes mantêm identificadores em inglês e usam árabe apenas em comentários.

**Comunidade Russa (🇷🇺):**
Estudos acadêmicos mostram que desenvolvedores russos adotam universalmente: código em inglês + comentários/logs em russo.

**Comunidade Europeia (🇳🇱 Países Baixos):**
O artigo seminal ["Programming on a Non-English Project"](https://berk.es/2012/10/05/programming-on-a-none-english-project-best-practices/) (Berk Kessels, 2012) estabelece a **"Regra da Exceção Única"**: código deve ser em inglês sempre, sem exceções; comentários e documentação podem seguir o idioma nativo. Esta abordagem permanece válida 15 anos depois.

### System Prompts de Agentes AI

Considerando a SPEC008 e o uso de agentes autônomos no Skybridge, os **system prompts** (`src/runtime/config/system_prompt.json`) seguem o mesmo princípio:

- **Instruções técnicas** devem ser em PT-BR (alinhado com ADR018)
- **Output JSON** com nomes de campos em inglês (interoperabilidade)
- **Thinkings/raciocínio** em PT-BR (observabilidade para time brasileiro)

**Tradeoffs analisados:**
- ✅ Coerência com ADR018 e código em PT-BR
- ✅ Manutenibilidade para time brasileiro
- ⚠️ Performance de LLM em PT-BR é ~2-3% inferior (impacto mínimo)
- ⚠️ Colaboração internacional mitigada via documentação bilíngue

### Referências

- [Programming on a Non-English Project; best practices](https://berk.es/2012/10/05/programming-on-a-none-english-project-best-practices/) — Berk Kessels, 2012
- [Alibaba Java Development Guidelines](https://xiaoxue-images.oss-cn-shenzhen.aliyuncs.com/%25E9%2598%25BF%25E9%2587%258C%25E5%25B7%25B4%25E5%25B7%25B4Java%25E5%25BC%2580%25E5%258F%2591%25E8%25A7%2584%25E8%258C%2583%25EF%25BC%2588%25E5%25B5%25A9%25E5%25B1%25B1%25E7%2589%2588%25EF%25BC%2589.pdf) — Seção de nomenclatura
- [W3C Internationalization Best Practices](https://www.w3.org/TR/international-specs/)
- [Right-to-Left Languages Localization](https://www.ecinnovations.com/blog/right-to-left-languages-localization/)

A decisão do Skybridge, portanto, não é uma exceção ou um experimento — é uma prática madura e testada por comunidades globais que enfrentam os mesmos desafios linguísticos.

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
