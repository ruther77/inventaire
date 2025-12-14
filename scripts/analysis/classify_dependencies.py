#!/usr/bin/env python3
"""Analyse automatique du repo : classification et graphe de dépendances pondéré."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ["backend", "core", "frontend", "newCMS", "monprojet", "scripts", "docs"]
SEARCH_EXTS = [".py", ".js", ".ts", ".tsx", ".jsx"]
CLASS_TAGS = {"#USÉ", "#DEPRECATED", "#WORK_IN_PROGRESS"}


def read_first_lines(path: Path, limit: int = 8) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()[:limit]
    except OSError:
        return []


def classify(path: Path) -> str:
    lines = read_first_lines(path)
    for line in lines:
        trimmed = line.strip()
        for tag in CLASS_TAGS:
            if tag in trimmed:
                return tag

    lowered = str(path).lower()
    if "deprecated" in lowered or "legacy" in lowered:
        return "#DEPRECATED"
    if "wip" in lowered or "todo" in lowered:
        return "#WORK_IN_PROGRESS"
    return "#USÉ"


def possible_targets(module: str, source: Path) -> list[Path]:
    module = module.strip()
    if not module or module.startswith("http") or module.startswith(("node:", "@")):
        return []

    if module.startswith("."):
        candidate = (source.parent / module).resolve()
    elif module.startswith("/"):
        candidate = (ROOT / module.lstrip("/")).resolve()
    else:
        candidate = (ROOT / module.replace(".", "/")).resolve()

    targets: list[Path] = []
    for ext in SEARCH_EXTS:
        candidate_with_ext = candidate.with_suffix(ext)
        if candidate_with_ext.exists():
            targets.append(candidate_with_ext)
    if candidate.is_dir():
        for index in ("index", "__init__"):
            for ext in SEARCH_EXTS:
                entry = (candidate / f"{index}{ext}")
                if entry.exists():
                    targets.append(entry)
    return targets


IMPORT_PATTERNS = [
    re.compile(r"from\s+([^\s]+)\s+import"),
    re.compile(r"import\s+[^\s,]+\s+from\s+[\"']([^\"']+)[\"']"),
    re.compile(r"import\s+([^\s,]+)"),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
]


def extract_modules(line: str) -> list[str]:
    modules: list[str] = []
    for pattern in IMPORT_PATTERNS:
        for match in pattern.findall(line):
            modules.append(match)
    return modules


def build_graph() -> None:
    files: list[Path] = []
    for base in SCAN_DIRS:
        root_dir = ROOT / base
        if not root_dir.exists():
            continue
        files.extend([p for p in root_dir.rglob("*") if p.is_file()])

    classifications: dict[str, str] = {}
    file_sizes: dict[str, int] = {}
    edges: defaultdict[tuple[str, str], float] = defaultdict(float)

    for path in files:
        rel = str(path.relative_to(ROOT))
        classifications[rel] = classify(path)
        try:
            file_sizes[rel] = max(1, path.stat().st_size)
        except OSError:
            file_sizes[rel] = 1

        if path.suffix not in SEARCH_EXTS:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in text:
            for module in extract_modules(line):
                targets = possible_targets(module, path)
                for target in targets:
                    dest_rel = str(target.relative_to(ROOT))
                    weight_kb = max(1.0, file_sizes.get(dest_rel, 1) / 1024)
                    edges[(rel, dest_rel)] += weight_kb

    summary_path = ROOT / "reports" / "classification_summary.md"
    summary_path.parent.mkdir(exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as summary:
        summary.write("# Classification automatique\n\n")
        counts = Counter(classifications.values())
        for tag in sorted(CLASS_TAGS):
            summary.write(f"- `{tag}` : {counts.get(tag, 0)} fichiers\n")
        summary.write("\n## Top dépendances pondérées\n")
        sorted_edges = sorted(edges.items(), key=lambda item: -item[1])[:20]
        for (src, dest), weight in sorted_edges:
            summary.write(f"- `{src}` → `{dest}` (poids ≈ {weight:.1f} KB)\n")

    dot_path = ROOT / "reports" / "dependency_graph.dot"
    with dot_path.open("w", encoding="utf-8") as dot:
        dot.write("digraph dependencies {\n")
        dot.write("  rankdir=LR;\n")
        nodes = set(file_sizes.keys())
        for node in nodes:
            tag = classifications.get(node, "#USÉ")
            size = file_sizes.get(node, 0) / 1024
            label = node.replace('"', '\\"')
            dot.write(
                f'  "{label}" [label="{label}\\n{tag}\\n{size:.1f} KB"];\n'
            )
        for (src, dest), weight in edges.items():
            width = min(10.0, max(1.0, weight / 200))
            dot.write(
                f'  "{src}" -> "{dest}" [penwidth={width:.2f}, weight={weight:.1f}];\n'
            )
        dot.write("}\n")

    print("Rapport généré :")
    print(f"- {summary_path}")
    print(f"- {dot_path}")


if __name__ == "__main__":
    build_graph()
