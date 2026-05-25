"""Shared helpers for 월납환산 premium / NB CSM multiple pipeline."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 십억원/month → 억원/month (1 십억 = 10억)
SIBEOK_TO_EOK = 10.0


def mn_krw_to_eok(mn: float | None) -> float | None:
    if mn is None:
        return None
    return round(float(mn) / 100.0, 4)


def sibeok_month_to_eok_month(sibeok: float | None) -> float | None:
    if sibeok is None:
        return None
    return round(float(sibeok) * SIBEOK_TO_EOK, 4)


def normalize_company(name: str) -> str:
    return re.sub(r"\s+", "", (name or "").strip())


def load_alias_map() -> dict[str, str]:
    """Map association / IR short names → IFRS17 company names."""
    aliases: dict[str, str] = {
        "DB손보": "DB손해보험",
        "DB손해보험": "DB손해보험",
        "현대해상": "현대해상",
        "현대해상화재보험": "현대해상",
        "삼성화재": "삼성화재해상보험",
        "삼성화재해상보험": "삼성화재해상보험",
        "한화생명": "한화생명",
        "삼성생명": "삼성생명",
        "메리츠화재": "메리츠화재해상보험",
        "메리츠화재해상보험": "메리츠화재해상보험",
    }
    for reg in (
        ROOT / "src/solvency/downloader/nonlife_insurer_registry.yaml",
        ROOT / "src/solvency/downloader/life_insurer_registry.yaml",
    ):
        if not reg.exists():
            continue
        try:
            import yaml
        except ImportError:
            break
        data = yaml.safe_load(reg.read_text(encoding="utf-8")) or {}
        for ins in data.get("insurers") or []:
            dirname = ins.get("dirname") or ""
            canonical = dirname.split("_", 1)[-1] if "_" in dirname else dirname
            if not canonical:
                continue
            aliases[normalize_company(canonical)] = canonical
            for a in ins.get("aliases") or []:
                aliases[normalize_company(a)] = canonical
    return aliases


def resolve_company(name: str, alias_map: dict[str, str]) -> str | None:
    key = normalize_company(name)
    if key in alias_map:
        return alias_map[key]
    for alias, canonical in alias_map.items():
        if alias in key or key in alias:
            return canonical
    return name if key else None
