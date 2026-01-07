# Museu de Testes - Sky-RPC

**Status:** ARQUIVADO

**Data de Arquivamento:** 2025-01-05

---

## O Que É Este Diretório

Este diretório contém testes que foram **arquivados** quando Sky-RPC foi descontinuado.

## Por Que Foram Arquivados

- **Sky-RPC foi descontinuado** em favor de MCP (Model Context Protocol)
- Os testes validam funcionalidade que não será mais mantida
- Mantidos aqui para **análise histórica** e referência futura

## Conteúdo

| Arquivo | O Que Testa | Versão Sky-RPC |
|---------|--------------|----------------|
| `test_sky_rpc.py` | Ticket + Envelope (v0.1/v0.2) | v0.1, v0.2 |
| `test_sky_rpc_v03.py` | Schemas, Registry, Discovery | v0.3 |

## Documentação Relacionada

- **Post-Mortem:** `docs/report/skyrpc-post-mortem-arquivamento.md`
- **Crossfire:** `docs/report/skyrpc-vs-jsonrpc-crossfire.md`
- **Dependência:** `docs/report/skyrpc-dependency-analysis.md`
- **Evolução:** `docs/report/sky-rpc-evolution-analysis.md`

## Posso Executar Esses Testes?

**Sim, mas não são mantidos.**

Se quiser executar por curiosidade ou análise:

```bash
# Teste v0.1/v0.2
cd tests/archived
python test_sky_rpc.py

# Teste v0.3
python test_sky_rpc_v03.py
```

Mas não espere que passem - podem falhar se o código base mudou.

## Por Que Não Deletar?

Testes arquivados preservam:
1. **Comportamento esperado** do Sky-RPC
2. **Exemplos de uso** para análise futura
3. **Validação de schemas** e estruturas
4. **Histórico de evolução** do protocolo

## Aprendizado

Estes testes documentam:
- Como o ticket handshake funcionava
- Como o envelope estruturado era validado
- Como o discovery e reload funcionavam
- Como as versões evuíram (v0.1 → v0.2 → v0.3)

Para alguém no futuro analisando "por que Sky-RPC não deu certo", estes testes são evidência valiosa.

---

> "Código deletado é lição esquecida. Código arquivado é lição preservada."
>
> – made by Sky 🏛️
