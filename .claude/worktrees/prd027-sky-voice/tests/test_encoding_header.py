from pathlib import Path
import re


CODING_RE = re.compile(r"^[ \t\f]*#.*coding[:=][ \t]*utf-8", re.IGNORECASE)


def test_all_python_files_have_utf8_coding_cookie() -> None:
    src_root = Path("src")
    missing: list[str] = []
    for path in src_root.rglob("*.py"):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            missing.append(f"{path} (decode_error)")
            continue
        head = lines[:2]
        if not any(CODING_RE.search(line) for line in head):
            missing.append(str(path))
    assert not missing, "Arquivos sem cabeçalho utf-8: " + ", ".join(missing)
