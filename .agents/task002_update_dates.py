import json
from pathlib import Path

json_path = Path(r"B:\\_repositorios\\skybridge\\.agents\\task002-entity-dates.json")
report_path = Path(r"B:\\_repositorios\\skybridge\\.agents\\inspiration-report.md")

with json_path.open("r", encoding="utf-8-sig") as f:
    dates = json.load(f)

text = report_path.read_text(encoding="utf-8")

for k, v in dates.items():
    if v.get("first"):
        v["first"] = v["first"].replace("--", "-")
    if v.get("last"):
        v["last"] = v["last"].replace("--", "-")

parts = text.split("## Entidade: ")

if len(parts) == 1:
    raise SystemExit("Nenhuma entidade encontrada.")

prefix = parts[0]
blocks = parts[1:]
new_blocks = []

for block in blocks:
    lines = block.splitlines()
    if not lines:
        new_blocks.append(block)
        continue

    header = lines[0].strip()
    path = header.split(" (")[0]

    info = dates.get(path)
    if info and info.get("first") and info.get("last"):
        date_line = f"10. Datas de alteração (primeira/última): {info['first']} / {info['last']}"
    else:
        date_line = "10. Datas de alteração (primeira/última): indisponível"

    replaced = False
    for i, line in enumerate(lines):
        if line.startswith("10. Datas de alteração"):
            lines[i] = date_line
            replaced = True
            break

    if not replaced:
        for i, line in enumerate(lines):
            if line.startswith("9. Potencial de amadurecimento"):
                lines.insert(i + 1, date_line)
                replaced = True
                break

    new_blocks.append("\n".join(lines))

new_text = prefix + "## Entidade: " + "## Entidade: ".join(new_blocks)
report_path.write_text(new_text, encoding="utf-8")
print(len(new_blocks))
