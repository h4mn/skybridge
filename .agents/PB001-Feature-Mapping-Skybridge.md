# PLAYBOOK PB001 - Feature Mapping da Skybridge

## 0) Propósito
Transformar o discovery em um mapa funcional comparável entre entidades.

## 1) Entradas
- `task001-discovery-report.md`
- README*, pyproject.toml, configs relevantes, e código mínimo para evidenciar features.

## 2) Escopo de leitura
- Ler README* e configs antes do código.
- Código apenas para confirmar comportamento.
- Priorizar top scores.

## 3) Passos
1) Selecionar entidades por score.
2) Para cada entidade, listar features candidatas.
3) Para cada feature, registrar: item, local, o que faz, propósito unificado, como agrega, score.
4) Classificar entidade vs núcleo (forte, parcial, fraca).
5) Extrair padrões/preferências (estrutura de pastas, CLI/API, integrações).
6) Mapear domínios/infras potenciais.
7) Propor blueprints candidatos (ex.: CLI-first, API-first, Agent-core).
8) Preparar base para strategy ladder (capabilities -> platform -> leverage).

## 4) Saídas
- `features-report.md` preenchido.
- Seção de padrões e preferências.
- Seção de domínios/infras e blueprints.

## 5) DoD
- Features por entidade com evidência.
- Ranking e classificação vs núcleo.
- Padrões e domínios documentados.
- Blueprints propostos.

---
> "Entender antes de unificar." - made by Sky
