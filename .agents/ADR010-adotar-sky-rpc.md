# ADR-010 — Adoção do Sky-RPC

## Contexto

Durante a integração entre cliente GPT Custom Action e o endpoint `cunning-dear-primate.ngrok-free.app`, identificamos uma limitação estrutural na comunicação via JSON-RPC. O wrapper do jit_plugin local (gerado automaticamente com schema rígido) rejeita qualquer campo além de `jsonrpc`, `id` e `method` — incluindo `params`, essencial para a semântica do JSON-RPC.

O erro recorrente (`UnrecognizedKwargsError: params`) ocorre **antes do envio do request**, durante a validação de schema. Ou seja, o problema não está na API remota, mas na camada de binding entre OpenRPC ↔ Tool Schema. Essa camada não suporta campos aninhados (como `params`), quebrando o contrato RPC tradicional.

Essa limitação expôs um conflito mais profundo:

* **OpenAPI** foca em contratos REST, mas perde a expressividade RPC.
* **JSON-RPC** foca em simplicidade RPC, mas não é extensível nem introspectivo.
* Nenhum dos dois lida bem com ambientes híbridos, como orquestrações distribuídas (ex.: Skybridge).

---

### Diagrama de Causa (Ishikawa)

```
                            ┌───────────────────────────┐
                            │ Falha ao enviar `params`  │
                            └────────────┬──────────────┘
                                         │
 ┌───────────────────────┬────────────────┼────────────────────┬─────────────────────┐
 │ Ambiente Local        │ Binding Schema │ OpenRPC Mapping     │ API Remota          │
 ├───────────────────────┼────────────────┼────────────────────┼─────────────────────┤
 │ Schema rígido         │ `additionalProperties:false` │ Campos não aninhados │ Método validado por nome │
 │ Validação antecipada  │ Falta de flatten reverso │ Falta de suporte a meta │ Anti-injection ativa │
 │ Erro no wrapper local │ Erro antes do envio  │ Perda de semântica RPC │ Rejeição de query params │
 └───────────────────────┴────────────────┴────────────────────┴─────────────────────┘
```

**Síntese:** a falha nasce no cliente, não no servidor. O binding local rejeita `params` por schema fechado e validação precoce, impedindo a transmissão JSON-RPC válida.

---

## Decisão

Adotaremos um novo contrato híbrido chamado **Sky-RPC**, um spec de comunicação orientado a métodos, introspectivo e permissivo no cliente, porém estrito no servidor.

A ideia é que o conteúdo de `method` conterá a chamada completa, com o método (dominio.caso) e argumentos (chave=valor) na mesma string, separados pelo caracter `?`, como no padrão Query Parameters do URI. Ficando um misto de método do JSON-RPC e QueryParameter, característica principal do Sky-RPC.

O formato base de request será:

```json
{
  "jsonrpc": "2.0",
  "id": "1234",
  "method": "fileops.read?path=README.md"
}
```

E a resposta:

```json
// montar result ou error
```

Esse modelo mantém compatibilidade com JSON-RPC (pode ser facilmente adaptado) e adiciona semântica suficiente para introspecção, discovery e versionamento leve.

---

## Consequências

### Positivas

* Simplifica a comunicação entre serviços internos, removendo camadas de schema redundantes.
* Facilita discovery e documentação via `sky.discover`.
* Cria base sólida para geração de SDKs automatizados.
* Reduz acoplamento com padrões externos (OpenAPI / JSON-RPC puros).

### Negativas / Riscos

* Requer novo parser nos gateways.
* Ferramentas externas não compreenderão o formato sem adaptação.
* Precisamos definir claramente as regras de compatibilidade (v1 do Sky-RPC).

---

## Próximos Passos

1. Verificar compatibilidade com decisões anteriores e aplicar patch se necessário.
2. Definir SPEC para a nova adoção.
3. Criar `sky-discover` endpoint unificado.
4. Definir JSON Schema do Sky-RPC v0.1.
5. Documentar política de versionamento e compatibilidade.

---

> "Simplicidade é o poder de orquestrar complexidade sem ruído." – made by Sky ✨
