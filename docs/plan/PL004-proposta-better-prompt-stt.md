# Proposta: Agente de Correção pós-STT

## 🎯 Objetivo
Criar uma camada inteligente de correção entre o STT (Speech-to-Text) e o sistema de comandos, capaz de entender erros de transcrição de termos técnicos e inferir a intenção real do usuário baseado no contexto do codebase.

---

## 📋 Problema Atual

### Exemplos Reais de Falhas do STT:
```
❌ STT: "salva na pasta SCR/Quore/Sky"
✅ Real: "salva na pasta src/core/sky"

❌ STT: "PF SRC Quore"
✅ Real: "path src core"

❌ STT: "C Quore Sky"
✅ Real: "src core sky"
```

### Causa Raiz:
- STT configurado para **português**
- Termos técnicos são em **inglês** (src, core, path, etc.)
- Fonetização imprópria ("C" → "Quore", "path" → "PF")
- **Sem contexto do código** para ajudar na correção

---

## 🧩 Solução Proposta

### Arquitetura:
```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│   STT       │ ───► │  Agente LLM      │ ───► │  Sistema de │
│ (Fraco)     │      │  Correção        │      │  Comandos   │
│             │      │  Contextual      │      │             │
└─────────────┘      └──────────────────┘      └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Contexto do  │
                    │ Codebase     │
                    └──────────────┘
```

### Fluxo de Funcionamento:
1. **Usuário fala** → STT transcreve (com erros)
2. **Transcrição bruta** → Agente LLM recebe
3. **Agente analisa**:
   - Transcrição recebida
   - Estrutura do projeto (pastas, arquivos)
   - Comandos conhecidos
   - Padrões de sintaxe
4. **Agente retorna** → Comando corrigido e conciso
5. **Sistema executa** → Comando entendido corretamente

---

## 🏗️ Implementação

### 1. **Módulo Coletor de Contexto**
```python
# src/core/sky/workers/context_collector.py

class ContextCollector:
    """Mapeia o contexto atual do projeto"""

    async def get_project_structure(self) -> dict:
        """Retorna estrutura de pastas e arquivos relevantes"""
        return {
            "pastas": ["src", "core", "sky", "app", "components", "screens"],
            "arquivos_recentes": [...],
            "comandos_conhecidos": ["salvar", "criar", "abrir", "listar"],
            "termos_tecnicos": ["src", "core", "path", "file", "widget"]
        }
```

### 2. **Agente de Correção LLM**
```python
# src/core/sky/workers/stt_corrector.py

class STTCorrector:
    """Usa LLM para corrigir transcrições falhas do STT"""

    async def correct(self, raw_transcript: str, context: dict) -> str:
        prompt = self._build_correction_prompt(raw_transcript, context)
        corrected = await self.llm.complete(prompt)
        return self._parse_correction(corrected)

    def _build_correction_prompt(self, transcript: str, ctx: dict) -> str:
        return f"""
Você é um especialista em corrigir transcrições de voz falhas.

**Transcrição STT (com erros):**
"{transcript}"

**Contexto do Projeto:**
- Pastas válidas: {ctx['pastas']}
- Comandos conhecidos: {ctx['comandos_conhecidos']}
- Termos técnicos: {ctx['termos_tecnicos']}

**Problemas comuns:**
- "Quore" → "core"
- "PF/path" → "src" ou "path"
- "C" → "src"
- Termos em inglês transcritos como português

**Sua tarefa:**
1. Analise a transcrição e o contexto
2. Corrija erros óbvios de STT
3. Retorne apenas o comando corrigido, conciso e claro

**Exemplo:**
Entrada: "salva na pasta SCR Quore Sky"
Saída: "salvar em src/core/sky"

**RETORNE APENAS O COMANDO CORRIGIDO, nada mais.**
"""
```

### 3. **Integração no Pipeline**
```python
# src/core/sky/screens/chat_screen.py

class ChatScreen:
    async def on_voice_command(self, raw_stt_output: str):
        # 1. Coletar contexto
        context = await self.context_collector.get_project_structure()

        # 2. Corrigir com LLM
        corrected_command = await self.stt_corrector.correct(
            raw_stt_output,
            context
        )

        # 3. Executar comando corrigido
        await self.execute_command(corrected_command)

        # 4. Log para aprendizado
        self.log_correction(raw_stt_output, corrected_command)
```

---

## 📊 Exemplos de Uso

### Antes vs Depois:

| Transcrição STT | Comando Corrigido | Contexto Usado |
|-----------------|-------------------|----------------|
| "salva na SCR Quore Sky" | "salvar em src/core/sky" | pasta "core" existe |
| "PF SRC Quore" | "path src core" | pasta "src" existe |
| "C Quore Sky" | "src core sky" | pastas "src" e "core" |
| "abri o arquivo de confi" | "abrir arquivo config" | arquivo "config" existe |

---

## 🚀 Etapas de Implementação

### Fase 1: Fundação
- [ ] Criar módulo `context_collector.py`
- [ ] Mapear estrutura do projeto
- [ ] Identificar termos técnicos comuns

### Fase 2: Agente LLM
- [ ] Criar módulo `stt_corrector.py`
- [ ] Implementar prompt template
- [ ] Testar com exemplos reais

### Fase 3: Integração
- [ ] Inserir no pipeline de comandos de voz
- [ ] Adicionar logging de correções
- [ ] Criar interface de debug (mostrar original vs corrigido)

### Fase 4: Otimização
- [ ] Cache de correções comuns
- [ ] Aprendizado com correções recorrentes
- [ ] Métricas de taxa de sucesso

---

## 🔧 Configuração

### Variáveis de Ambiente:
```env
# Modelo LLM para correção (pode ser menor/faster)
STT_CORRECTOR_MODEL=gpt-4o-mini
# ou
STT_CORRECTOR_MODEL=claude-haiku

# Mostrar transcrição original vs corrigida?
DEBUG_STT_CORRECTION=true
```

---

## 📈 Benefícios Esperados

1. **✅ Robustez** - Sistema funciona mesmo com STT falho
2. **✅ Contextual** - Usa conhecimento do projeto para corrigir
3. **✅ Flexível** - Adapta-se a novos erros sem reprogramação
4. **✅ Aprendizável** - Logs permitem otimização contínua
5. **✅ Conciso** - Remove redundâncias da fala natural

---

## 🧪 Testes

### Casos de Teste:
```python
test_cases = [
    ("salva na SCR Quore Sky", "salvar em src/core/sky"),
    ("PF SRC Quore", "path src core"),
    ("abri o widget de chat", "abrir widget chat"),
    ("cria uma nova tela", "criar tela"),
]
```

---

## 📝 Próximos Passos

1. **Aprovação** da proposta
2. **Escolha do modelo** LLM para correção
3. **Implementação** fase 1 e 2
4. **Testes** com comandos reais
5. **Deploy** e validação

---

**📖 made by Sky 🚀**
