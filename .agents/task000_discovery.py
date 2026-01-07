import json
import os
import re
from pathlib import Path

root = Path(r"B:\\_repositorios")
json_path = Path(r"B:\\_repositorios\\pyro\\src\\snapshot\\snapshots\\_repositorios_2025-12-22-15-32.json")

with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

files = data["files"]
dirs = data["dirs"]

keywords = {"skybridge", "sky-bridge", "sky_bridge", "sky", "bridge"}

def depth_of(rel_path):
    if not rel_path:
        return 0
    return len(rel_path.split("\\"))

candidates = []
for d in dirs:
    name = d.get("name") or ""
    if name.lower() in keywords and depth_of(d["path"]) <= 5:
        candidates.append(d["path"])

candidates = sorted(set(candidates))

def in_subtree(file_path, candidate_path):
    if file_path == candidate_path:
        return False
    prefix = candidate_path + "\\"
    return file_path.startswith(prefix)


def readme_mentions_skybridge(paths):
    hits = []
    for rel in paths:
        if not os.path.basename(rel).lower().startswith("readme"):
            continue
        abs_path = root / rel
        try:
            content = abs_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            try:
                content = abs_path.read_text(encoding="latin-1", errors="ignore")
            except Exception:
                content = ""
        if re.search(r"skybridge", content, re.IGNORECASE):
            hits.append(rel)
    return hits

results = []
for cand in candidates:
    cand_files = [f for f in files if in_subtree(f["path"], cand)]
    cand_dirs = [d for d in dirs if in_subtree(d["path"], cand)]

    count_py = sum(1 for f in cand_files if f["name"].lower().endswith(".py"))
    count_md = sum(1 for f in cand_files if f["name"].lower().endswith(".md"))
    count_toml = sum(1 for f in cand_files if f["name"].lower().endswith(".toml"))
    count_txt = sum(1 for f in cand_files if f["name"].lower().endswith(".txt"))
    count_yml = sum(1 for f in cand_files if f["name"].lower().endswith(".yml") or f["name"].lower().endswith(".yaml"))
    count_json = sum(1 for f in cand_files if f["name"].lower().endswith(".json"))

    has_skybridge_dir = any(d["name"].lower() == "skybridge" for d in cand_dirs)
    has_modules_skybridge = any(d["path"].lower().endswith("modules\\skybridge") for d in cand_dirs)
    has_src_skybridge = any(d["path"].lower().endswith("src\\skybridge") for d in cand_dirs)
    has_cli = any(os.path.basename(f["name"]).lower() in ("__main__.py", "cli.py") for f in cand_files)

    readme_hits = readme_mentions_skybridge([f["path"] for f in cand_files if f["name"].lower().startswith("readme")])
    has_readme_hit = len(readme_hits) > 0

    has_openapi = any("openapi" in f["name"].lower() for f in cand_files)
    has_workflows = any("\\.github\\workflows\\" in f["path"].lower() for f in cand_files)

    has_route = any(re.search(r"route|router", f["name"], re.IGNORECASE) for f in cand_files)
    has_message = any(re.search(r"message|msg", f["name"], re.IGNORECASE) for f in cand_files)
    has_file = any(re.search(r"file", f["name"], re.IGNORECASE) for f in cand_files)

    score = 0
    score += count_py * 3
    score += count_md * 2
    score += (count_toml + count_txt) * 2
    score += (count_yml + count_json) * 1

    strong_markers = []
    if has_skybridge_dir or has_modules_skybridge or has_src_skybridge:
        score += 10
        strong_markers.append("skybridge_dir")
    if has_readme_hit:
        score += 8
        strong_markers.append("readme_skybridge")
    if has_cli:
        score += 5
        strong_markers.append("cli")
    if has_openapi or has_workflows:
        score += 3
        strong_markers.append("openapi/workflows")

    total_files = len(cand_files)
    penalty_generic = 0
    penalty_dense = 0
    if not strong_markers:
        score -= 10
        penalty_generic = -10
    if total_files >= 500 and len(strong_markers) <= 1:
        score -= 5
        penalty_dense = -5

    results.append({
        "path": cand,
        "score": score,
        "counts": {
            "py": count_py,
            "md": count_md,
            "toml": count_toml,
            "txt": count_txt,
            "yml": count_yml,
            "json": count_json,
        },
        "markers": {
            "skybridge_dir": has_skybridge_dir,
            "modules_skybridge": has_modules_skybridge,
            "src_skybridge": has_src_skybridge,
            "readme_hits": readme_hits,
            "cli": has_cli,
            "openapi": has_openapi,
            "workflows": has_workflows,
        },
        "penalties": {
            "generic": penalty_generic,
            "dense": penalty_dense,
        },
        "domains": {
            "route": has_route,
            "message": has_message,
            "file": has_file,
        },
        "total_files": total_files,
    })

results.sort(key=lambda x: x["score"], reverse=True)

out_dir = Path(r"B:\\_repositorios\\skybridge\\.agents")
out_dir.mkdir(parents=True, exist_ok=True)
report_path = out_dir / "task000-discovery-report.md"

lines = []
lines.append("# TASK000 - Discovery Skybridge (Snapshot + Score)")
lines.append("")
lines.append("## Escopo e metodo")
lines.append("- Root: B:\\_repositorios")
lines.append("- Profundidade maxima: 5 (snapshot)")
lines.append("- Coleta: nomes de pastas/arquivos e extensoes; leitura apenas de README* quando necessario")
lines.append("- Pesos (PB000): .py=+3, .md=+2, .toml/.txt=+2, .yml/.yaml/.json=+1")
lines.append("- Bonus: skybridge dir / modules/skybridge / src/skybridge (+10), README citando Skybridge (+8), CLI (__main__.py/cli.py) (+5), openapi/workflows (+3)")
lines.append("- Penalidades: entidade generica sem marcador forte (-10), alta contagem com baixa densidade de marcadores (-5)")
lines.append("")
lines.append("## Ranking de entidades (score)")
for i, r in enumerate(results, 1):
    lines.append(f"{i}) {root / r['path']} -> {r['score']}")
lines.append("")
lines.append("## Evidencias por entidade")
for r in results:
    lines.append("")
    lines.append(f"### {root / r['path']} (score {r['score']})")
    c = r["counts"]
    lines.append(f"- Contagens: .py={c['py']} .md={c['md']} .toml={c['toml']} .txt={c['txt']} .yml/.yaml={c['yml']} .json={c['json']}")
    m = r["markers"]
    strong = []
    if m["skybridge_dir"] or m["modules_skybridge"] or m["src_skybridge"]:
        strong.append("pasta skybridge/modules/skybridge/src/skybridge")
    if m["readme_hits"]:
        strong.append("README menciona Skybridge")
    if m["cli"]:
        strong.append("CLI (__main__.py/cli.py)")
    if m["openapi"] or m["workflows"]:
        strong.append("openapi/workflows")
    lines.append(f"- Marcadores fortes: {', '.join(strong) if strong else 'nenhum'}")
    lines.append(f"- CLI: {'sim' if m['cli'] else 'nao'}")
    lines.append(f"- Integracoes: openapi={'sim' if m['openapi'] else 'nao'}, workflows={'sim' if m['workflows'] else 'nao'}")
    if m["readme_hits"]:
        lines.append("- README hits:")
        for h in m["readme_hits"][:10]:
            lines.append(f"  - {root / h}")
    if r["penalties"]["generic"] or r["penalties"]["dense"]:
        lines.append(f"- Penalidades: generic={r['penalties']['generic']} dense={r['penalties']['dense']}")

lines.append("")
lines.append("## Recomendacoes acionaveis")
if results:
    lines.append(f"- Nucleo provavel: {root / results[0]['path']} (maior score)")
    if len(results) > 1:
        lines.append(f"- Implementacoes paralelas/abandono: {root / results[1]['path']}")
    frag = [r for r in results if r["markers"]["readme_hits"]]
    if frag:
        lines.append(f"- Fragmentos reaproveitaveis: {root / frag[0]['path']} (docs com Skybridge)")
lines.append("")
lines.append("## Tabela comparativa (resumo)")
lines.append("| Entidade | Score | Codigo (.py) | Docs (.md) | Config (.toml/.txt) | Infra/API (.yml/.yaml/.json) | CLI | Snapshot/Diff | Dominios detectados | Integracoes |")
lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |")
for r in results:
    c = r["counts"]
    infra = c["yml"] + c["json"]
    config = c["toml"] + c["txt"]
    doms = []
    if r["domains"]["file"]:
        doms.append("file")
    if r["domains"]["route"]:
        doms.append("rota")
    if r["domains"]["message"]:
        doms.append("mensagem")
    doms_str = ",".join(doms) if doms else "nenhum"
    integ = []
    if r["markers"]["openapi"]:
        integ.append("openapi")
    if r["markers"]["workflows"]:
        integ.append("workflows")
    integ_str = ",".join(integ) if integ else "-"
    lines.append(f"| {root / r['path']} | {r['score']} | {c['py']} | {c['md']} | {config} | {infra} | {'sim' if r['markers']['cli'] else 'nao'} | nao | {doms_str} | {integ_str} |")

report_path.write_text("\n".join(lines), encoding="utf-8")
print(str(report_path))
