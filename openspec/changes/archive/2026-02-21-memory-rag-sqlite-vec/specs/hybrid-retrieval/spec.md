# Especificação: Recuperação Híbrida

Combina busca vetorial (semântica) com keyword (exata).

## Requisitos ADICIONADOS

### Requisito: Busca combinada vetorial + keyword
O sistema DEVE combinar busca semântica vetorial com filtro keyword para resultados ótimos.

#### Cenário: Busca semântica encontra conceitos relacionados
- **QUANDO** o usuário busca "medo de falhar"
- **ENTÃO** o sistema retorna memórias sobre "ansiedade", "insegurança", "dúvida"
- **E** resultados são classificados por similaridade semântica

#### Cenário: Filtro keyword reduz ruído
- **QUANDO** a busca semântica retorna muitos resultados de baixa relevância
- **ENTÃO** o sistema aplica filtro keyword para remover mismatches óbvios
- **E** apenas resultados acima do threshold de relevância (0.7) são retornados

### Requisito: Re-ranqueamento por recência
O sistema DEVE re-ranquear resultados de busca combinando score de relevância com recência.

#### Cenário: Memórias recentes ganham boost
- **QUANDO** múltiplas memórias têm scores semânticos similares
- **ENTÃO** memórias mais recentes são classificadas mais alto
- **E** score final = 0.7 * score_semântico + 0.3 * score_recência

### Requisito: Deduplicação
O sistema DEVE deduplicar memórias similares nos resultados de busca.

#### Cenário: Memórias duplicadas são fundidas
- **QUANDO** a busca retorna duas memórias com >0.95 de similaridade
- **ENTÃO** o sistema retorna apenas a mais recente
- **E** nota que duplicata foi fundida
