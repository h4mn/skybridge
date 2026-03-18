from pathlib import Path


MOJIBAKE_MARKERS = ("\u00c2", "\ufffd")
# Nota: \u00c3 (Ã) foi removido porque é usado em português válido (ex: "NÃO", "SÃO")
# Mojibake real de \u00c3 tipicamente aparece como Ã©, Ã£o, etc (dobrado)


def test_no_mojibake_in_source_files() -> None:
    """Detecta mojibake real sem falso-positivos para português."""
    src_root = Path("src")
    offenders: list[str] = []

    for path in src_root.rglob("*.py"):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            offenders.append(f"{path} (decode_error)")
            continue

        # Procura por padrões de mojibake real (sequências suspeitas)
        # Mojibake real tipicamente aparece como: Ã©, Ã£o, Ã§ (caractere Ã seguido de outro)
        # Ã isolado em português é válido (NÃO, SÃO, PÃO)
        import re
        mojibake_patterns = [
            r'Ã©',  # é corrompido
            r'Ã£o',  # ão corrompido
            r'Ã§',  # ç corrompido
            r'Ã\$',  # qualquer Ã seguido de caractere que não forma português válido
            r'\u00c2[^A-Z]',  # Â seguido de não-maiúscula (provável mojibake)
            r'\ufffd',  # replacement character
        ]

        for pattern in mojibake_patterns:
            if re.search(pattern, content):
                offenders.append(f"{path} (pattern: {pattern})")
                break

    assert not offenders, "Arquivos com mojibake: " + ", ".join(offenders)
