# coding: utf-8
"""
Conversor de DOCX para Markdown.

Suporta múltiplas estratégias de conversão:
1. mammoth (recomendado) - Conversão mais fiel de docx → md
2. python-docx - Extração básica de parágrafos
3. pandoc (CLI) - Se instalado no sistema

Requisitos:
    pip install mammoth

    # OU para python-docx:
    pip install python-docx

Uso:
    python scripts/convert_docx_to_md.py arquivo.docx
    python scripts/convert_docx_to_md.py arquivo.docx --output=saida.md
    python scripts/convert_docx_to_md.py arquivo.docx --method=python-docx
"""

import argparse
import sys
from pathlib import Path


def convert_mammoth(docx_path: str, output_path: str | None = None) -> str:
    """
    Converte DOCX para Markdown usando mammoth.

    Mammoth preserva formatação, negrito, itálico, listas, etc.

    Args:
        docx_path: Caminho do arquivo .docx
        output_path: Caminho de saída .md (opcional)

    Returns:
        Conteúdo Markdown gerado
    """
    try:
        import mammoth
    except ImportError:
        print("[ERROR] 'mammoth' not installed.")
        print("        Install with: pip install mammoth")
        sys.exit(1)

    docx = Path(docx_path)
    if not docx.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {docx_path}")

    # Converter para Markdown via HTML intermediário
    with open(docx, "rb") as docx_file:
        result = mammoth.convert_to_markdown(docx_file)
        markdown = result.value

    # Salvar se caminho especificado
    if output_path:
        Path(output_path).write_text(markdown, encoding="utf-8")
        print(f"[OK] Salvo em: {output_path}")
    else:
        # Salvar com mesmo nome do arquivo
        default_output = docx.with_suffix(".md")
        default_output.write_text(markdown, encoding="utf-8")
        print(f"[OK] Salvo em: {default_output}")

    return markdown


def convert_python_docx(docx_path: str, output_path: str | None = None) -> str:
    """
    Converte DOCX para Markdown usando python-docx.

    Método mais básico - extrai apenas parágrafos e negrito/itálico.

    Args:
        docx_path: Caminho do arquivo .docx
        output_path: Caminho de saída .md (opcional)

    Returns:
        Conteúdo Markdown gerado
    """
    try:
        from docx import Document
    except ImportError:
        print("[ERROR] 'python-docx' not installed.")
        print("        Install with: pip install python-docx")
        sys.exit(1)

    docx = Path(docx_path)
    if not docx.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {docx_path}")

    doc = Document(docx)

    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            lines.append("")
            continue

        # Preservar formatação básica
        formatted = ""
        for run in para.runs:
            run_text = run.text
            if run.bold and run.italic:
                formatted += f"***{run_text}***"
            elif run.bold:
                formatted += f"**{run_text}**"
            elif run.italic:
                formatted += f"*{run_text}*"
            else:
                formatted += run_text

        lines.append(formatted)

    markdown = "\n".join(lines)

    # Salvar
    if output_path:
        Path(output_path).write_text(markdown, encoding="utf-8")
        print(f"[OK] Salvo em: {output_path}")
    else:
        default_output = docx.with_suffix(".md")
        default_output.write_text(markdown, encoding="utf-8")
        print(f"[OK] Salvo em: {default_output}")

    return markdown


def convert_pandoc(docx_path: str, output_path: str | None = None) -> str:
    """
    Converte DOCX para Markdown usando pandoc CLI.

    Requer pandoc instalado no sistema:
        Windows: choco install pandoc
        Linux: sudo apt-get install pandoc
        Mac: brew install pandoc

    Args:
        docx_path: Caminho do arquivo .docx
        output_path: Caminho de saída .md (opcional)

    Returns:
        Conteúdo Markdown gerado
    """
    import subprocess

    docx = Path(docx_path)
    if not docx.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {docx_path}")

    if output_path is None:
        output_path = str(docx.with_suffix(".md"))

    try:
        result = subprocess.run(
            ["pandoc", "-f", "docx", "-t", "markdown", "-o", output_path, str(docx)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"[ERROR] pandoc failed: {result.stderr}")
            sys.exit(1)

        # Ler o arquivo gerado
        markdown = Path(output_path).read_text(encoding="utf-8")
        print(f"[OK] Salvo em: {output_path}")

        return markdown

    except FileNotFoundError:
        print("[ERROR] 'pandoc' not installed on system.")
        print("        Install with:")
        print("          Windows: choco install pandoc")
        print("          Linux:   sudo apt-get install pandoc")
        print("          Mac:     brew install pandoc")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Converte arquivos .docx para Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s arquivo.docx
  %(prog)s arquivo.docx --output=saida.md
  %(prog)s arquivo.docx --method=python-docx
  %(prog)s arquivo.docx --method=pandoc

Métodos disponíveis:
  mammoth       - Requer: pip install mammoth (recomendado)
  python-docx   - Requer: pip install python-docx
  pandoc        - Requer: pandoc instalado no sistema
        """,
    )
    parser.add_argument("docx_file", help="Arquivo .docx a converter")
    parser.add_argument(
        "-o",
        "--output",
        help="Caminho de saída .md (padrão: mesmo nome do arquivo)",
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=["mammoth", "python-docx", "pandoc"],
        default="mammoth",
        help="Método de conversão (padrão: mammoth)",
    )

    args = parser.parse_args()

    # Escolher método
    if args.method == "mammoth":
        convert_mammoth(args.docx_file, args.output)
    elif args.method == "python-docx":
        convert_python_docx(args.docx_file, args.output)
    elif args.method == "pandoc":
        convert_pandoc(args.docx_file, args.output)


if __name__ == "__main__":
    main()
