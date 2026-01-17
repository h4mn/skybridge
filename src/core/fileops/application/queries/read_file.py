# -*- coding: utf-8 -*-
"""
Read File Query — Query handler para leitura de arquivo.

Application layer orquestra domain + port.
"""

from typing import TypedDict

from kernel import Result
from kernel.registry.decorators import query
from core.fileops.domain.allowed_path import AllowedPath
from core.fileops.ports.filesystem_port import FileSystemPort


class ReadFileRequest(TypedDict):
    """Request para leitura de arquivo."""
    path: str


class ReadFileResponse(TypedDict):
    """Response de leitura de arquivo."""
    path: str
    content: str
    size: int


class ReadFileQuery:
    """
    Query handler para ler arquivo.

    Use case:
    1. Validar path com allowlist
    2. Ler arquivo via FileSystemPort
    3. Retornar conteúdo ou erro
    """

    def __init__(self, allowed_path: AllowedPath, filesystem: FileSystemPort):
        self.allowed_path = allowed_path
        self.filesystem = filesystem

    def execute(self, request: ReadFileRequest) -> Result[ReadFileResponse, str]:
        """
        Executa a query de leitura de arquivo.

        Args:
            request: Dict com `path` do arquivo

        Returns:
            Result com ReadFileResponse ou mensagem de erro
        """
        path = request.get("path", "")

        if not path:
            return Result.err("Path is required")

        # Validar allowlist (via port)
        if not self.filesystem.is_allowed(path):
            return Result.err(f"Path not allowed: {path}")

        # Ler arquivo
        result = self.filesystem.read_file(path)

        if result.is_err:
            return Result.err(result.error)

        content = result.unwrap()

        return Result.ok({
            "path": path,
            "content": content,
            "size": len(content.encode("utf-8")),
        })


_read_file_query: ReadFileQuery | None = None


def set_read_file_query(query: ReadFileQuery) -> None:
    """Configura instancia para uso do handler decorado."""
    global _read_file_query
    _read_file_query = query


@query(
    name="fileops.read",
    description="Read file within allowlist",
    tags=["fileops"],
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
        },
        "required": ["path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "size": {"type": "number"},
        },
        "required": ["path", "content", "size"],
    },
)
def read_file_query(request: ReadFileRequest) -> Result[ReadFileResponse, str]:
    """Handler decorado para Sky-RPC."""
    if _read_file_query is None:
        return Result.err("FileOps not initialized")
    return _read_file_query.execute(request)
