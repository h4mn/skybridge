# Spec: Personalidade da Sky (Delta)

## MODIFIED Requirements

### Requirement: Formatação markdown nas respostas

O sistema DEVERÁ usar formatação markdown quando apropriado para melhorar legibilidade, renderizada via Textual com CSS customizado.

#### Cenário: Blocos de código com syntax highlighting Textual
- **QUANDO** resposta inclui código ou exemplos técnicos
- **ENTÃO** código é formatado em blocos markdown com crases triplas
- **E** identificador de linguagem é especificado quando conhecido (python, bash, etc.)
- **E** syntax highlighting é aplicado via CSS Textual
- **E** cores de syntax são customizáveis via arquivo CSS

#### Cenário: Negrito com CSS customizado
- **QUANDO** enfatizando pontos-chave ou informação importante
- **ENTÃO** markdown negrito é usado (**texto**)
- **E** cor e estilo são definidos via CSS Textual
- **E** ênfase é usada parcimoniosamente para máximo impacto

#### Cenário: Listas com indentação correta
- **QUANDO** resposta contém múltiplos itens relacionados
- **ENTÃO** itens são formatados como listas bullet ou numeradas
- **E** MarkdownText widget do Textual renderiza lista corretamente
- **E** indentação é preservada
- **E** marcadores são estilizados via CSS

#### Cenário: Links clicáveis
- **QUANDO** markdown contém links
- **ENTÃO** links são exibidos em cor distinta definida via CSS
- **E** links são clicáveis (abre no browser padrão ao Enter ou clique)

---

## ADDED Requirements

### Requirement: MarkdownText widget com CSS customizado

O sistema DEVERÁ usar MarkdownText widget do Textual com CSS customizado para renderização de markdown.

#### Cenário: MarkdownText é usado para mensagens da Sky
- **QUANDO** resposta da Sky contém markdown
- **ENTÃO** MarkdownText widget é usado para renderizar
- **E** CSS customizado é aplicado
- **E** tema padrão é usado (cores definidas em CSS)

#### Cenário: CSS define cores de markdown
- **QUANDO** markdown é renderizado
- **ENTÃO** cor de código é definida via CSS (ex: laranja para Python)
- **E** cor de links é definida via CSS (ex: azul claro)
- **E** cor de negrito é definida via CSS (ex: branco com brilho)

#### Cenário: Usuário pode customizar CSS
- **QUANDO** usuário quer mudar cores de markdown
- **ENTÃO** arquivo CSS pode ser editado
- **E** mudanças são aplicadas ao reiniciar chat
- **E** múltiplos temas podem ser fornecidos (dark, light, etc.)

---

> "Personalidade não é o que você diz, é como você faz os outros sentirem" – made by Sky 🚀
