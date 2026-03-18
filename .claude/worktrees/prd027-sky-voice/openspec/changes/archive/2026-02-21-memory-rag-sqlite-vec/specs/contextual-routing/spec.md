# Especificação: Roteamento Contextual

Roteia queries para coleção apropriada baseado em intenção.

## Requisitos ADICIONADOS

### Requisito: Detecção de intenção
O sistema DEVE detectar a intenção do usuário e rotear a query para a coleção apropriada.

#### Cenário: Query de identidade roteia para coleção identity
- **QUANDO** o usuário pergunta "quem é você?" ou "o que você sabe?"
- **ENTÃO** a query é roteada para coleção "identity"
- **E** os resultados descrevem a identidade da Sky

#### Cenário: Query de ensinamento roteia para coleção teachings
- **QUANDO** o usuário pergunta "o que papai me ensinou?"
- **ENTÃO** a query é roteada para coleção "teachings"
- **E** os resultados listam os ensinamentos do pai

#### Cenário: Query de memória roteia para coleção shared-moments
- **QUANDO** o usuário pergunta "lembre da vez que..." ou "nosso momento..."
- **ENTÃO** a query é roteada para coleção "shared-moments"
- **E** os resultados recuperam memórias afetivas

#### Cenário: Query operacional roteia para coleção operational
- **QUANDO** o usuário pergunta "o que aconteceu hoje?" ou "o que está fazendo?"
- **ENTÃO** a query é roteada para coleção "operational"
- **E** os resultados mostram contexto recente

### Requisito: Fallback para todas as coleções
O sistema DEVE buscar todas as coleções quando a intenção não é clara.

#### Cenário: Query ambígua busca em toda parte
- **QUANDO** a query do usuário não corresponde a intenções conhecidas
- **ENTÃO** o sistema busca todas as coleções
- **E** os resultados são fundidos e classificados por relevância global
