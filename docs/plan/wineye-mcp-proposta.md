# WINEYE MCP - Proposta Técnica Mínima

> **WINEYE**: Windows UI Observation & Error Examination via MCP

## 🎯 Objetivo

Criar um servidor MCP que permite ao Claude **observar e analisar** UIs de aplicações Windows nativas (como SkyChat) para diagnosticar erros, anomalias visuais e estados inconsistentes.

**O que NÃO é:**
- ❌ Ferramenta de automação (RPA)
- ❌ Fork do Skyvern
- ❌ Controle de janelas (click, digitar)

**O que É:**
- ✅ Ferramenta de **observação e análise**
- ✅ Debugging assistido por AI
- � Captura + raciocínio sobre UIs nativas

---

## 📋 Requisitos Mínimos

### Funcionalidades Core (MVP)

| ID | Funcionalidade | Descrição |
|----|---------------|-----------|
| F1 | `capture_window` | Captura screenshot de janela Windows específica |
| F2 | `analyze_ui` | Analisa UI com Claude Vision para identificar erros |
| F3 | `detect_elements` | Detecta elementos interativos na UI (botões, inputs) |
| F4 | `compare_states` | Compara dois estados da UI (before/after) |

### Casos de Uso

1. **SkyChat Error Diagnosis**
   ```
   Usuário reporta: "A SkyChat travou"
   → WINEYE captura tela
   → Claude analise: "Vejo mensagem 'Connection timeout'"
   → Diagnóstico estruturado
   ```

2. **Visual Regression Testing**
   ```
   Dev atualiza SkyChat
   → Compara UI antes/depois
   → Lista mudanças detectadas
   ```

3. **Auto-diagnóstico**
   ```python
   # Hook na SkyChat
   except Exception as e:
       diagnosis = await wineye.analyze_ui("SkyChat", str(e))
       logger.error(f"Auto-diagnosis: {diagnosis}")
   ```

---

## 🛠️ Stack Tecnológico

```python
# Mínimo necessário para MVP

pywinauto==0.6.8       # Encontrar e manipular janelas Windows
mss==9.0.1            # Screenshot rápido (cross-platform)
Pillow==10.0.0        # Processamento de imagem
anthropic==0.39.0     # Claude API (vision)
mcp==0.9.0            # Model Context Protocol
```

---

## 📁 Estrutura de Diretórios

```
skybridge/
└── mcp/
    └── wineye/
        ├── __init__.py
        ├── server.py              # MCP server principal
        ├── capture.py              # Screenshot de janelas
        ├── analyzer.py             # Análise com Claude
        ├── prompts.py              # Templates de prompts
        └── schemas.py              # Tipos Pydantic
```

---

## 🔌 MCP Tools (API)

```python
# skybridge/mcp/wineye/server.py

from mcp import Server

app = Server("wineye")

@app.tool()
async def capture_window(
    title: str,
    format: Literal["base64", "path"] = "base64"
) -> str:
    """
    Captura screenshot de janela Windows específica.

    Args:
        title: Título da janela (ex: "SkyChat")
        format: "base64" retorna string, "path" salva arquivo

    Returns:
        Screenshot em base64 ou caminho do arquivo
    """

@app.tool()
async def analyze_ui(
    title: str,
    context: str = "",
    focus: str | None = None
) -> UIAnalysis:
    """
    Analisa UI com Claude Vision.

    Args:
        title: Título da janela
        context: Contexto do problema (ex: "Erro ao conectar")
        focus: Onde focar (ex: "botão enviar", "mensagens de erro")

    Returns:
        {
            "error_detected": bool,
            "error_type": str | None,
            "elements": List[UIElement],
            "anomalies": List[str],
            "suggestion": str | None
        }
    """

@app.tool()
async def detect_elements(title: str) -> List[UIElement]:
    """
    Detecta elementos interativos na UI.

    Returns:
        [
            {"type": "button", "text": "Enviar", "position": {...}},
            {"type": "input", "placeholder": "Mensagem", "position": {...}},
            ...
        ]
    """

@app.tool()
async def compare_states(
    title: str,
    before: str,  # base64 ou path
    after: str
) -> StateDiff:
    """
    Compara dois estados da UI.

    Returns:
        {
            "changes": [
                {"type": "position", "element": "button", "delta": "5px right"},
                {"type": "color", "element": "text", "from": "#333", "to": "#000"},
                ...
            ]
        }
    """
```

---

## 🎨 Implementação Core (Pseudocódigo)

```python
# skybridge/mcp/wineye/capture.py

import mss
import base64
from pywinauto import Application

class WindowCapture:
    async def capture(self, title: str) -> str:
        """Captura janela e retorna base64"""
        # 1. Encontra janela
        app = Application().connect(title=title)
        window = app.top_window()
        rect = window.rectangle()

        # 2. Captura com mss
        with mss() as sct:
            monitor = {
                "top": rect.top,
                "left": rect.left,
                "width": rect.width(),
                "height": rect.height()
            }
            screenshot = sct.grab(monitor)

        # 3. Converte para base64
        from io import BytesIO
        from PIL import Image

        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

# skybridge/mcp/wineye/analyzer.py

from anthropic import Anthropic

class UIAnalyzer:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    async def analyze(
        self,
        image_b64: str,
        context: str = "",
        focus: str | None = None
    ) -> dict:
        """Analisa UI com Claude Vision"""

        prompt = f"""
        Analise esta UI de aplicação Windows nativa.

        Contexto do problema: {context}
        {f'Foque em: {focus}' if focus else ''}

        Identifique:
        1. Erros visuais óbvios (mensagens de erro, warnings)
        2. Estados inconsistentes (botões desabilitados, layouts quebrados)
        3. Elementos que parecem quebrados
        4. Cores, ícones ou texto fora do comum

        Responda em JSON estruturado.
        """

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        return self._parse_response(response)

# skybridge/mcp/wineye/server.py

from mcp import Server
from .capture import WindowCapture
from .analyzer import UIAnalyzer

app = Server("wineye")
capture = WindowCapture()
analyzer = UIAnalyzer(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.tool()
async def capture_window(title: str) -> str:
    return await capture.capture(title)

@app.tool()
async def analyze_ui(title: str, context: str = "") -> dict:
    image_b64 = await capture.capture(title)
    return await analyzer.analyze(image_b64, context)
```

---

## 📊 Roadmap

| Fase | Descrição | Estimativa | Status |
|------|-----------|------------|--------|
| **MVP** | F1: capture_window | 2 dias | 🔲 Todo |
| **MVP** | F2: analyze_ui | 3 dias | 🔲 Todo |
| **V1** | F3: detect_elements | 2 dias | 🔲 Todo |
| **V1** | F4: compare_states | 2 dias | 🔲 Todo |
| **V2** | Integração SkyChat | 2 dias | 🔲 Todo |
| **V2** | Autodiagnóstico | 1 dia | 🔲 Todo |

**Total MVP:** ~5 dias úteis
**Total V1:** ~12 dias úteis

---

## 🔑 Variáveis de Ambiente

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
WINEYE_SCREENSHOT_DIR=/tmp/wineye/screenshots
WINEYE_LOG_LEVEL=INFO
```

---

## ⚙️ Configuração MCP

```json
// .mcp.json
{
  "mcpServers": {
    "wineye": {
      "command": "python",
      "args": ["-m", "skybridge.mcp.wineye.server"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      }
    }
  }
}
```

---

## 🧪 Exemplo de Uso

```
Usuário: "A SkyChat está com erro na tela"

Claude (usando WINEYE MCP):

1. [capture_window(title="SkyChat")]
   ✓ Capturou janela

2. [analyze_ui(title="SkyChat", context="Usuário reporta erro")]
   ✓ Analisando com Claude Vision...

   Resposta:
   {
     "error_detected": true,
     "error_type": "connection_error",
     "elements": [
       {"type": "error_message", "text": "Connection timeout", "position": "bottom-right"}
     ],
     "anomalies": [
       "Botão 'Enviar' appears disabled (grayed out)",
       "Spinner de carregamento visível no topo"
     ],
     "suggestion": "Verificar conexão de rede. O problema parece ser na camada de WebSocket, não na UI em si."
   }

3. Claude formula resposta para usuário com base na análise
```

---

## 📝 Notas de Design

1. **Observação apenas**: Não controla a UI, só observa
2. **Não intrusivo**: Usa APIs Windows nativas, não injeta código
3. **Privacidade**: Screenshots ficam locais, enviados apenas para Claude API
4. **Cross-platform futuro**: Arquitetura permite suporte a macOS/Linux depois

---

## 🚀 Próximos Passos

1. ✅ Proposta aprovada
2. 🔲 Criar estrutura `mcp/wineye/`
3. 🔲 Implementar `capture.py` (mss + pywinauto)
4. 🔲 Implementar `analyzer.py` (Claude Vision)
5. 🔲 Implementar `server.py` (MCP)
6. 🔲 Testar com SkyChat

---

> "A melhor ferramenta é a que resolve o problema real" – made by Sky 🎯
