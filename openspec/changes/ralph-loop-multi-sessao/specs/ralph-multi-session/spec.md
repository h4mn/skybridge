# Spec: Ralph Multi-Session

## ADDED Requirements

### Requirement: Arquivo de estado por sessão

O sistema Ralph Loop SHALL criar um arquivo de estado único por sessão do Claude Code usando o session_id no nome do arquivo.

#### Scenario: Criação de arquivo por sessão

- **GIVEN** uma sessão do Claude Code com session_id `72dc7f6e-e0d8-4e32-8a88414294e5e`
- **WHEN** o usuário executa `/ralph-loop:ralph-loop "minha tarefa"`
- **THEN** o sistema SHALL criar o arquivo `.claude/ralph-loop.72dc7f6e-e0d8-4e32-8a88414294e5e.md`
- **AND** o arquivo SHALL conterter o session_id correto no frontmatter

#### Scenario: Múltiplas sessões simultâneas

- **GIVEN** duas sessões Claude Code com session_ids diferentes
- **WHEN** Sessão A executa `/ralph-loop:ralph-loop "tarefa A"`
- **AND** Sessão B executa `/ralph-loop:ralph-loop "tarefa B"`
- **THEN** SHALL ser criado `.claude/ralph-loop.{session_A}.md`
- **AND** SHALL ser criado `.claude/ralph-loop.{session_B}.md`
- **AND** cada arquivo SHALL ter seu próprio session_id no frontmatter

### Requirement: Stop hook identifica arquivo da sessão atual

O stop hook SHALL identificar o arquivo de estado correspondente à sessão atual usando o session_id fornecido no HOOK_INPUT.

#### Scenario: Stop hook localiza arquivo correto

- **GIVEN** Ralph Loop ativo na sessão com session_id `abc-123`
- **WHEN** o stop hook é executado ao tentar sair
- **THEN** o hook SHALL receber `{"session_id": "abc-123", ...}` via STDIN
- **AND** o hook SHALL localizar o arquivo `.claude/ralph-loop.abc-123.md`
- **AND** o hook SHALL bloquear a saída se o session_id do arquivo corresponder ao session_id do hook

#### Scenario: Sessão sem loop não é bloqueada

- **GIVEN** uma sessão com session_id `def-456` SEM Ralph Loop ativo
- **WHEN** o stop hook é executado
- **THEN** o hook SHALL receber `{"session_id": "def-456", ...}` via STDIN
- **AND** o hook SHALL não encontrar arquivo `.claude/ralph-loop.def-456.md`
- **AND** o hook SHALL permitir saída (exit 0)

### Requirement: Cancel remove arquivo correto por sessão

O comando `/ralph-loop:cancel-ralph` SHALL remover o arquivo de estado correspondente à sessão atual usando o session_id capturado pelo UserPromptSubmit hook.

#### Scenario: Cancela loop da sessão atual

- **GIVEN** Ralph Loop ativo na sessão com session_id `xyz-789`
- **AND** arquivo de estado `.claude/ralph-loop.xyz-789.md` existe
- **WHEN** usuário executa `/ralph-loop:cancel-ralph`
- **THEN** o sistema SHALL ler session_id do cache em `.claude/cache/ralph-session-id.txt`
- **AND** o sistema SHALL remover `.claude/ralph-loop.xyz-789.md`

#### Scenario: Arquivo não encontrado

- **GIVEN** nenhuma sessão com Ralph Loop ativo
- **WHEN** usuário executa `/ralph-loop:cancel-ralph`
- **THEN** o sistema SHALL reportar "No active Ralph loop found"

### Requirement: Compatibilidade com formato legado

O sistema SHALL suportar temporariamente o formato legado `.claude/ralph-loop.local.md` para backwards compatibility.

#### Scenario: Loop legado ainda funciona

- **GIVEN** um loop antigo com arquivo `.claude/ralph-loop.local.md`
- **WHEN** o stop hook é executado
- **THEN** o hook SHALL aceitar ambos os formatos (legado e por sessão)
- **AND** o hook SHALL processar normalmente o arquivo encontrado
