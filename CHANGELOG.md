# Changelog

Todas as alterações notáveis do Skybridge serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html/).


## [Pendente]


### ✨ Novidades


[**#28**](https://github.com/h4mn/skybridge/pull/28) - implementar integração GitHub → Trello com agentes autônomos

* [`fb9ffe7`](https://github.com/h4mn/skybridge/commit/fb9ffe7e1af1c85d6d832cb00ba218d44f4e04cf) **kanban:** implementar integração GitHub → Trello com agentes autônomos ([#28](https://github.com/h4mn/skybridge/pull/28)) [`@h4mn`](https://github.com/h4mn)
* [`48d3c9a`](https://github.com/h4mn/skybridge/commit/48d3c9a1204567b9fbf0015b691d5c51391a10d2) **kanban:** implementar contexto Kanban com integração Trello ([#28](https://github.com/h4mn/skybridge/pull/28)) [`@h4mn`](https://github.com/h4mn)


[**#33**](https://github.com/h4mn/skybridge/pull/33) - implementar FileBasedJobQueue standalone + observabilidade

* [`c46da09`](https://github.com/h4mn/skybridge/commit/c46da096640437e0a430e60ce5b46e17c063df30) **queue:** implementar FileBasedJobQueue standalone + observabilidade ([#33](https://github.com/h4mn/skybridge/pull/33)) [`@h4mn`](https://github.com/h4mn)


[**#49**](https://github.com/h4mn/skybridge/pull/49) - implementar sincronização de labels e corrigir handlers asyn...

* [`93b8517`](https://github.com/h4mn/skybridge/commit/93b8517a7b007a81f0a70f8801264b6239d2fe1c) **webhooks:** implementar sincronização de labels e corrigir handlers async ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)
* [`7534cd9`](https://github.com/h4mn/skybridge/commit/7534cd99102373ff276b95b07efc8921470488dc) **webhooks:** sincronização de labels GitHub→Trello e correção de handlers ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)
* [`3daab9f`](https://github.com/h4mn/skybridge/commit/3daab9fdaae09087d60c6464b8566f5a2982d3c1) **runtime:** implementar Demo Engine com CLI e integração com Snapshot ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)
* [`33f47a0`](https://github.com/h4mn/skybridge/commit/33f47a08b6967a9f78000986cc561015ab3d30c4) **webhooks:** configurar branch base para worktrees de agentes ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)
* [`195412c`](https://github.com/h4mn/skybridge/commit/195412ccabab9268d827646e1445d3cc0cce3130) **queue:** implementar FileBasedJobQueue standalone + observabilidade ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)

* [`93468f5`](https://github.com/h4mn/skybridge/commit/93468f5b2508b9b0de79a9f52fa65e6893374dc8) **ci:** implementar gerador de changelog Sky com Python [`@h4mn`](https://github.com/h4mn)

[**#25**](https://github.com/h4mn/skybridge/pull/25) - implementar idempotência completa com correlation ID

* [`9260458`](https://github.com/h4mn/skybridge/commit/9260458df722f8f7e4c49727a5cd0f36592536ec) **webhooks:** implementar idempotência completa com correlation ID ([#25](https://github.com/h4mn/skybridge/pull/25)) [`@h4mn`](https://github.com/h4mn)


[**#40**](https://github.com/h4mn/skybridge/pull/40) - configurar branch base para worktrees de agentes

* [`3c29179`](https://github.com/h4mn/skybridge/commit/3c2917974449fbdaf542de120c86f8cceb209826) **webhooks:** configurar branch base para worktrees de agentes ([#40](https://github.com/h4mn/skybridge/pull/40)) [`@h4mn`](https://github.com/h4mn)



### 🐛 Correções

* [`e53d93b`](https://github.com/h4mn/skybridge/commit/e53d93bd32f9952307da0c79d256ec126dc98c40) **build:** remover configuração Poetry do pyproject.toml [`@h4mn`](https://github.com/h4mn)

[**#49**](https://github.com/h4mn/skybridge/pull/49) - implementar exists_by_delivery no FileBasedJobQueue

* [`84dbb0e`](https://github.com/h4mn/skybridge/commit/84dbb0e6df865bf664d7b981c96cb29d90479e98) **queue:** implementar exists_by_delivery no FileBasedJobQueue ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)


[**#30**](https://github.com/h4mn/skybridge/pull/30) - implementar deduplicação usando X-GitHub-Delivery #30

* [`4a1b106`](https://github.com/h4mn/skybridge/commit/4a1b10676407899c5c82fe248e45b5c75902987e) **webhooks:** implementar deduplicação usando X-GitHub-Delivery #30 ([#30](https://github.com/h4mn/skybridge/pull/30)) [`@h4mn`](https://github.com/h4mn)



### ♻️ Refatoração


[**#30**](https://github.com/h4mn/skybridge/pull/30) - renomear Mock→Fake e implementar deduplicação #30

* [`d949bd2`](https://github.com/h4mn/skybridge/commit/d949bd246e17769580f12bbd59b55befffae6771) **webhooks:** renomear Mock→Fake e implementar deduplicação #30 ([#30](https://github.com/h4mn/skybridge/pull/30)) [`@h4mn`](https://github.com/h4mn)


[**#28**](https://github.com/h4mn/skybridge/pull/28) - migrar estrutura para simplificar imports

* [`a49c3e5`](https://github.com/h4mn/skybridge/commit/a49c3e586a357ca27a95c4577a1223db163fc639) migrar estrutura para simplificar imports ([#28](https://github.com/h4mn/skybridge/pull/28)) [`@h4mn`](https://github.com/h4mn)
* [`2d313ec`](https://github.com/h4mn/skybridge/commit/2d313ec71aa48826030d8a4a91a03532f759bc8e) **namespace:** integração GitHub → Trello com agentes autônomos ([#28](https://github.com/h4mn/skybridge/pull/28)) [`@h4mn`](https://github.com/h4mn)



### 📚 Documentação

* [`d4d4322`](https://github.com/h4mn/skybridge/commit/d4d4322c6eb052b35df79f077e9c972a9ea0839b) **config:** adicionar memória do projeto e reorganizar .env.example [`@h4mn`](https://github.com/h4mn)

[**#49**](https://github.com/h4mn/skybridge/pull/49) - documentar idempotência e correlation ID

* [`9a09d9b`](https://github.com/h4mn/skybridge/commit/9a09d9b5aa394b248083b7f9f3c713a7ed87499d) **webhooks:** documentar idempotência e correlation ID ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)
* [`0a58ec4`](https://github.com/h4mn/skybridge/commit/0a58ec40306401098abc1503cc7f7a752bf6f187) adicionar levantamento completo do fluxo GitHub → Trello ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)


[**#28**](https://github.com/h4mn/skybridge/pull/28) - documentar simplificação da estrutura src/

* [`042dfdb`](https://github.com/h4mn/skybridge/commit/042dfdbce5e4c6ade7e8f607aa7ed43bca504336) **adr:** documentar simplificação da estrutura src/ ([#28](https://github.com/h4mn/skybridge/pull/28)) [`@h4mn`](https://github.com/h4mn)



### ✅ Testes


[**#49**](https://github.com/h4mn/skybridge/pull/49) - corrigir imports e patches após refactoring

* [`fdce64f`](https://github.com/h4mn/skybridge/commit/fdce64fd21715a3258637dadc81474e67712fea8) corrigir imports e patches após refactoring ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)



### 🧹 Tarefas

* [`d3b20a5`](https://github.com/h4mn/skybridge/commit/d3b20a50c7a365cbe42553fc5d85f387a3776230) **sync:** sincronizar dev com main (v0.5.4) [`@h4mn`](https://github.com/h4mn)
* [`837c212`](https://github.com/h4mn/skybridge/commit/837c212044fca9728411e29cc793cb08c87898fd) **sync:** sincronizar dev com main (semantic-release configurado) [`@h4mn`](https://github.com/h4mn)


## [0.5.4] - 2026-01-19


### 🐛 Correções

* [`c7bc2d0`](https://github.com/h4mn/skybridge/commit/c7bc2d0b5042642b84e452cf1c4cfb8030e4e4dc) **build:** remover configuração Poetry do pyproject.toml [`@h4mn`](https://github.com/h4mn)


### 📚 Documentação

* [`387396b`](https://github.com/h4mn/skybridge/commit/387396bb57311f1ade21a195fb1b97f6cb54c10d) adicionar relatório de comparação de execução de agentes [`@h4mn`](https://github.com/h4mn)


## [0.5.2] - 2026-01-12


### 🐛 Correções


[**#18**](https://github.com/h4mn/skybridge/pull/18) - corrigir inconsistências na documentação e criar skill resol...

* [`5ef59fe`](https://github.com/h4mn/skybridge/commit/5ef59fe031843138d9f49b402539b2f3a15db3fb) corrigir inconsistências na documentação e criar skill resolve-issue ([#18](https://github.com/h4mn/skybridge/pull/18)) [`@h4mn`](https://github.com/h4mn)
* [`5828a25`](https://github.com/h4mn/skybridge/commit/5828a25bff41871064f8a6ffef6e2adef53fddc1) **docs:** corrigir inconsistências na documentação e criar skill resolve-issue ([#18](https://github.com/h4mn/skybridge/pull/18)) [`@h4mn`](https://github.com/h4mn)



### 🧹 Tarefas


[**#18**](https://github.com/h4mn/skybridge/pull/18) - adicionar arquivos temporários do opencode ao .gitignore

* [`db5b11c`](https://github.com/h4mn/skybridge/commit/db5b11cda33fd31e40c06fc2a60012f9a2aab355) adicionar arquivos temporários do opencode ao .gitignore ([#18](https://github.com/h4mn/skybridge/pull/18)) [`@h4mn`](https://github.com/h4mn)


[**#15**](https://github.com/h4mn/skybridge/pull/15) - remover .agents/ e settings.local.json do versionamento

* [`6eadf43`](https://github.com/h4mn/skybridge/commit/6eadf4356eec4fd1d656e73808af566dcdd17d39) remover .agents/ e settings.local.json do versionamento ([#15](https://github.com/h4mn/skybridge/pull/15)) [`@h4mn`](https://github.com/h4mn)
* [`57d85b6`](https://github.com/h4mn/skybridge/commit/57d85b61de44e46d129d78c51299eeaa5b355f6e) remover .agents/ e settings.local.json do versionamento ([#15](https://github.com/h4mn/skybridge/pull/15)) [`@h4mn`](https://github.com/h4mn)



## [0.5.1] - 2026-01-12


### 🐛 Correções


[**#13**](https://github.com/h4mn/skybridge/pull/13) - adicionar fi faltante no step Update SPEC versions

* [`c563873`](https://github.com/h4mn/skybridge/commit/c563873e6ba66b1ea8efafe4fef031d0990d084b) **docs/workflow:** adicionar fi faltante no step Update SPEC versions ([#13](https://github.com/h4mn/skybridge/pull/13)) [`@h4mn`](https://github.com/h4mn)
* [`b86b620`](https://github.com/h4mn/skybridge/commit/b86b620ee7b8e2119089412f6cea93e74d55bf09) **ci/pages:** converter index.md para index.html para resolver 404 ([#13](https://github.com/h4mn/skybridge/pull/13)) [`@h4mn`](https://github.com/h4mn)
* [`5a74375`](https://github.com/h4mn/skybridge/commit/5a743755443bf85d5e17405672319d9d3049d125) **ci/pages:** converter index.md para index.html para resolver 404 ([#13](https://github.com/h4mn/skybridge/pull/13)) [`@h4mn`](https://github.com/h4mn)



## [0.5.0] - 2026-01-11


### ✨ Novidades

* [`f2727a0`](https://github.com/h4mn/skybridge/commit/f2727a0b2f0e6e25cbcd81294166f37f0f41c397) **webhooks:** integração com plataforma Skybridge [`@h4mn`](https://github.com/h4mn)
* [`5f2f968`](https://github.com/h4mn/skybridge/commit/5f2f968d965c239c3b72de1e4003065e349451bb) **snapshot:** GitExtractor + scripts + ADR015/017 [`@h4mn`](https://github.com/h4mn)
* [`1479b36`](https://github.com/h4mn/skybridge/commit/1479b36f91132c9e657e8f759ebdd4f3b4151223) **webhooks:** sistema de agentes autônomos (PRD013) [`@h4mn`](https://github.com/h4mn)
* [`0c183e2`](https://github.com/h4mn/skybridge/commit/0c183e246f9320a25a3f33c1d3b401c74ed5e282) **agent-interface:** SPEC008 + infra de agentes [`@h4mn`](https://github.com/h4mn)


### 🐛 Correções


[**#8**](https://github.com/h4mn/skybridge/pull/8) - adicionar fi faltante no step Update SPEC versions

* [`c563873`](https://github.com/h4mn/skybridge/commit/c563873e6ba66b1ea8efafe4fef031d0990d084b) **docs/workflow:** adicionar fi faltante no step Update SPEC versions ([#8](https://github.com/h4mn/skybridge/pull/8)) [`@h4mn`](https://github.com/h4mn)
* [`24d1961`](https://github.com/h4mn/skybridge/commit/24d1961608730f51150de64653875696efad6343) **docs/workflow:** adicionar fi faltante no step Update SPEC versions ([#8](https://github.com/h4mn/skybridge/pull/8)) [`@h4mn`](https://github.com/h4mn)

* [`6542630`](https://github.com/h4mn/skybridge/commit/654263082bc8d8dd1d4defbc50228f24ffb979e7) **release:** corrige line endings do arquivo VERSION [`@h4mn`](https://github.com/h4mn)


### 📚 Documentação

* [`f2e5688`](https://github.com/h4mn/skybridge/commit/f2e5688a02874154fff02f5c3013d53988adac8a) **webhooks:** relatórios, PRD014, testes, config, ADR018 [`@h4mn`](https://github.com/h4mn)
* [`f13988c`](https://github.com/h4mn/skybridge/commit/f13988c6337d5b9e2d50db5f83d710a0c8fb0986) **webhooks:** limpeza de documentos duplicados [`@h4mn`](https://github.com/h4mn)
* [`a254128`](https://github.com/h4mn/skybridge/commit/a254128700614871deed81038a273120db1178ef) adiciona PRD e estudo sobre webhook autonomous agents [`@h4mn`](https://github.com/h4mn)
* [`1aeaf77`](https://github.com/h4mn/skybridge/commit/1aeaf776b1a3900f35cd8f6443f99ac9f7584a20) **versioning:** estudo sobre padrões profissionais de versionamento [`@h4mn`](https://github.com/h4mn)


### 🧹 Tarefas

* [`5737aca`](https://github.com/h4mn/skybridge/commit/5737aca51ab0b0f7e4718847287bdd4e82b5ea2f) **git:** remove node_modules do versionamento e atualiza .gitignore [`@h4mn`](https://github.com/h4mn)


## [0.4.0] - 2026-01-11


### ✨ Novidades


[**#6**](https://github.com/h4mn/skybridge/pull/6) - Webhook Autonomous Agents + Snapshot Service + AI Agent Inte...

* [`f7756cd`](https://github.com/h4mn/skybridge/commit/f7756cd9b99cc8e09d5f7e633b5ff7ba71727e46) Webhook Autonomous Agents + Snapshot Service + AI Agent Interface (v0.3.0) ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`f2727a0`](https://github.com/h4mn/skybridge/commit/f2727a0b2f0e6e25cbcd81294166f37f0f41c397) **webhooks:** integração com plataforma Skybridge ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`5f2f968`](https://github.com/h4mn/skybridge/commit/5f2f968d965c239c3b72de1e4003065e349451bb) **snapshot:** GitExtractor + scripts + ADR015/017 ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`1479b36`](https://github.com/h4mn/skybridge/commit/1479b36f91132c9e657e8f759ebdd4f3b4151223) **webhooks:** sistema de agentes autônomos (PRD013) ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`0c183e2`](https://github.com/h4mn/skybridge/commit/0c183e246f9320a25a3f33c1d3b401c74ed5e282) **agent-interface:** SPEC008 + infra de agentes ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)



### 📚 Documentação


[**#6**](https://github.com/h4mn/skybridge/pull/6) - relatórios, PRD014, testes, config, ADR018

* [`f2e5688`](https://github.com/h4mn/skybridge/commit/f2e5688a02874154fff02f5c3013d53988adac8a) **webhooks:** relatórios, PRD014, testes, config, ADR018 ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`f13988c`](https://github.com/h4mn/skybridge/commit/f13988c6337d5b9e2d50db5f83d710a0c8fb0986) **webhooks:** limpeza de documentos duplicados ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`a254128`](https://github.com/h4mn/skybridge/commit/a254128700614871deed81038a273120db1178ef) adiciona PRD e estudo sobre webhook autonomous agents ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`1aeaf77`](https://github.com/h4mn/skybridge/commit/1aeaf776b1a3900f35cd8f6443f99ac9f7584a20) **versioning:** estudo sobre padrões profissionais de versionamento ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)



### 🧹 Tarefas


[**#6**](https://github.com/h4mn/skybridge/pull/6) - remove node_modules do versionamento e atualiza .gitignore

* [`5737aca`](https://github.com/h4mn/skybridge/commit/5737aca51ab0b0f7e4718847287bdd4e82b5ea2f) **git:** remove node_modules do versionamento e atualiza .gitignore ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)
* [`37ac3cd`](https://github.com/h4mn/skybridge/commit/37ac3cd30755872052e1211ec8cefeabfedf3e5f) **release:** bump versão para 0.3.0 ([#6](https://github.com/h4mn/skybridge/pull/6)) [`@h4mn`](https://github.com/h4mn)



## [0.2.5] - 2026-01-08


### 🐛 Correções

* [`495358b`](https://github.com/h4mn/skybridge/commit/495358bd7348acc44fb4f712d87c96fcf51c1c59) alinhar versões da CLI e API com ADR012 [`@h4mn`](https://github.com/h4mn)


### ♻️ Refatoração

* [`ca1044a`](https://github.com/h4mn/skybridge/commit/ca1044a7fbd218e5bbbb459e940d5cded55afc59) **i18n:** align changelog to english for consistency [`@h4mn`](https://github.com/h4mn)


## [0.2.4] - 2026-01-07


### 🐛 Correções

* [`fc8eb95`](https://github.com/h4mn/skybridge/commit/fc8eb9503b002d71fa00283847ee4c4861acb0fd) **ci:** capture grep output in variable before writing to file [`@h4mn`](https://github.com/h4mn)


## [0.2.3] - 2026-01-07


### 🐛 Correções

* [`e48ef0d`](https://github.com/h4mn/skybridge/commit/e48ef0dae0c8d84d167f13191021476df7932d3f) **ci:** simplify changelog regex to basic string matching [`@h4mn`](https://github.com/h4mn)


## [0.2.2] - 2026-01-07


### 🐛 Correções

* [`fda65ca`](https://github.com/h4mn/skybridge/commit/fda65ca7643db45072fb18ffa4c4420b1d44bfb4) **ci:** escape regex pattern properly for changelog [`@h4mn`](https://github.com/h4mn)


## [0.2.1] - 2026-01-07


### 🐛 Correções

* [`7356957`](https://github.com/h4mn/skybridge/commit/7356957bc83008706825329f381316bfec18c38a) **ci:** improve changelog generation with better regex [`@h4mn`](https://github.com/h4mn)


## [0.2.0] - 2026-01-07


### ✨ Novidades

* [`eda6842`](https://github.com/h4mn/skybridge/commit/eda6842841e63f8583a9bf5a023df784c416bf45) implement single source of truth for versioning (ADR012) [`@h4mn`](https://github.com/h4mn)
* [`592201d`](https://github.com/h4mn/skybridge/commit/592201d56e47fe5f9c7818c63b69b949e02d753f) **config:** implement conventional commits with commitlint and husky [`@h4mn`](https://github.com/h4mn)
* [`1215572`](https://github.com/h4mn/skybridge/commit/1215572eb9dc56a489293c0ba8819288f1c20914) **release:** add initial changelog for automated versioning [`@h4mn`](https://github.com/h4mn)
* [`0a81861`](https://github.com/h4mn/skybridge/commit/0a818613553a0adaa5d40fb31b57228202cfeeb5) **ci:** add github workflows for release and docs automation [`@h4mn`](https://github.com/h4mn)


### 🐛 Correções

* [`b2cbeba`](https://github.com/h4mn/skybridge/commit/b2cbeba2de0c958cfae5c7150f1427ae108bba4a) **ci:** correct commit type detection in release workflow [`@h4mn`](https://github.com/h4mn)
* [`458f06a`](https://github.com/h4mn/skybridge/commit/458f06a8078bc9809a2610fca665396883f6616c) **ci:** handle first release and missing directories in workflows [`@h4mn`](https://github.com/h4mn)


### 🧹 Tarefas

* [`95db6d0`](https://github.com/h4mn/skybridge/commit/95db6d0ad14afb7f2e18eee140920d43ca581585) initial commit - skybridge v0.1.0 [`@h4mn`](https://github.com/h4mn)


---

## Referências

- **Versão atual:** ver `src/version.py`
- **Semantic Versioning:** https://semver.org/
- **Keep a Changelog:** https://keepachangelog.com/pt-BR/1.0.0/

> "A disciplina dos changelogs é o respeito ao tempo de quem os lê" – made by Sky 📚
