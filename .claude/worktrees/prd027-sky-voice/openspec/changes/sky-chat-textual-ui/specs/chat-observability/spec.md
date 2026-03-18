# Spec: Observabilidade do Chat (Delta)

## MODIFIED Requirements

### Requirement: Métricas de latência registradas

O sistema DEVERÁ registrar latência de cada geração de resposta para monitoramento de performance.

#### Cenário: Latência medida e registrada
- **QUANDO** resposta é gerada via Claude SDK
- **ENTÃO** tempo de início é marcado antes da chamada
- **E** tempo de fim é marcado após resposta recebida
- **E** latência em ms é calculada (fim - início)
- **E** latência é registrada em log estruturado

#### Cenário: Latência exibida no header Textual
- **QUANDO** resposta é gerada
- **ENTÃO** latência é exibida no header (linha 2 de métricas)
- **E** formato é "⚡1.2s" (compacto para economizar espaço)
- **E** formato completo "(1234ms)" é exibido em tooltip ao focar

#### Cenário: Alerta de latência alta como notificação Toast
- **QUANDO** latência excede 5000ms (5 segundos)
- **ENTÃO** alerta é registrado no log
- **E** notificação Toast Textual é exibida: "⚠️ Resposta demorou mais que o normal"
- **E** Toast é auto-descartável após 5 segundos ou ao pressionar ESC

---

### Requirement: Contagem de tokens registrada

O sistema DEVERÁ registrar quantidade de tokens usados (entrada e saída) para controle de custos.

#### Cenário: Tokens de entrada contados
- **QUANDO** requisição é enviada para Claude SDK
- **ENTÃO** total de tokens de entrada é registrado
- **E** contagem inclui system prompt + contexto de memória + mensagem do usuário
- **E** tokens são registrados em log estruturado

#### Cenário: Tokens de saída contados
- **QUANDO** resposta é recebida do Claude SDK
- **ENTÃO** total de tokens de saída é registrado
- **E** contagem reflete tamanho exato da resposta gerada
- **E** tokens são registrados em log estruturado

#### Cenário: Totais de sessão exibidos no header
- **QUANDO** tokens são acumulados durante sessão
- **ENTÃO** totais são exibidos no header (linha 2 de métricas)
- **E** formato é "💰 1234/10k" (tokens usados / limite estimado)
- **E** ao encerrar sessão, totais completos são exibidos em DataTable Textual

---

### Requirement: Uso de memória RAG observável

O sistema DEVERÁ registrar quantidade de memórias usadas e sua relevância para debugging.

#### Cenário: Contagem de memórias usadas
- **QUANDO** busca RAG é executada
- **ENTÃO** quantidade de memórias recuperadas é registrada
- **E** contagem distingue entre memórias acima e abaixo do threshold
- **E** contagem é incluída nas métricas da resposta

#### Cenário: Scores de similaridade registrados
- **QUANDO** memórias são recuperadas do RAG
- **ENTÃO** score de similaridade de cada memória é registrado
- **E** scores permitem analisar qualidade da busca semântica
- **E** scores são registrados em log detalhado (debug level)

#### Cenário: Memórias exibidas no header como contador
- **QUANDO** memórias são usadas na resposta
- **ENTÃO** header exibe "N mems" (ex: "3 mems")
- **E** preview detalhado é exibido como widget colapsável
- **E** ao expandir widget, memórias são listadas com scores de similaridade

---

### Requirement: Execução de tools observável

O sistema DEVERÁ registrar tools executadas durante geração de resposta para rastreamento.

#### Cenário: Tools executadas listadas
- **QUANDO** Claude usa function calling durante resposta
- **ENTÃO** cada tool executada é registrada
- **E** nome da tool e parâmetros são registrados
- **E** resultado da tool é registrado (sucesso/falha)

#### Cenário: Tools exibidas como componente Textual integrado
- **QUANDO** tools são executadas durante resposta
- **ENTÃO** componente Textual é exibido no container de mensagens
- **E** componente lista cada tool com status (⏳ executando, ✅ sucesso, ❌ falha)
- **E** componente é posicionado entre thinking e resposta final
- **E** componentes de tool são removidos ao final da resposta

#### Cenário: Falha de tool notificada com Toast
- **QUANDO** tool falha durante execução
- **ENTÃO** erro é registrado com stack trace
- **E** notificação Toast Textual é exibida: "❌ Tool <nome> falhou"
- **E** Toast é exibido por 5 segundos ou até usuário dispensar

---

### Requirement: Métricas agregadas por sessão

O sistema DEVERÁ calcular e exibir métricas agregadas ao fim de cada sessão.

#### Cenário: Resumo ao encerrar sessão com DataTable Textual
- **QUANDO** usuário digita "sair" ou Ctrl+C
- **ENTÃO** DataTable Textual é exibido com resumo da sessão
- **E** DataTable contém colunas: Métrica, Valor
- **E** linhas incluem: mensagens trocadas, latência média, tokens totais
- **E** DataTable é estilizado via CSS

#### Cenário: Comparação com sessão anterior
- **QUANDO** sessão anterior existe nos logs
- **ENTÃO** resumo compara métricas com sessão anterior
- **E** delta é mostrado (↑↓) para latência média
- **E** tendência é indicada (melhor/pior) com cor (verde para melhora, vermelho para piora)

---

## ADDED Requirements

### Requirement: Barra de progresso de contexto no header

O sistema DEVERÁ exibir barra de progresso no header indicando quanto da janela de contexto (20 mensagens) foi usada.

#### Cenário: Barra exibe porcentagem de contexto usado
- **QUANDO** histórico de mensagens é atualizado
- **ENTÃO** barra de progresso no header é recalculada
- **E** barra mostra porcentagem: (mensagens_usadas / 20) * 100
- **E** cor muda conforme faixa: verde (0-50%), amarelo (51-75%), laranja (76-90%), vermelho (91-100%)

#### Cenário: Barra alerta sobre truncamento iminente
- **QUANDO** contexto atinge 90%+ de uso
- **ENTÃO** barra fica vermelha
- **E** texto de aviso é exibido: "Contexto cheio - msgs antigas serão dropadas"

---

> "O que não é medido não pode ser melhorado" – made by Sky 🚀
