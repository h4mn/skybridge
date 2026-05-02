"""
Cedilha Hook — Detector de diacríticos ausentes em pt-BR.

Hook PostToolUse para Claude Code que detecta palavras sem acentos
em arquivos .md e .txt, bloqueia a escrita e lista correções.

Uso: configurado como hook PostToolUse no hooks.json do projeto.
"""

import sys
import json
import re
from pathlib import Path

# Dicionário reverso: forma sem acento → forma com acento
# Palavras mais frequentes em pt-BR que perdem diacríticos
REVERSE_DICT = {
    # a → á, ã, à
    "ate": "até",
    "ja": "já",
    "la": "lá",
    "ta": "tá",
    "pra": "pra",
    "aquela": "aquela",
    "aquelas": "aquelas",
    "este": "este",
    "desta": "desta",
    "nesta": "nesta",
    "ultima": "última",
    "ultimas": "últimas",
    "ultimo": "último",
    "ultimos": "últimos",
    "util": "útil",
    "uteis": "úteis",
    "analise": "análise",
    "analises": "análises",
    "url": "url",  # não corrigir
    # e → é, ê
    "voce": "você",
    "ele": "ele",
    "ela": "ela",
    "eles": "eles",
    "elas": "elas",
    "de": "de",
    "que": "que",
    "se": "se",
    "no": "no",
    "ser": "ser",
    "pode": "pode",
    "esse": "esse",
    "essa": "essa",
    "nele": "nele",
    "nela": "nela",
    "numero": "número",
    "numeros": "números",
    "metodo": "método",
    "metodos": "métodos",
    "acessivel": "acessível",
    "possivel": "possível",
    "possiveis": "possíveis",
    "impossivel": "impossível",
    "responsavel": "responsável",
    "responsaveis": "responsáveis",
    "notavel": "notável",
    "visivel": "visível",
    "legivel": "legível",
    "sensivel": "sensível",
    # i → í
    "aqui": "aqui",
    "individual": "individual",
    "inicial": "inicial",
    "inicio": "início",
    "inicios": "inícios",
    "critica": "crítica",
    "criticas": "críticas",
    "critico": "crítico",
    "criticos": "críticos",
    "antiga": "antiga",
    "antigas": "antigas",
    "antigo": "antigo",
    "antigos": "antigos",
    # o → ó, õ
    "avos": "avos",
    "orgao": "órgão",
    "orgaos": "órgãos",
    "destroi": "destrói",
    # u → ú
    "ruim": "ruim",
    # c → ç
    "transcricao": "transcrição",
    "transcricoes": "transcrições",
    "producao": "produção",
    "producoes": "produções",
    "configuracao": "configuração",
    "configuracoes": "configurações",
    "correcao": "correção",
    "correcoes": "correções",
    "funcao": "função",
    "funcoes": "funções",
    "informacao": "informação",
    "informacoes": "informações",
    "solucao": "solução",
    "solucoes": "soluções",
    "acao": "ação",
    "acoes": "ações",
    "operacao": "operação",
    "operacoes": "operações",
    "criacao": "criação",
    "criacoes": "criações",
    "conexao": "conexão",
    "conexoes": "conexões",
    "direcao": "direção",
    "direcoes": "direções",
    "versao": "versão",
    "versoes": "versões",
    "excecao": "exceção",
    "excecoes": "exceções",
    "secao": "seção",
    "secoes": "seções",
    "situacao": "situação",
    "situacoes": "situações",
    "validacao": "validação",
    "validacoes": "validações",
    "implementacao": "implementação",
    "implementacoes": "implementações",
    "integracao": "integração",
    "integracoes": "integrações",
    "execucao": "execução",
    "execucoes": "execuções",
    "aplicacao": "aplicação",
    "aplicacoes": "aplicações",
    "localizacao": "localização",
    "localizacoes": "localizações",
    "autenticacao": "autenticação",
    "autenticacoes": "autenticações",
    "autorizacao": "autorização",
    "autorizacoes": "autorizações",
    "organizacao": "organização",
    "organizacoes": "organizações",
    "atualizacao": "atualização",
    "atualizacoes": "atualizações",
    "notificacao": "notificação",
    "notificacoes": "notificações",
    "comunicacao": "comunicação",
    "comunicacoes": "comunicações",
    "especificacao": "especificação",
    "especificacoes": "especificações",
    "verificacao": "verificação",
    "verificacoes": "verificações",
    "requisicao": "requisição",
    "requisicoes": "requisições",
    "resolucao": "resolução",
    "resolucoes": "resoluções",
    "classificacao": "classificação",
    "classificacoes": "classificações",
    "rejeicao": "rejeição",
    "rejeicoes": "rejeições",
    "inicializacao": "inicialização",
    "inicializacoes": "inicializações",
    "configuracoes": "configurações",
    "instrucao": "instrução",
    "instrucoes": "instruções",
    "duracao": "duração",
    "duracoes": "durações",
    "confianca": "confiança",
    "importancia": "importância",
    "relevancia": "relevância",
    "excelencia": "excelência",
    "conferencia": "conferência",
    "referencia": "referência",
    "preferencia": "preferência",
    "experiencia": "experiência",
    "frequencia": "frequência",
    "consequencia": "consequência",
    "influencia": "influência",
    "ausencia": "ausência",
    "presenca": "presença",
    "dependencia": "dependência",
    "independencia": "independência",
    "pendencia": "pendência",
    "procedencia": "procedência",
    "evidencia": "evidência",
    "providencia": "providência",
    "tolerancia": "tolerância",
    "garantia": "garantia",
    "cotidiano": "cotidiano",
    "ingestao": "ingestão",
    "ingestoes": "ingestões",
    # Comuns sem acento
    "tambem": "também",
    "porem": "porém",
    "alem": "além",
    "atraves": "através",
    "pais": "país",
    "paises": "países",
    "historia": "história",
    "historias": "histórias",
    "memoria": "memória",
    "memorias": "memórias",
    "categoria": "categoria",
    "categorias": "categorias",
    "pagina": "página",
    "paginas": "páginas",
    "codigo": "código",
    "codigos": "códigos",
    "metodo": "método",
    "metodos": "métodos",
    "periodo": "período",
    "periodos": "períodos",
    "logica": "lógica",
    "logico": "lógico",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "tecnicos": "técnicos",
    "tecnico": "técnico",
    "genero": "gênero",
    "generos": "gêneros",
    "bateria": "bateria",
    "batidas": "batidas",
    "correto": "correto",
    "correta": "correta",
    "corretos": "corretos",
    "corretas": "corretas",
    "incorreto": "incorreto",
    "incorreta": "incorreta",
    "telefone": "telefone",
    "modulo": "módulo",
    "modulos": "módulos",
    "regiao": "região",
    "regioes": "regiões",
    "uniao": "união",
    "caminhao": "caminhão",
    "coracao": "coração",
    "coracoes": "corações",
    "emocao": "emoção",
    "emocoes": "emoções",
    "musica": "música",
    "musicas": "músicas",
    "musico": "músico",
    "unico": "único",
    "unica": "única",
    "unicos": "únicos",
    "unicas": "únicas",
    "log": "log",
    "doc": "doc",
    "docs": "docs",
    "env": "env",
    "etc": "etc",
    "api": "api",
    "cli": "cli",
    "mcp": "mcp",
    "tdd": "tdd",
    "bdd": "bdd",
    "ci": "ci",
    "cd": "cd",
    "json": "json",
    "yaml": "yaml",
    "html": "html",
    "sql": "sql",
}

# Palavras que NÃO devem ser corrigidas (código, URLs, identificadores)
SKIP_PATTERNS = re.compile(
    r'(^[\s]*[`~])|'      # código inline/bloco
    r'(https?://)|'        # URLs
    r'(\.[a-z]{2,4}$)|'   # extensões de arquivo
    r'(^[A-Z_]+$)|'        # constantes UPPER_CASE
    r'(^[a-z_]+\(\))|'    # chamadas de função
    r'(^[a-z_]+\.[a-z]+)' # atributos
)

# Extensões de arquivo para verificar
CHECK_EXTENSIONS = {'.md', '.txt', '.markdown'}


def load_hook_input():
    """Lê input JSON do hook do Claude Code via stdin."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def extract_file_path(tool_input: dict) -> str | None:
    """Extrai caminho do arquivo do input do tool."""
    return tool_input.get("file_path") or tool_input.get("path")


def should_check(file_path: str) -> bool:
    """Verifica se o arquivo deve ser checado."""
    if not file_path:
        return False
    ext = Path(file_path).suffix.lower()
    return ext in CHECK_EXTENSIONS


def find_missing_diacritics(content: str) -> list[dict]:
    """Encontra palavras com diacríticos ausentes no conteúdo."""
    issues = []
    seen = set()

    for line_num, line in enumerate(content.split('\n'), 1):
        # Pular linhas de código
        stripped = line.strip()
        if stripped.startswith('```') or stripped.startswith('    ') or stripped.startswith('\t'):
            continue
        if stripped.startswith('|') and '```' in stripped:
            continue

        # Tokenizar por palavras
        words = re.findall(r'[a-zA-ZáàãâéêíóôõúüçñÁÀÃÂÉÊÍÓÔÕÚÜÇÑ]+', line.lower())

        for word in words:
            if word in seen:
                continue
            if word in REVERSE_DICT:
                corrected = REVERSE_DICT[word]
                # Só reporta se a forma correta for diferente (tem diacrítico)
                if corrected != word and any(c in corrected for c in 'áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ'):
                    # Verifica se não está em contexto de código
                    pattern = rf'`[^`]*{word}[^`]*`'
                    if not re.search(pattern, line):
                        seen.add(word)
                        issues.append({
                            "line": line_num,
                            "original": word,
                            "suggested": corrected,
                        })

    return issues


def format_report(issues: list[dict], file_path: str) -> str:
    """Formata relatório de diacríticos ausentes."""
    count = len(issues)
    filename = Path(file_path).name

    lines = [f"\n Cedilha: {count} diacrítico(s) ausente(s) em {filename}\n"]

    for issue in issues[:15]:
        lines.append(f'  - linha {issue["line"]}: "{issue["original"]}" → "{issue["suggested"]}"')

    if count > 15:
        lines.append(f"  ... e mais {count - 15}")

    lines.append("\n Corrija os diacríticos e reescreva o arquivo.")
    return '\n'.join(lines)


def main():
    """Entry point do hook."""
    hook_input = load_hook_input()
    tool_input = hook_input.get("tool_input", hook_input)
    file_path = extract_file_path(tool_input)

    if not should_check(file_path):
        sys.exit(0)

    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    if not content:
        sys.exit(0)

    issues = find_missing_diacritics(content)

    if issues:
        report = format_report(issues, file_path)
        print(report, file=sys.stderr)
        # Retorna erro pra bloquear a tool
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
