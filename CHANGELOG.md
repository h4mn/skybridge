# Changelog

Todas as alterações notáveis do Skybridge serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html/).






## [0.11.0] - 2026-01-25


### ✨ Novidades

* [`fb1ed51`](https://github.com/h4mn/skybridge/commit/fb1ed519298932cbc1d6dd0c1738eb887145355a) **pl001:** migrar versionamento para git tags via setuptools_scm [`@h4mn`](https://github.com/h4mn)
* [`95c3772`](https://github.com/h4mn/skybridge/commit/95c37726b68f5d4333d7e55fba5bbfef0cb71d19) **webhooks:** implementar sistema de snapshots para worktrees [`@h4mn`](https://github.com/h4mn)
* [`9564ec6`](https://github.com/h4mn/skybridge/commit/9564ec6a0cfe747f43b0630204a0c077288c1496) **webui:** adicionar proteção de senha para deleção de worktrees [`@h4mn`](https://github.com/h4mn)
* [`77cf21c`](https://github.com/h4mn/skybridge/commit/77cf21c916e765e3acd3c48ce663c5d49d93fdb9) **quality:** adicionar infraestrutura de qualidade e SPEC009 demo [`@h4mn`](https://github.com/h4mn)
* [`220e101`](https://github.com/h4mn/skybridge/commit/220e101e989e907f59f9cba0c676b056b7130877) **webui:** adicionar prefixo /api nas rotas para compatibilidade com WebUI [`@h4mn`](https://github.com/h4mn)
* [`19cd0dc`](https://github.com/h4mn/skybridge/commit/19cd0dc01924821a11091173080aabba2b6117ba) **pl001:** concluir fases 4-5 da migração de versionamento [`@h4mn`](https://github.com/h4mn)
* [`0d146ac`](https://github.com/h4mn/skybridge/commit/0d146acf21b3cf9a5224e489fd2532590c82026e) **webui:** implementar sistema de logs com streaming real-time [`@h4mn`](https://github.com/h4mn)


### 🐛 Correções

* [`b8f17cc`](https://github.com/h4mn/skybridge/commit/b8f17cc021cdc8594252ed17e96df4d191473811) **quality:** corrigir imports e configurar pre-commit Python [`@h4mn`](https://github.com/h4mn)
* [`93f8c4d`](https://github.com/h4mn/skybridge/commit/93f8c4d7869991912f9c46a71617534b83d2cef4) **release:** corrigir execução do changelog no workflow [`@h4mn`](https://github.com/h4mn)
* [`1e907a6`](https://github.com/h4mn/skybridge/commit/1e907a60798a658e2e96a54fcb1e66491090ced9) **release:** adicionar __init__.py para tornar runtime um pacote Python [`@h4mn`](https://github.com/h4mn)
* [`18f682b`](https://github.com/h4mn/skybridge/commit/18f682bf9438e4c097776c2b84339911907dbf61) **release:** não falhar quando não há mudanças no CHANGELOG [`@h4mn`](https://github.com/h4mn)


### ♻️ Refatoração

* [`950f5cd`](https://github.com/h4mn/skybridge/commit/950f5cd52b931473d0d76cd47e3140dae7b4efe5) **skills:** traduzir frontmatters para Português Brasileiro (ADR018) [`@h4mn`](https://github.com/h4mn)
* [`8a97d7b`](https://github.com/h4mn/skybridge/commit/8a97d7be37c3c5c6d850e3e30f7d6c753cabf272) **runtime:** traduzir system prompt para Português Brasileiro (ADR018) [`@h4mn`](https://github.com/h4mn)
* [`2951297`](https://github.com/h4mn/skybridge/commit/29512972ff5c00926077b9fc0c20c22808cb307d) **runtime:** reorganizar prompts e skills para estrutura src/runtime/prompts (PRD021) [`@h4mn`](https://github.com/h4mn)


### 📚 Documentação

* [`d5ed9a1`](https://github.com/h4mn/skybridge/commit/d5ed9a1cb78fb4d8d997d5e99d97fb6a269f898c) corrigir inconsistências identificadas no relatório consolidado [`@h4mn`](https://github.com/h4mn)
* [`9d4ebae`](https://github.com/h4mn/skybridge/commit/9d4ebaeb83b4851e64d6545269240b935636d5f0) **prd014:** adicionar gap analysis de documentação vs implementação [`@h4mn`](https://github.com/h4mn)


### ✅ Testes

* [`e8b4c9c`](https://github.com/h4mn/skybridge/commit/e8b4c9c5bd9f8c4ebc0af7144bd6fae8ecc2622d) pre-commit [`@h4mn`](https://github.com/h4mn)
* [`d873be5`](https://github.com/h4mn/skybridge/commit/d873be566eed2d4401be9de888d40c6dcf418758) hook [`@h4mn`](https://github.com/h4mn)

## [0.10.0] - 2026-01-25


### ✨ Novidades

* [`efb73ef`](https://github.com/h4mn/skybridge/commit/efb73ef8641c8eabff403e7f98d24f72dadb18d9) **core:** PRD018 Fase 3 - Guardrails (Validações Pré-Commit) [`@h4mn`](https://github.com/h4mn)
* [`cec6652`](https://github.com/h4mn/skybridge/commit/cec6652bc33b1e2ed784d93ef5abffb3f2876cca) **infra:** PRD018 Fase 3 - Domain Event Listeners [`@h4mn`](https://github.com/h4mn)
* [`c73d895`](https://github.com/h4mn/skybridge/commit/c73d8954e095791463a5518b9d9bf48981ca9214) **infra:** PRD018 Fase 2 - Job Queue Adapters com Factory Pattern [`@h4mn`](https://github.com/h4mn)
* [`c34edb5`](https://github.com/h4mn/skybridge/commit/c34edb553e95cd9eb6b8c02d8829f7003aff300f) **core:** PRD018 Fase 3 - CommitMessageGenerator [`@h4mn`](https://github.com/h4mn)
* [`bd58da2`](https://github.com/h4mn/skybridge/commit/bd58da2f57051f79db537ca127b7d9fb42755798) **demo:** adicionar demos Agent SDK para PRD019 [`@h4mn`](https://github.com/h4mn)
* [`afd5b4a`](https://github.com/h4mn/skybridge/commit/afd5b4a4872ae42e6066283cf3ba3cc0159f6530) **prd020:** implementar fluxo bidirecional Trello → GitHub [`@h4mn`](https://github.com/h4mn)
* [`ac43145`](https://github.com/h4mn/skybridge/commit/ac431457eed200656373dbe0782f793fd9f6ad18) **infra:** PRD018 Fase 3 - GitHub API Client [`@h4mn`](https://github.com/h4mn)
* [`a07cee3`](https://github.com/h4mn/skybridge/commit/a07cee38c0bd7ff0ff517d2dc64fde38a6c874b0) **core:** PRD018 Fase 3 - Domain Events System (Core) [`@h4mn`](https://github.com/h4mn)
* [`989c07e`](https://github.com/h4mn/skybridge/commit/989c07e6550f7e14f887a85bcd90183f3fcb7b00) **prd020:** implementar verificação HMAC-SHA1 do Trello + conftest load_dotenv [`@h4mn`](https://github.com/h4mn)
* [`93468f5`](https://github.com/h4mn/skybridge/commit/93468f5b2508b9b0de79a9f52fa65e6893374dc8) **ci:** implementar gerador de changelog Sky com Python [`@h4mn`](https://github.com/h4mn)
* [`50e0900`](https://github.com/h4mn/skybridge/commit/50e09005375d4813d717ce5e3b4ed5e90cc065eb) **core:** PRD018 Fase 3 - JobOrchestrator com Autonomia 70% [`@h4mn`](https://github.com/h4mn)
* [`3d99690`](https://github.com/h4mn/skybridge/commit/3d996904cc2f78076c5cf2ace449ca0d537cd1db) **infra:** PRD018 Fase 3 - InMemoryEventBus Implementation [`@h4mn`](https://github.com/h4mn)
* [`2b06e14`](https://github.com/h4mn/skybridge/commit/2b06e14f8c766f257eb70788e564ecf312bbc648) **ci:** implementar gerador de changelog Sky com Python [`@h4mn`](https://github.com/h4mn)
* [`283be38`](https://github.com/h4mn/skybridge/commit/283be3809076404d38bba677247931fa8e46c4b0) **runtime:** HEAD method para Trello e atualiza bootstrap [`@h4mn`](https://github.com/h4mn)
* [`17967d4`](https://github.com/h4mn/skybridge/commit/17967d4d168cbdb040aba87f1ed1cc566c642992) **core:** PRD018 Fase 3 - GitService (Operações Git Abstratas) [`@h4mn`](https://github.com/h4mn)
* [`0e9ae6b`](https://github.com/h4mn/skybridge/commit/0e9ae6bcba0e236e2927824769f042cc5e666602) **prd019:** implementar ClaudeSDKAdapter com feature flag [`@h4mn`](https://github.com/h4mn)
* [`09ad406`](https://github.com/h4mn/skybridge/commit/09ad40637fefb8ced3ff47031dfa695d5983a891) **ci:** habilitar modo detalhado no changelog do release [`@h4mn`](https://github.com/h4mn)

[**#33**](https://github.com/h4mn/skybridge/pull/33) - implementar FileBasedJobQueue standalone + observabilidade

* [`c46da09`](https://github.com/h4mn/skybridge/commit/c46da096640437e0a430e60ce5b46e17c063df30) **queue:** implementar FileBasedJobQueue standalone + observabilidade ([#33](https://github.com/h4mn/skybridge/pull/33)) [`@h4mn`](https://github.com/h4mn)


[**#49**](https://github.com/h4mn/skybridge/pull/49) - sincronização de labels GitHub→Trello e correção de handlers

* [`7534cd9`](https://github.com/h4mn/skybridge/commit/7534cd99102373ff276b95b07efc8921470488dc) **webhooks:** sincronização de labels GitHub→Trello e correção de handlers ([#49](https://github.com/h4mn/skybridge/pull/49)) [`@h4mn`](https://github.com/h4mn)


[**#40**](https://github.com/h4mn/skybridge/pull/40) - configurar branch base para worktrees de agentes

* [`3c29179`](https://github.com/h4mn/skybridge/commit/3c2917974449fbdaf542de120c86f8cceb209826) **webhooks:** configurar branch base para worktrees de agentes ([#40](https://github.com/h4mn/skybridge/pull/40)) [`@h4mn`](https://github.com/h4mn)



### 🐛 Correções

* [`e53d93b`](https://github.com/h4mn/skybridge/commit/e53d93bd32f9952307da0c79d256ec126dc98c40) **build:** remover configuração Poetry do pyproject.toml [`@h4mn`](https://github.com/h4mn)
* [`df89294`](https://github.com/h4mn/skybridge/commit/df89294c3bc38ebd9cd844115c617de2a38788fe) **build:** remover sintaxe inválida no pyproject.toml [`@h4mn`](https://github.com/h4mn)
* [`5508d24`](https://github.com/h4mn/skybridge/commit/5508d2444bd79c2538cdc5038a459181dfa8b237) **ci:** adicionar instalação do requests no workflow de release [`@h4mn`](https://github.com/h4mn)
* [`159690c`](https://github.com/h4mn/skybridge/commit/159690c57b2ae5a10346c956efbd7e88829fde58) **sdk:** implementar custom tools e hooks corretamente via API oficial [`@h4mn`](https://github.com/h4mn)
* [`0f7c04d`](https://github.com/h4mn/skybridge/commit/0f7c04d8946e4cb0300c3317e1eb93a8bda710ef) altera assinatura de PRs automáticos para "made with Sky" [`@h4mn`](https://github.com/h4mn)

[**#66**](https://github.com/h4mn/skybridge/pull/66) - PRD018 Fase 2 - Resolve Problemas P1-P3 da Issue #66

* [`1ea3402`](https://github.com/h4mn/skybridge/commit/1ea34027823437361432165972bdc214402a439d) PRD018 Fase 2 - Resolve Problemas P1-P3 da Issue #66 ([#66](https://github.com/h4mn/skybridge/pull/66)) [`@h4mn`](https://github.com/h4mn)



### ♻️ Refatoração

* [`a5d568a`](https://github.com/h4mn/skybridge/commit/a5d568a835e9ac3e8591aefe7aea462bc949b045) **core:** PRD018 Fase 2 - Application Layer com JobQueueFactory [`@h4mn`](https://github.com/h4mn)

[**#28**](https://github.com/h4mn/skybridge/pull/28) - integração GitHub → Trello com agentes autônomos

* [`2d313ec`](https://github.com/h4mn/skybridge/commit/2d313ec71aa48826030d8a4a91a03532f759bc8e) **namespace:** integração GitHub → Trello com agentes autônomos ([#28](https://github.com/h4mn/skybridge/pull/28)) [`@h4mn`](https://github.com/h4mn)



### 📚 Documentação

* [`f63d6e2`](https://github.com/h4mn/skybridge/commit/f63d6e2a1e097145eea807639559fe8bba1194fe) **adr018:** adicionar seção de motivação com alinhamento internacional [`@h4mn`](https://github.com/h4mn)
* [`d4d4322`](https://github.com/h4mn/skybridge/commit/d4d4322c6eb052b35df79f077e9c972a9ea0839b) **config:** adicionar memória do projeto e reorganizar .env.example [`@h4mn`](https://github.com/h4mn)
* [`c480ebb`](https://github.com/h4mn/skybridge/commit/c480ebb73972442dae083386774fb90b7a654351) **adr:** ADR021 - Adoção do Claude Agent SDK [`@h4mn`](https://github.com/h4mn)
* [`c4069ae`](https://github.com/h4mn/skybridge/commit/c4069ae87535da23ccf4f52603882850ef96b59d) Atualiza PRDs, remove testes obsoletos e adiciona resumo [`@h4mn`](https://github.com/h4mn)
* [`907ee20`](https://github.com/h4mn/skybridge/commit/907ee2098349fde03a41757cdf618452e8c2f578) corrigir numeração PRD019/PRD020 e referências internas [`@h4mn`](https://github.com/h4mn)
* [`7147cad`](https://github.com/h4mn/skybridge/commit/7147cadbbdf25c064ca28b592f81462b1aa0ab4e) adicionar roteiro de aprendizado Git & GitHub avançado [`@h4mn`](https://github.com/h4mn)
* [`6c9a53a`](https://github.com/h4mn/skybridge/commit/6c9a53a92804fd6a0671fdcda0b0d7f6cd977a7d) adicionar PRD018 roadmap autonomia v2.0 e relatório consolidado [`@h4mn`](https://github.com/h4mn)
* [`61d3bd2`](https://github.com/h4mn/skybridge/commit/61d3bd2b6376c8cb95686ed37e2129a4be602e6d) remover PRDs com numeração incorreta [`@h4mn`](https://github.com/h4mn)
* [`601dac3`](https://github.com/h4mn/skybridge/commit/601dac3ec5fbec42ef207448e3aa5ea65da2bbb1) **changelog:** documentar gerador de changelog Sky com Python [`@h4mn`](https://github.com/h4mn)
* [`3cba75a`](https://github.com/h4mn/skybridge/commit/3cba75ab394d6bfef214525fac1f09a06f83fe3b) PRD018 Fase 2 - Documentação e Scripts [`@h4mn`](https://github.com/h4mn)
* [`3caeccd`](https://github.com/h4mn/skybridge/commit/3caeccd0d63d9d5162c13ec6917b29ae7fe56b28) **report:** adiciona relatórios de streaming console e structlog [`@h4mn`](https://github.com/h4mn)
* [`0451b0d`](https://github.com/h4mn/skybridge/commit/0451b0d30ee80b82ba7ffe574d1c30db1e3e0ca6) aprovar ADR021 e criar ADR022 + PRDs para autonomia 2026.S1 [`@h4mn`](https://github.com/h4mn)


### ✅ Testes

* [`e9b606f`](https://github.com/h4mn/skybridge/commit/e9b606fae31e09eebecfbbe82f057381f4cb9ef0) Atualiza test_openapi_hybrid_online para validação completa [`@h4mn`](https://github.com/h4mn)
* [`aecfb66`](https://github.com/h4mn/skybridge/commit/aecfb66ea11814bf553437ebc9c189f2906686b4) **prd019:** suíte completa de testes e correções [`@h4mn`](https://github.com/h4mn)
* [`985c789`](https://github.com/h4mn/skybridge/commit/985c7898607d1c541fd22cb262d41a7d76a66deb) **core:** Corrige fixtures e adiciona event_bus aos testes [`@h4mn`](https://github.com/h4mn)
* [`0cf5cc7`](https://github.com/h4mn/skybridge/commit/0cf5cc753037b8dc593ffb3c2d65566baa015953) **agents:** corrigir testes para API @tool do claude-agent-sdk [`@h4mn`](https://github.com/h4mn)


### 🧹 Tarefas

* [`df3d19e`](https://github.com/h4mn/skybridge/commit/df3d19ee209aa3be0ba846386e0c6541ff4e52b2) **ci:** resolver conflito de merge com main [`@h4mn`](https://github.com/h4mn)
* [`d3b20a5`](https://github.com/h4mn/skybridge/commit/d3b20a50c7a365cbe42553fc5d85f387a3776230) **sync:** sincronizar dev com main (v0.5.4) [`@h4mn`](https://github.com/h4mn)
* [`8598de6`](https://github.com/h4mn/skybridge/commit/8598de6f07d87f2fd2bf925c79603a448c5fe862) **config:** pytest, requirements e configurações [`@h4mn`](https://github.com/h4mn)
* [`837c212`](https://github.com/h4mn/skybridge/commit/837c212044fca9728411e29cc793cb08c87898fd) **sync:** sincronizar dev com main (semantic-release configurado) [`@h4mn`](https://github.com/h4mn)
* [`2c6214f`](https://github.com/h4mn/skybridge/commit/2c6214f1167fb37c0bcecb3466d91e8be0cfae0a) atualiza .gitignore para arquivos locais [`@h4mn`](https://github.com/h4mn)

## [0.9.0] - 2026-01-20


### ✨ Novidades


[**#54**](https://github.com/h4mn/skybridge/pull/54) - habilitar modo detalhado no changelog do release

* [`e86a8fa`](https://github.com/h4mn/skybridge/commit/e86a8fa59ab37f219b77876960f313cc08ecb73a) **ci:** habilitar modo detalhado no changelog do release ([#54](https://github.com/h4mn/skybridge/pull/54)) [`@h4mn`](https://github.com/h4mn)


## [0.8.0] - 2026-01-20


### ✨ Novidades

* [`ee1ab00`](https://github.com/h4mn/skybridge/commit/ee1ab0076e2c73bb7743ccbaa10be39431a281e0) **ci:** implementar gerador de changelog Sky com Python ([#51](https://github.com/h4mn/skybridge/pull/51)) [`@h4mn`](https://github.com/h4mn)


### 🐛 Correções

* [`14508b9`](https://github.com/h4mn/skybridge/commit/14508b9b55a75e12c36bf18cef78dfc1f56d9d5d) **ci:** adicionar instalação do requests no workflow de release ([#53](https://github.com/h4mn/skybridge/pull/53)) [`@h4mn`](https://github.com/h4mn)
* [`68dc02a`](https://github.com/h4mn/skybridge/commit/68dc02aa3f7cf95abcea330ca265d8c69543e45d) **build:** remover sintaxe inválida no pyproject.toml ([#52](https://github.com/h4mn/skybridge/pull/52)) [`@h4mn`](https://github.com/h4mn)

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
