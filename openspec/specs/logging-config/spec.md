# logging-config Specification

## Purpose
TBD - created by archiving change internalizar-glitchtip. Update Purpose after archive.
## Requirements
### Requirement: Logger com FileHandler rotativo
O sistema SHALL fornecer `get_logger(name)` que retorna um logger configurado com stdout handler e FileHandler rotativo.

#### Scenario: Logger padrão
- **WHEN** `get_logger("youtube")` é chamado
- **THEN** retorna logger com nome "youtube" E handler stdout E FileHandler em `logs/observability.log`

#### Scenario: Rotação automática
- **WHEN** o arquivo de log atinge 5MB
- **THEN** o FileHandler rotaciona automaticamente mantendo até 3 backups

#### Scenario: Diretório logs/ não existe
- **WHEN** `get_logger()` é chamado E o diretório `logs/` não existe
- **THEN** o sistema cria o diretório automaticamente

### Requirement: Formato estruturado de log
O sistema SHALL usar formato de log estruturado com timestamp, nível, nome do logger e mensagem.

#### Scenario: Formato de saída
- **WHEN** `logger.info("Download completed")` é chamado
- **THEN** a saída segue o formato `YYYY-MM-DD HH:MM:SS | LEVEL | name | message`

### Requirement: Disponibilidade independente do Glitchtip
O sistema SHALL funcionar completamente sem o Glitchtip. O logging em arquivo NÃO depende do Glitchtip estar rodando.

#### Scenario: Glitchtip indisponível
- **WHEN** o Glitchtip NÃO está rodando
- **THEN** `get_logger()` retorna logger funcional E logs são salvos em arquivo normalmente

#### Scenario: Importação isolada
- **WHEN** `from src.core.observability.logging_config import get_logger` é executado
- **THEN** não há dependência de `glitchtip_client.py` ou Docker

