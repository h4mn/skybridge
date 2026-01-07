from pathlib import Path


MOJIBAKE_MARKERS = ("\u00c3", "\u00c2", "\ufffd")


def test_no_mojibake_in_docs_markdown() -> None:
    docs_root = Path("docs")
    offenders: list[str] = []
    for path in docs_root.rglob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            offenders.append(f"{path} (decode_error)")
            continue
        if any(marker in content for marker in MOJIBAKE_MARKERS):
            offenders.append(str(path))
    assert not offenders, "Arquivos de docs com mojibake: " + ", ".join(offenders)
