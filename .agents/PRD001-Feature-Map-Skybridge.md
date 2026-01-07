# PRD001 - Mapa de Funcionalidades da Skybridge

## 1. Objetivo
Com base no discovery, mapear e comparar as funcionalidades presentes em cada entidade Skybridge para orientar unificacao, dominios e estrategia.

## 2. Problema
O discovery indica onde estao as entidades, mas nao descreve o que cada uma faz. Sem esse mapa funcional, a unificacao vira tentativa e erro.

## 3. Escopo
### Dentro do escopo
- Inventario de features por entidade.
- Classificacao contra o nucleo provavel.
- Extracao de padroes e preferencias.
- Preparacao de mapa de dominios/infras e possiveis blueprints.
- Estrutura inicial para strategy ladder.

### Fora do escopo
- Refatoracao e consolidacao de codigo.
- Decisao final de arquitetura.
- Implementacao de novas features.

## 4. Usuarios / Stakeholders
- Autor do projeto Skybridge.
- Agentes IA (Codex).
- Time futuro.

## 5. Requisitos
### Funcionais
- Gerar `features-report.md` com campos: item, local, o que faz, proposito unificado, como agrega, valor (score).
- Inventariar por entidade e ordenar por score.
- Classificar cada entidade contra o nucleo.
- Listar padroes e preferencias (CLI, API, orquestracao, integracoes).
- Indicar dominios e infras potenciais.
- Sugerir blueprints candidatos.

### Nao funcionais
- Evidencias auditaveis (paths e trechos curtos).
- Baixo ruido (foco no top score).
- Formato legivel e reutilizavel.

## 6. Criterios de sucesso
- Features inventariadas por entidade com evidencia clara.
- Comparacao objetiva contra o nucleo.
- Padroes e preferencias destacados.
- Mapa inicial de dominios/infras e blueprints propostos.

## 7. Dependencias e restricoes
- Relatorio `task000-discovery-report.md`.
- Acesso leitura a README/configs/codigo minimo.

## 8. Entregaveis
- `features-report.md`.
- Tabela de comparacao por entidade.
- Sumario de padroes, dominios e blueprints.

## 9. Proximos passos
- Executar playbook.
- Validar com o dono do projeto.
- Abrir ADR para unificacao quando necessario.

---
> "Funcionalidade clara guia a unificacao." - made by Sky
