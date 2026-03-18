# Especificação: Hierarquia de Memória

Memória de curto/longo prazo com diferentes estratégias de retenção.

## Requisitos ADICIONADOS

### Requisito: Múltiplas coleções de memória
O sistema DEVE organizar memórias em coleções especializadas por propósito e política de retenção.

#### Cenário: Coleção identity é permanente
- **QUANDO** Sky aprende sobre sua identidade
- **ENTÃO** a memória é armazenada na coleção "identity"
- **E** a política de retenção é "permanent" (nunca expira)

#### Cenário: Coleção operational expira após 30 dias
- **QUANDO** Sky aprende contexto operacional (ex: "usuário está codando agora")
- **ENTÃO** a memória é armazenada na coleção "operational"
- **E** a política de retenção é 30 dias
- **E** memórias expiradas são removidas automaticamente

#### Cenário: Coleção shared-moments armazena memórias afetivas
- **QUANDO** Sky compartilha um momento significativo com o usuário
- **ENTÃO** a memória é armazenada na coleção "shared-moments"
- **E** a memória é marcada com peso afetivo (alto/médio/baixo)

### Requisito: Políticas de retenção específicas por coleção
O sistema DEVE aplicar diferentes políticas de retenção por coleção.

| Coleção | Retenção | Propósito |
|---------|----------|-----------|
| identity | permanente | Quem Sky é |
| shared-moments | permanente | Memórias afetivas |
| teachings | permanente | Ensinamentos do pai |
| operational | 30 dias | Contexto recente |

#### Cenário: Remoção automática
- **QUANDO** o sistema realiza manutenção (diariamente)
- **ENTÃO** memórias operacionais mais antigas que 30 dias são deletadas
- **E** coleções permanentes nunca são removidas

### Requisito: Score de importância da memória
O sistema DEVE atribuir scores de importância às memórias baseado na frequência de acesso.

#### Cenário: Memórias acessadas frequentemente ganham score maior
- **QUANDO** uma memória é recuperada múltiplas vezes
- **ENTÃO** seu score de importância aumenta
- **E** memórias com score alto são classificadas mais alto em resultados de busca
