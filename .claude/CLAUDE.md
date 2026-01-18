# Memória do Projeto Skybridge

## Servidor de Desenvolvimento

### API Server
- **Comando de inicialização:** `python -m apps.api.main`
- Este é o método preferencial para iniciar o servidor de desenvolvimento

## Gerenciamento de Worktrees

### Sincronização de Ambiente
- **Criar worktree:** Sempre copiar o `.env` do projeto principal para a nova worktree
- **Sincronização bidirecional:** Se o `.env` da worktree estiver mais atual (novas variáveis/alterações), sincronizar de volta com o original
- **Rastreamento:** O `.env` não é versionado no Git, mas o `.env.example` deve ser mantido atualizado
- **Variáveis sensíveis:** Tokens, chaves de API e credenciais devem ser preservadas durante a sincronização

### .env.example
- Manter sempre organizado com:
  - Comentários explicativos para cada variável
  - Separação por categorias funcionais
  - Valores padrão seguros quando aplicável
  - Referências a documentação relevante (ex: PB002 para Ngrok)

> "Simplicidade é o último grau de sofisticação" – made by Sky 🚀
