"""Insurer search names for FSC bond API bondIsurNm filter."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class InsurerRef:
    code: str
    dirname: str
    search_names: tuple[str, ...]


def _dirname_label(dirname: str) -> str:
    if "_" in dirname:
        return dirname.split("_", 1)[1]
    return dirname


def load_insurer_refs(repo_root: Path) -> list[InsurerRef]:
    paths = [
        repo_root / "src" / "solvency" / "downloader" / "life_insurer_registry.yaml",
        repo_root / "src" / "solvency" / "downloader" / "nonlife_insurer_registry.yaml",
    ]
    refs: list[InsurerRef] = []
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for entry in data.get("insurers", []):
            code = entry["code"]
            dirname = entry["dirname"]
            names: list[str] = []
            label = _dirname_label(dirname)
            names.append(label)
            for alias in entry.get("aliases", []):
                if alias and alias not in names:
                    names.append(alias)
            refs.append(InsurerRef(code=code, dirname=dirname, search_names=tuple(names)))
    return refs


def match_insurer_code(bond_isur_nm: str, refs: list[InsurerRef]) -> str | None:
    if not bond_isur_nm:
        return None
    best: tuple[int, str] | None = None
    for ref in refs:
        for name in ref.search_names:
            if name in bond_isur_nm or bond_isur_nm in name:
                score = len(name)
                if best is None or score > best[0]:
                    best = (score, ref.code)
    return best[1] if best else None
