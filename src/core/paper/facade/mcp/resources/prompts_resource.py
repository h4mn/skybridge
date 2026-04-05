# -*- coding: utf-8 -*-
"""Resource: Prompts - Paper Trading MCP.

Expõe instruções modulares como recursos MCP.
"""
from ....prompts import load_prompt, PROMPTS


class PromptsResource:
    """Resource MCP para acessar instruções de paper trading.

    URIs disponíveis:
    - paper://prompts/guide - Guia geral de uso
    - paper://prompts/operations - Referência de operações
    - paper://prompts/troubleshooting - Guia de resolução de problemas
    - paper://prompts/all - Todos os prompts combinados
    """

    mime_type = "text/markdown"

    def __init__(self, prompt_name: str):
        """Inicializa o recurso.

        Args:
            prompt_name: Nome do prompt ("guide", "operations", "troubleshooting", "all")
        """
        self.prompt_name = prompt_name
        self.uri = f"paper://prompts/{prompt_name}"

    @property
    def name(self) -> str:
        """Nome amigável do recurso."""
        names = {
            "guide": "Guia de Paper Trading",
            "operations": "Referência de Operações",
            "troubleshooting": "Guia de Troubleshooting",
            "all": "Todas as Instruções",
        }
        return names.get(self.prompt_name, f"Prompt: {self.prompt_name}")

    @property
    def description(self) -> str:
        """Descrição do recurso."""
        descriptions = {
            "guide": """
Instruções gerais de como usar o sistema de paper trading.

Inclui:
- Visão geral das capacidades
- Fluxo de uso recomendado
- Tickers suportados
- Exemplos de conversa
""",
            "operations": """
Referência técnica de todas as operações disponíveis.

Inclui:
- MCP Tools com parâmetros e retornos
- REST API Endpoints
- Códigos de erro
""",
            "troubleshooting": """
Guia de resolução de problemas comuns.

Inclui:
- Problemas frequentes
- Soluções passo a passo
- Comandos de debug
""",
            "all": "Todos os prompts de instrução combinados em um único documento.",
        }
        return descriptions.get(self.prompt_name, "")

    async def read(self) -> str:
        """Lê o conteúdo do prompt.

        Returns:
            Conteúdo markdown do prompt
        """
        if self.prompt_name == "all":
            # Combina todos os prompts
            sections = []
            for name in PROMPTS.keys():
                content = load_prompt(name)
                sections.append(f"---\n# {name.upper()}\n\n{content}")
            return "\n\n".join(sections)

        return load_prompt(self.prompt_name)

    def get_template(self) -> dict:
        """Retorna template do recurso para registro no MCP."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


# Factory para criar todos os recursos de prompt
def create_prompt_resources() -> list[PromptsResource]:
    """Cria instâncias de todos os recursos de prompt.

    Returns:
        Lista de PromptsResource
    """
    return [PromptsResource(name) for name in list(PROMPTS.keys()) + ["all"]]
