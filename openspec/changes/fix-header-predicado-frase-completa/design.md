# Design: Fix Header Predicado Frase Completa

## Context

### Estado Atual

O header do Sky Chat implementa o título dinâmico com verbo animado usando `AnimatedTitle`, que compõe três partes: sujeito ("Sky"), verbo (animado via `AnimatedVerb`), e predicado. O verbo é animado via `EstadoLLM`, um dataclass que controla dimensões da animação (certeza, esforço, emoção, direção).

**Problema identificado:**
- `EstadoLLM` não possui campo `predicado`, apenas `verbo`
- `_VERBOS_TESTE` contém apenas verbos isolados sem predicados
- `ChatHeader.__init__` define predicado padrão como `"conversa"` e nunca é atualizado
- Resultado visual: `"Sky analisando conversa"`, `"Sky buscando conversa"` (predicado fixo de 1 palavra)

### Restrições

- **Compatibilidade backward**: Código existente que chama `update_estado(estado)` deve continuar funcionando
- **API pública**: `ChatHeader.update_estado()` tem parâmetro opcional `predicado` que não pode ser removido
- **TDD Estrito**: Mudanças devem seguir Red → Green → Refactor com testes primeiro

---

## Goals / Non-Goals

### Goals
1. `EstadoLLM` tornar-se DTO completo para dados do título (texto + animação)
2. Predicados em `_VERBOS_TESTE` serem frases completas (2-5 palavras)
3. `ChatHeader.update_estado(estado)` sem predicado usar `estado.predicado`
4. Compatibilidade total com API existente

### Non-Goals
- ❌ Modificar comportamento de animação (cores, velocidade, oscilação)
- ❌ Alterar formato do título (continua "Sujeito Verbo Predicado")
- ❌ Modificar `AnimatedVerb` ou animação de color sweep
- ❌ Criar novos tipos ou classes (usar `EstadoLLM` existente)

---

## Decisões

### DECISÃO 1: Adicionar `predicado` ao `EstadoLLM`

**Escolha:** Adicionar campo `predicado: str = "conversa"` ao dataclass `EstadoLLM`

**Por que:**
- `EstadoLLM` já é DTO para dados do título (não gera animação, `AnimatedVerb` sim)
- Centraliza todos os dados do título em um lugar
- Facilita transporte: passar 1 objeto em vez de 2 parâmetros
- Serialização simples para logs/debug

**Alternativas rejeitadas:**
- ❌ Criar `TituloCompleto` (dataclass separado) → overhead desnecessário
- ❌ Usar `NamedTuple` → menos extensível que dataclass
- ❌ Manter predicado separado → fragmenta dados, viola coesão

**Implementação:**
```python
@dataclass
class EstadoLLM:
    # === TEXTO ===
    verbo: str = "iniciando"
    predicado: str = "conversa"  # ← ADICIONAR

    # === ANIMAÇÃO ===
    certeza: float = 0.8
    esforco: float = 0.5
    emocao: str = "neutro"
    direcao: int = 1
```

---

### DECISÃO 2: `ChatHeader.update_estado()` usar `estado.predicado` como fallback

**Escolha:** Quando `predicado=None`, usar `estado.predicado`

**Por que:**
- Mantém compatibilidade com código que passa apenas `estado`
- Permite override explícito quando necessário
- Follows principle of least surprise

**ANTES (quebrado):**
```python
def update_estado(self, estado: EstadoLLM, predicado: str | None = None):
    if predicado is not None:
        self._predicado = predicado  # ← Só atualiza se explicito
    # predicado nunca muda se None
```

**DEPOIS (corrigido):**
```python
def update_estado(self, estado: EstadoLLM, predicado: str | None = None):
    # Usa estado.predicado como fallback
    self._predicado = predicado if predicado is not None else estado.predicado
    title.update_estado(estado, self._predicado)
```

---

### DECISÃO 3: `_VERBOS_TESTE` com tuplas nomeadas ou dataclasses

**Escolha:** Manter formato atual mas adicionar predicado em cada `EstadoLLM`

**Por que:**
- Mudança mínima (já existe estrutura)
- `EstadoLLM` agora tem campo `predicado`
- Não cria novos tipos

**ANTES (quebrado):**
```python
_VERBOS_TESTE: list[tuple[str, EstadoLLM]] = [
    ("analisando", EstadoLLM(verbo="analisando", certeza=0.7, ...)),
    #                                           ↑ sem predicado
]
```

**DEPOIS (corrigido):**
```python
_VERBOS_TESTE: list[tuple[str, EstadoLLM]] = [
    ("analisando", EstadoLLM(
        verbo="analisando",
        predicado="estrutura do projeto",  # ← ADICIONAR
        certeza=0.7, ...
    )),
]
```

---

### DECISÃO 4: Valores de predicado em `_VERBOS_TESTE`

**Escolha:** Predicados descritivos de 2-5 palavras relacionados ao verbo

**Por que:**
- Segue exemplos da especificação ("erro na API" = 3 palavras)
- Fornece contexto visual do que está sendo feito
- Diversifica os títulos para teste visual

**Exemplos:**
| Verbo | Predicado | Resultado |
|-------|-----------|-----------|
| analisando | estrutura do projeto | "Sky analisando estrutura do projeto" |
| codando | implementação de widgets | "Sky codando implementação de widgets" |
| refletindo | melhor abordagem possível | "Sky refletindo melhor abordagem possível" |
| criando | novos componentes Textual | "Sky criando novos componentes Textual" |
| buscando | informações relevantes | "Sky buscando informações relevantes" |

---

## Sequência de Implementação (TDD)

### 1. RED - Testes que falham

```python
# tests/unit/core/sky/chat/textual_ui/widgets/test_animated_verb.py
async def test_estadollm_possui_campo_predicado():
    """EstadoLLM deve ter campo predicado com valor padrão 'conversa'."""
    estado = EstadoLLM()
    assert hasattr(estado, "predicado")
    assert estado.predicado == "conversa"

async def test_estadollm_aceita_predicado_customizado():
    """EstadoLLM deve aceitar predicado customizado no init."""
    estado = EstadoLLM(predicado="erro na API")
    assert estado.predicado == "erro na API"

async def test_chatheader_update_estado_usa_predicado_do_estado():
    """ChatHeader.update_estado() deve usar estado.predicado quando predicado=None."""
    header = ChatHeader()
    estado = EstadoLLM(verbo="debugando", predicado="código quebrado")
    header.update_estado(estado)  # sem predicado
    assert header._predicado == "código quebrado"

async def test_verbos_teste_possuem_predicados_completos():
    """_VERBOS_TESTE deve ter predicados de 2+ palavras."""
    for verbo, estado in _VERBOS_TESTE:
        assert len(estado.predicado.split()) >= 2
```

### 2. GREEN - Implementação mínima

- Adicionar campo `predicado` ao `EstadoLLM`
- Modificar `ChatHeader.update_estado()`
- Atualizar `_VERBOS_TESTE`

### 3. REFACTOR - Melhorar mantendo verde

- Adicionar mais predicados variados
- Validar comprimento máximo
- Documentar no docstring

---

## Riscos / Trade-offs

### [RISCO] Breaking change em código que depende de `EstadoLLM`

**Mitigação:**
- Campo `predicado` tem valor padrão, backward compatible
- Código existente que cria `EstadoLLM()` continua funcionando
- Apenas código que serializa `EstadoLLM` pode precisar de ajuste

### [RISCO] `_VERBOS_TESTE` com strings literais pode ficar desatualizado

**Mitigação:**
- Predicados são para teste visual, não produção
- Títulos reais são gerados por LLM (`_gerar_titulo`)
- Documentar em comentário que são valores de teste

### [Trade-off] `EstadoLLM` agora mistura dois conceitos (texto + animação)

**Decisão:** Aceitável pois ambos são dados do mesmo contexto (título)
- Não há comportamento em `EstadoLLM`, apenas dados
- `AnimatedVerb` usa `EstadoLLM` mas não é contido nele
- Separação seria overkill para este caso simples

### [RISCO] LLM title gen pode não formatar corretamente

**Mitigação:**
- Prompt `_TITULO_PROMPT` já pede formato "verbo_gerúndio predicado"
- Código já faz split `titulo.split(" ", 1)` para separar verbo/predicado
- Se falhar, predicado padrão "conversa" é usado

---

## Plano de Migração

### Fase 1: Preparação (Red)
- [ ] Escrever testes que falham (TDD)
- [ ] Confirmar que testes falham como esperado

### Fase 2: Implementação (Green)
- [ ] Adicionar campo `predicado` ao `EstadoLLM`
- [ ] Modificar `ChatHeader.update_estado()`
- [ ] Atualizar `_VERBOS_TESTE`
- [ ] Confirmar que testes passam

### Fase 3: Refinamento (Refactor)
- [ ] Adicionar mais predicados variados
- [ ] Executar aplicação para validação visual
- [ ] Ajustar valores se necessário

### Fase 4: Validação
- [ ] Testar com `Ctrl+V` (ciclar verbo) para ver títulos completos
- [ ] Verificar que `_gerar_titulo` continua funcionando
- [ ] Confirmar backward compatibility

---

## Open Questions

1. **Comprimento máximo do predicado?**
   - Pergunta: Qual o limite de caracteres para predicado?
   - Decisão pendente: Usar 60 chars como limite (já existe no código)

2. **Predicados em `_VERBOS_TESTE` devem ser i18n?**
   - Pergunta: Suportar múltiplos idiomas?
   - Decisão pendente: Apenas português por enquanto (escopo limitado)

3. **Deve validar formato do predicado?**
   - Pergunta: Impedir predicados vazios ou muito curtos?
   - Decisão pendente: Validar apenas em testes, runtime aceita qualquer string

---

## Referências

- Proposal: `openspec/changes/fix-header-predicado-frase-completa/proposal.md`
- Espec original: `openspec/changes/sky-chat-textual-ui/proposal.md` (linha 23-24)
- Código: `src/core/sky/chat/textual_ui/widgets/animated_verb.py`
- Código: `src/core/sky/chat/textual_ui/widgets/header.py`
- Código: `src/core/sky/chat/textual_ui/screens/chat.py`

---

> "Design é tomar decisões conscientes e documentar o porquê" – made by Sky 🚀
