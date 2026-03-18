---
status: aceito
data: 2025-12-25
---

# ADR008 — Adotar HTTPS como transporte opcional

**Status:** Aceito

**Data:** 2025-12-25

## Contexto
A Skybridge e consumida por LLMs/agents e pode rodar fora do localhost. HTTPS e requisito minimo para proteger trafego em ambientes remotos, mas o desenvolvimento local precisa continuar simples (HTTP).

## Decisao
Adicionar suporte a HTTPS (TLS) opcional no servidor, controlado por variaveis de ambiente.

* Quando habilitado (`SKYBRIDGE_SSL_ENABLED=true`), o servidor deve iniciar com `ssl_certfile` e `ssl_keyfile`.
* Quando desabilitado, o servidor inicia em HTTP.

## Consequencias

### Positivas
* Protege trafego em ambientes remotos.
* Permite evolucao para producao sem alterar codigo.

### Negativas / Trade-offs
* Exige provisionamento de certificado e chave.
* Pode introduzir friccao no setup local se habilitado sem arquivos validos.

## Escopo

Inclui: suporte a TLS via env vars.
Nao inclui: mTLS, rotacao automatica, gestao de certificados.

## DoD
* `SKYBRIDGE_SSL_ENABLED=true` com cert/key validos inicia em HTTPS.
* `SKYBRIDGE_SSL_ENABLED=false` inicia em HTTP.

> "Transporte seguro, sem travar o dev." – made by Sky
