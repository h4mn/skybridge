# features-report.md

## Ranking de entidades (do discovery)
1) B:\_repositorios\Hadsteca\modules\skybridge (score 226)
2) B:\_repositorios\_backup\sky-bridge (score 67)
3) B:\_repositorios\Sky_Bridge (score 60)
4) B:\_repositorios\gpt\src\sky (score 50)
5) B:\_repositorios\_backup\sky-app\skybridge (score 16)
6) B:\_repositorios\Skybridge_2\skybridge (score 5)
7) B:\_repositorios\pyro\projects\sky (score 4)
8) B:\_repositorios\skybridge (score 2)

## Inventario por entidade

### Entidade: B:\_repositorios\Hadsteca\modules\skybridge (score 226)
Classificacao vs nucleo: forte

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| API de arquivos | routes/file_routes.py + services/file_service.py | Endpoints para abrir/editar arquivos e operacoes de arquivo | Camada de file-ops central da Skybridge | Habilita automacao e tooling sobre repos | 226 | B:\_repositorios\Hadsteca\modules\skybridge\routes\file_routes.py | 
| Versionamento GitHub | services/github_service.py | Commit/backup automatico no GitHub | Auditoria e reversao de mudanças | Rastreabilidade e rollback | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\github_service.py |
| Verificacao de dados sensiveis | services/security_check.py + routes/security_routes.py | Detecta chaves/senhas/padroes sensiveis | Protecao e compliance | Reduz risco de vazamento | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\security_check.py |
| Autenticacao/controle | middleware/auth_middleware.py | Middleware de autenticacao | Gate de acesso a API | Seguranca operacional | 226 | B:\_repositorios\Hadsteca\modules\skybridge\middleware\auth_middleware.py |
| OpenAPI | routes/openapi.yaml | Especificacao de endpoints | Contrato de API | Facilita integracao e doc | 226 | B:\_repositorios\Hadsteca\modules\skybridge\routes\openapi.yaml |
| Integracao Discord | routes/discord_routes.py + services/discord_service.py | Acoes/notify via Discord | Canal de comunicacao | Integra notificacoes/acoes | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\discord_service.py |
| Integracao Trello | routes/trello_routes.py + services/trello_service.py | Operacoes de tarefas no Trello | Ponte com planejamento externo | Sincroniza tarefas | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\trello_service.py |
| Integracao Spotify | routes/spotify_routes.py + services/spotify_service.py | Acoes/consulta Spotify | Experiencia/automacao | Integra contexto musical | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\spotify_service.py |
| Integracao VS Code | routes/vscode_routes.py + services/vscode_service.py | Acoes no VS Code | Automacao de dev | Conecta editor a Skybridge | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\vscode_service.py |
| Integracao DALL-E 3 | routes/dalle3_routes.py + services/dalle3_service.py | Geração de imagens | Capacidade multimodal | Expande output criativo | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\dalle3_service.py |
| Wiki/Tarefas | services/wiki_tarefas_service.py | Gestao de wiki/tarefas | Dominio de produtividade | Fonte de conhecimento e tarefas | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\wiki_tarefas_service.py |
| Notifications | services/notifications_service.py | Disparo de notificacoes | Alertas e feedback | Suporte a orquestracao | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\notifications_service.py |
| Ngrok | services/ngrok_service.py | Exposicao de servico local | Publicacao rapida de API | Facilita integracoes | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\ngrok_service.py |
| MCP service | services/mcp_service/* | Provas MCP / extrator RTM | Ponte com LLM via MCP | Compatibilidade MCP | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\mcp_service\README.md |
| Filehub | services/filehub/* | Modulo especializado em arquivos/snapshots | Subplataforma de arquivos | Evolucao de file-ops | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\filehub\__main__.py |
| MessengerHub | services/messengerhub/* | Adaptador para mensagens | Hub de mensageria | Padroniza canais | 226 | B:\_repositorios\Hadsteca\modules\skybridge\services\messengerhub\discord_service_adapter.py |

### Entidade: B:\_repositorios\_backup\sky-bridge (score 67)
Classificacao vs nucleo: parcial

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| Hub de orquestracao | README.md | Define Sky Bridge como hub para orquestrar servicos de LLM | Direcao de plataforma | Norte para arquitetura | 67 | B:\_repositorios\_backup\sky-bridge\README.md |
| CLI base | src/cli.py | CLI da ferramenta | Interface operacao | Operacao local | 67 | B:\_repositorios\_backup\sky-bridge\src\cli.py |
| Dockerizacao | docker-compose.yml + Dockerfile | Ambiente containerizado | Padrao de deploy | Reprodutibilidade | 67 | B:\_repositorios\_backup\sky-bridge\docker-compose.yml |
| CI/CD e testes | README.md + test/ | Indica testes e pipeline | Qualidade e entrega | Disciplina de engenharia | 67 | B:\_repositorios\_backup\sky-bridge\test\test_setup.py |

### Entidade: B:\_repositorios\Sky_Bridge (score 60)
Classificacao vs nucleo: fraca

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| Visao de nucleo Skybridge | README.md | Declara Sky_Bridge como nucleo conector | Direcao conceitual | Alinha narrativa | 60 | B:\_repositorios\Sky_Bridge\README.md |
| App inicial | src/main.py | Ponto de entrada basico | Esqueleto de API | Base para evoluir | 60 | B:\_repositorios\Sky_Bridge\src\main.py |

### Entidade: B:\_repositorios\gpt\src\sky (score 50)
Classificacao vs nucleo: parcial

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| CLI REPL | cli/repl.py + __main__.py | Interface REPL para comandos | Interface operacao | Operacao rapida local | 50 | B:\_repositorios\gpt\src\sky\cli\repl.py |
| Event sourcing | infra/event_store.py + domain/projector.py | Armazena eventos e reconstrucao de estado | Historico de mudancas | Auditabilidade | 50 | B:\_repositorios\gpt\src\sky\infra\event_store.py |
| Estado persistente | infra/json_store.py | Salva estado em JSON | Persistencia local | Recuperacao rapida | 50 | B:\_repositorios\gpt\src\sky\infra\json_store.py |
| Dominio de tarefas | domain/entities.py | Entidades Group/List/Task/Note | Dominio de produtividade | Base de workflow | 50 | B:\_repositorios\gpt\src\sky\domain\entities.py |

### Entidade: B:\_repositorios\_backup\sky-app\skybridge (score 16)
Classificacao vs nucleo: fragmento

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| Servidor MCP | mcp_server.py + README_MCP.md | Exponha API SkyBridge via MCP | Ponte com LLMs | Acesso por tools/agents | 16 | B:\_repositorios\_backup\sky-app\skybridge\README_MCP.md |
| CLI REST | cli-rest.py | Cliente para API SkyBridge | Integracao com API | Operacao manual | 16 | B:\_repositorios\_backup\sky-app\skybridge\cli-rest.py |

### Entidade: B:\_repositorios\Skybridge_2\skybridge (score 5)
Classificacao vs nucleo: fraca

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| Esqueleto Django | settings.py + urls.py | Projeto Django inicial | Base web alternativa | Referencia de stack | 5 | B:\_repositorios\Skybridge_2\skybridge\settings.py |

### Entidade: B:\_repositorios\pyro\projects\sky (score 4)
Classificacao vs nucleo: fragmento

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| Analise e diretrizes | README.md + analysis/* | Documenta stack, riscos e guidelines | Governanca tecnica | Guia de execucao | 4 | B:\_repositorios\pyro\projects\sky\README.md |

### Entidade: B:\_repositorios\skybridge (score 2)
Classificacao vs nucleo: fragmento

| Item | Local | O que faz | Proposito se unificado | Como agrega ao todo | Valor (score) | Evidencia |
| --- | --- | --- | --- | --- | ---: | --- |
| Docs de discovery | docs/* | ADR/PRD/Playbook/TASK de discovery | Base de decisao | Governanca inicial | 2 | B:\_repositorios\skybridge\docs\adr\ADR000-Descoberta via Score de Snapshot.md |

## Padroes e preferencias
- API-first com routes/services separados (B:\_repositorios\Hadsteca\modules\skybridge\routes\* e services\*).
- Integracoes externas como modulos (Discord, Trello, Spotify, GitHub, VS Code).
- Seguranca como camada (auth middleware + security_check).
- Observabilidade e logs (logger_service.py, logs/).
- CLI/REPL como interface secundaria (gpt\src\sky e _backup\sky-bridge\src\cli.py).
- Event sourcing para dominio de tarefas (gpt\src\sky).
- MCP como ponte para LLMs (sky-app\skybridge).

## Dominios e infras (rascunho)
- Dominios: File, Git/Versionamento, Segurança, Mensageria, Tarefas/Wiki, Notificações, Integrações, Conteúdo/Imagem.
- Infras: FastAPI/Uvicorn, OpenAPI, GitHub API, Docker/Compose, MCP, Event Store (jsonl), Ngrok.

## Blueprints candidatos
- API-first Core: routes + services + auth + security + openapi.
- FileOps Core: file_service + backups + github_service.
- Integration Hub: adaptadores (Discord/Trello/Spotify/VSCode/DALL-E).
- CLI/REPL Core: event sourcing + state store.
- MCP Gateway: server MCP para expor tools/resources.

## Strategy ladder (rascunho)
- Capabilities: edicao segura de arquivos, versionamento, integracoes, tarefas.
- Platform: API unificada + contratos OpenAPI + event store + MCP gateway.
- Leverage: novos agentes/skills conectados ao core, automacoes cross-sistemas.
