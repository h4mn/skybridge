# Delta Spec: Textual Chat UI

Especificações delta para corrigir a implementação do título dinâmico com verbo animado, garantindo que o predicado seja dinâmico e forme frases completas conforme especificado originalmente.

## MODIFIED Requirements

### Requirement: Título de sessão dinâmico com verbo animado

O sistema DEVERÁ exibir título no formato "Sujeito | Verbo Gerúndio Animado | Predicado" com animação de color sweep no verbo. **O predicado DEVERÁ ser dinâmico e formar frases completas de 2-5 palavras, NÃO um valor fixo como "conversa".**

#### Cenário: Título inicial é genérico
- **QUANDO** sessão é iniciada
- **ENTÃO** título é "Sky iniciando conversa"
- **E** verbo "iniciando" exibe animação color sweep
- **E** predicado "conversa" é apenas o valor inicial, NÃO permanente

#### Cenário: Título é regerado após 2-3 turnos
- **QUANDO** conversa tem 3 ou mais turnos
- **ENTÃO** Sky analisa contexto para inferir tópico
- **E** título é atualizado para formato estruturado
- **E** formato é: "Sky <verbo-gerúndio> <predicado>"
- **E** exemplos: "Sky debugando erro na API", "Sky aprendendo async Python"
- **E** **predicado é uma frase completa (2-5 palavras), NÃO uma palavra fixa**

#### Cenário: Animação color sweep no verbo
- **QUANDO** verbo é exibido
- **ENTÃO** onda de cor percorre letras da esquerda para direita
- **E** animação é contínua (loop infinito)
- **E** cor alterna entre cor primária e cor de destaque
- **E** duração do ciclo é aproximadamente 2 segundos

#### Cenário: Título é atualizado se tópico mudar
- **QUANDO** contexto da conversa muda significativamente
- **ENTÃO** Sky detecta mudança de tópico
- **E** título é regerado para refletir novo contexto
- **E** transição é suave (não há flicker)

#### Cenário: Predicado forma frase completa
- **QUANDO** título é atualizado após análise de contexto
- **ENTÃO** predicado consiste de 2 ou mais palavras descritivas
- **E** predicado forma uma frase fluida com sujeito e verbo
- **E** exemplo válido: "Sky analisando estrutura do projeto" (predicado = 3 palavras)
- **E** exemplo INVÁLIDO: "Sky analisando conversa" (predicado = 1 palavra fixa)

#### Cenário: EstadoLLM transporta predicado completo
- **QUANDO** `EstadoLLM` é usado para transportar dados do título
- **ENTÃO** `EstadoLLM` DEVERÁ possuir campo `predicado`
- **E** valor de `predicado` DEVERÁ ser usado pelo título quando aplicável
- **E** `EstadoLLM` torna-se DTO completo (texto + animação)

#### Cenário: Verbos de teste exibem frases completas
- **QUANDO** sistema está em modo de teste (`_VERBOS_TESTE`)
- **ENTÃO** cada entrada DEVERÁ ter um predicado completo de 2+ palavras
- **E** título exibido DEVERÁ ser visualmente distinto entre diferentes verbos
- **E** exemplo: "Sky analisando estrutura do projeto", "Sky codando widgets Textual"

---

> "Delta specs corrigem implementação sem alterar a promessa original" – made by Sky 🚀
