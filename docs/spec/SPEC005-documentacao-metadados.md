---
status: aceito
data: 2025-12-27
---

# SPEC003 - Metadados de Documentação

## 1) Objetivo

Padronizar metadados em documentos do repositório para viabilizar automação,
governança e rastreabilidade.

## 2) Formato obrigatório

Todo documento que exigir metadados deve começar com um bloco delimitado por
`---` no início e `---` no fim. O bloco deve vir no topo do arquivo, seguido
por uma linha vazia e então o título.

Regra: quando o frontmatter existir, **não repetir** `Status/Data` no corpo do
documento.

Exemplo:
```
---
status: proposto
data: 2025-12-27
owner: sky
---

# Título do Documento
```

Regras:

- Chaves em minúsculo.
- Separador `:` entre chave e valor.
- Datas no formato `YYYY-MM-DD`.
- Campos desconhecidos são permitidos, mas devem seguir o mesmo formato.

## 3) Campos mínimos

- `status`
- `data`

Campo recomendado:

- `owner`

## 4) Valores de status

Sugestão de valores:

- `proposto`
- `aceito`
- `substituido`
- `obsoleto`
- `draft`

## 5) Escopo

Aplica-se a PRDs, ADRs, SPECs e Playbooks que precisem de governança.
