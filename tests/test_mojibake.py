from pathlib import Path


MOJIBAKE_MARKERS = ("\u00c3", "\u00c2", "\ufffd")


def test_no_mojibake_in_source_files() -> None:
    src_root = Path("src")
    offenders: list[str] = []
    for path in src_root.rglob("*.py"):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            offenders.append(f"{path} (decode_error)")
            continue
        if any(marker in content for marker in MOJIBAKE_MARKERS):
            offenders.append(str(path))
    assert not offenders, "Arquivos com mojibake: " + ", ".join(offenders)
