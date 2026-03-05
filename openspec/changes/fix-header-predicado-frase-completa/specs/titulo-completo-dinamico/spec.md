# Spec: Titulo Completo Dinâmico

Capability para títulos de chat com predicados dinâmicos que formam frases completas fluentes, conforme especificação original da UI Textual.

## ADDED Requirements

### Requirement: EstadoLLM possui campo predicado

O dataclass `EstadoLLM` SHALL possuir um campo `predicado: str` para armazenar o predicado do título, permitindo que o DTO transporte todos os dados textuais do título (verbo + predicado) junto com os dados de animação.

#### Scenario: EstadoLLM inicializado com predicado padrão

- **WHEN** `EstadoLLM` é instanciado sem parâmetros
- **THEN** campo `predicado` SHALL ter valor padrão `"conversa"`

#### Scenario: EstadoLLM inicializado com predicado customizado

- **WHEN** `EstadoLLM` é instanciado com `predicado="erro na API"`
- **THEN** campo `predicado` SHALL ter valor `"erro na API"`

#### Scenario: EstadoLLM serializa corretamente

- **WHEN** `EstadoLLM` é convertido para string ou dict
- **THEN** campo `predicado` SHALL estar incluído na representação

---

### Requirement: ChatHeader usa predicado do EstadoLLM

O método `ChatHeader.update_estado()` SHALL usar o valor de `estado.predicado` quando o parâmetro opcional `predicado` não é fornecido, eliminando a necessidade de passar dois valores separados.

#### Scenario: update_estado sem predicado usa estado.predicado

- **WHEN** `ChatHeader.update_estado(estado)` é chamado apenas com `EstadoLLM`
- **AND** `estado.predicado` é `"estrutura do projeto"`
- **THEN** `ChatHeader._predicado` SHALL ser atualizado para `"estrutura do projeto"`

#### Scenario: update_estado com predicado override usa valor fornecido

- **WHEN** `ChatHeader.update_estado(estado, predicado="valor custom")` é chamado
- **THEN** `ChatHeader._predicado` SHALL ser atualizado para `"valor custom"` (ignora `estado.predicado`)

#### Scenario: update_estado com predicado None usa estado.predicado

- **WHEN** `ChatHeader.update_estado(estado, predicado=None)` é chamado
- **THEN** `ChatHeader._predicado` SHALL ser atualizado para `estado.predicado`

---

### Requirement: Verbos de teste possuem predicados completos

A lista `_VERBOS_TESTE` SHALL conter entradas onde cada `EstadoLLM` possui um `predicado` com 2 ou mais palavras, formando frases completas quando combinadas com o sujeito "Sky" e o verbo.

#### Scenario: Cada entrada de _VERBOS_TESTE tem predicado com múltiplas palavras

- **WHEN** `_VERBOS_TESTE` é iterado
- **THEN** cada `EstadoLLM` na lista SHALL ter `predicado` com pelo menos 2 palavras

#### Scenario: Título completo é formado corretamente

- **DADO** `_VERBOS_TESTE` contém `("analisando", EstadoLLM(verbo="analisando", predicado="estrutura do projeto"))`
- **QUANDO** este estado é usado no `AnimatedTitle`
- **ENTÃO** título exibido SHALL ser `"Sky analisando estrutura do projeto"`

#### Scenario: Predicados variados fornecem contexto visual

- **WHEN** usuário cicla através de `_VERBOS_TESTE` com `Ctrl+V`
- **THEN** cada título exibido SHALL ser visualmente distinto e descritivo

---

### Requirement: Titulo segue formato Sujeito-Verbo-Predicado

O título SHALL seguir o formato `"Sujeito Verbo Predicado"` onde:
- Sujeito é `"Sky"` (fixo)
- Verbo é um gerúndio animado em português (terminado em -ando ou -endo)
- Predicado é uma frase descritiva de 2-5 palavras

#### Scenario: Titulo tem exatamente 3 componentes

- **QUANDO** título é renderizado
- **ENTÃO** título SHALL consistir de sujeito + espaço + verbo + espaço + predicado

#### Scenario: Predicado pode ter múltiplas palavras

- **DADO** predicado é `"configuração completa do ambiente"`
- **QUANDO** título é renderizado
- **ENTÃO** resultado SHALL ser `"Sky {verbo} configuração completa do ambiente"`

#### Scenario: Exemplos da especificação original são válidos

- **DADO** especificação define exemplos como `"Sky debugando erro na API"` e `"Sky aprendendo async Python"`
- **QUANDO** sistema gera títulos
- **ENTÃO** títulos SHALL seguir este mesmo formato de frase completa

---

### Requirement: Compatibilidade backward com API existente

A mudança SHALL manter compatibilidade total com código existente que chama `ChatHeader.update_estado()` com apenas o parâmetro `estado`.

#### Scenario: Código legado continua funcionando

- **DADO** código existente chama `header.update_estado(estado)` sem predicado
- **QUANDO** este código é executado após a mudança
- **ENTÃO** código SHALL funcionar sem erro (usa `estado.predicado` como fallback)

#### Scenario: Assinatura do método é mantida

- **QUANDO** `ChatHeader.update_estado()` é inspecionado
- **ENTÃO** assinatura SHALL ser `update_estado(self, estado: EstadoLLM, predicado: str | None = None)`

#### Scenario: Predicado continua sendo opcional

- **QUANDO** `ChatHeader` é instanciado
- **ENTÃO** parâmetro `predicado` SHALL continuar sendo opcional em todos os métodos

---

> "Especificação é a promessa que o código cumpre" – made by Sky 🚀
