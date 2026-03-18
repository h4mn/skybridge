# Spec: Thinking UI (Delta)

## ADDED Requirements

### Requirement: Painel de pensamento colapsável

O sistema SHALL fornecer widget `ThinkingPanel` que mostra o processo de pensamento da Sky de forma colapsável.

#### Scenario: ThinkingPanel é criado no início do Turn
- **QUANDO** Turn é criado para uma mensagem do usuário
- **ENTÃO** ThinkingPanel vazio é montado no Turn
- **E** ThinkingPanel inicializa em estado expandido

#### Scenario: ThinkingPanel pode ser colapsado
- **QUANDO** usuário clica no botão de toggle [▶/[▼]
- **ENTÃO** ThinkingPanel alterna entre expandido/colapsado
- **E** estado colapsado é mantido entre mudanças

#### Scenario: ThinkingPanel mostra timestamp e contagem de tokens
- **QUANDO** ThinkingPanel é exibido
- **ENTÃO** header mostra tempo de pensamento (ex: "🤔 Thinking (2.3s)")
- **E** contagem de tokens usados é exibida (ex: "143 tokens")

---

### Requirement: Entradas de pensamento são adicionadas incrementalmente

O sistema SHALL fornecer método `Turn.add_thinking_entry()` para adicionar entradas ao ThinkingPanel durante o processo.

#### Scenario: Entrada de pensamento é adicionada
- **QUANDO** Sky inicia uma etapa de raciocínio
- **ENTÃO** `Turn.add_thinking_entry()` é chamado com o conteúdo
- **E** entrada aparece no ThinkingPanel com timestamp

#### Scenario: Entradas são renderizadas em ordem cronológica
- **QUANDO** múltiplas entradas são adicionadas
- **ENTÃO** ThinkingPanel mostra entradas em ordem de criação
- **E** entrada mais recente fica sempre visível (auto-scroll)

#### Scenario: Tipos diferentes de entrada têm estilos visuais distintos
- **QUANDO** entrada é do tipo "thought" (pensamento)
- **ENTÃO** texto é renderizado em itálico e cor muted
- **QUANDO** entrada é do tipo "tool_start" (ferramenta iniciada)
- **ENTÃO** nome da ferramenta é exibido em negrito com ícone 🔧
- **QUANDO** entrada é do tipo "tool_result" (resultado)
- **ENTÃO** resultado é exibido com ícone ✓ e cor success

---

### Requirement: ThinkingPanel é removido ou colapsado ao completar

O sistema SHALL remover ou colapsar o ThinkingPanel quando a resposta completa é recebida.

#### Scenario: ThinkingPanel é colapsado ao completar resposta
- **QUANDO** streaming de resposta é completado
- **ENTÃO** ThinkingPanel é colapsado automaticamente
- **E** usuário pode expandir para revisar o processo

#### Scenario: ThinkingPanel pode ser mantido expandido por preferência
- **QUANDO** usuário expandiu ThinkingPanel manualmente
- **ENTÃO** estado expandido é preservado entre respostas
- **E** preferência é salva na sessão

---

### Requirement: Widget ThinkingEntry representa unidade de pensamento

O sistema SHALL fornecer widget `ThinkingEntryWidget` para renderizar cada entrada do processo de pensamento.

#### Scenario: ThinkingEntryWidget mostra conteúdo formatado
- **QUANDO** ThinkingEntryWidget é criado
- **ENTÃO** exibe prefixo baseado no tipo (💭 para thought, 🔧 para tool, ✓ para result)
- **E** conteúdo da entrada é exibido após o prefixo
- **E** CSS class indica o tipo para estilização

#### Scenario: ThinkingEntryWidget suporta texto multiline
- **QUANDO** entrada de pensamento contém múltiplas linhas
- **ENTÃO** ThinkingEntryWidget renderiza todas as linhas
- **E** altura do widget se ajusta ao conteúdo

---

### Requirement: Indicação visual de processamento durante thinking

O sistema SHALL mostrar indicador visual de processamento enquanto Sky está pensando.

#### Scenario: Indicador aparece imediatamente após mensagem do usuário
- **QUANDO** usuário envia mensagem
- **ENTÃO** indicador de "pensando..." aparece na UI
- **E** indicador é substituído por ThinkingPanel quando primeiro pensamento chega

#### Scenario: Indicador é animado para dar feedback contínuo
- **QUANDO** sistema está aguardando resposta da Sky
- **ENTÃO** indicador mostra animação (spinner ou dots)
- **E** animação para quando resposta começa a chegar

---

### Requirement: Integração com stream de ferramentas

O sistema SHALL capturar e exibir eventos de ferramentas no ThinkingPanel durante streaming.

#### Scenario: Início de ferramenta é registrado
- **QUANDO** stream contém evento `content_block_start` com type `tool_use`
- **ENTÃO** entrada com nome da ferramenta e input é adicionada
- **E** entrada mostra status "executando..." enquanto ferramenta roda

#### Scenario: Resultado de ferramenta é registrado
- **QUANDO** stream contém evento `content_block_stop` após tool_use
- **ENTÃO** entrada com resultado da ferramenta é adicionada
- **E** resultado é truncado se muito longo (max 100 chars + "...")

---

> "O processo de pensamento é tão importante quanto o resultado" – made by Sky 🚀
