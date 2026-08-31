"""Generate/merge data/_derived/_patch_2026q2_<code>.json for the 16 life companies,
using the resolved values in _life16_final_values.json. Item labels are copied
programmatically from the SAME company's 2026.1Q (or 2026.2Q, whichever has the item)
master row -- never hand-typed (avoids the interpunct/dot-glyph mismatch trap).

Merge policy: if a patch file already exists, APPEND new cells for item numbers not
already present in it (never overwrite an existing cell in that file). If no file
exists, create it fresh with schema matching _patch_2026q2_KR1000.json.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

CODE, QUARTER, ITEM = "원보험사코드", "공시분기", "항목번호"
VAL, VAL_POST, NAME = "값", "값_적용후", "항목명"

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
label = {}  # (code, item) -> name. Prefer the SAME (2026.2Q) row -- that row already
# EXISTS for every target item (census requires 값(전) present), so its label is both
# the exact-match apply_2026q2_patches.py requires and a programmatic (non-hand-typed)
# copy. Fall back to 2026.1Q only if a 2026.2Q row genuinely doesn't exist yet.
for q_pref in ("2026.2Q", "2026.1Q"):
    for r in records:
        c, q, it = r.get(CODE), r.get(QUARTER), r.get(ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if q == q_pref and (c, it) not in label:
            label[(c, it)] = r.get(NAME)
for r in records:  # any remaining
    c, q, it = r.get(CODE), r.get(QUARTER), r.get(ITEM)
    try:
        it = int(it)
    except (TypeError, ValueError):
        continue
    if (c, it) not in label:
        label[(c, it)] = r.get(NAME)

final = json.loads((ROOT / "scripts" / "_probes" / "_life16_final_values.json").read_text(encoding="utf-8"))

REASON_TEXT = {
    "mirror(universal, no axis targets this leg)": "일반손해(18)/신용(20)/운영(21)위험은 K-ICS 경과조치 7종 어느 축도 대상으로 하지 않는다(TIR=생명장기, TER/TIRR=시장, TAC/TFI=가용자본만 대상) — 마스터 전체 회사·분기 census로 item18=0 예외 0건 재확인. 값_적용후=값 미러링.",
    "mirror(TIR=X confirmed 2026.2Q)": "data/_derived/kics_transition_applicability.json 2026.2Q 레코드에서 TIR=X 확인(요구자본측 생명장기 경과조치 미적용) → 값_적용후=값.",
    "mirror(TER=X,TIRR=X confirmed 2026.2Q)": "data/_derived/kics_transition_applicability.json 2026.2Q 레코드에서 TER=X·TIRR=X 확인(시장위험 관련 경과조치 둘 다 미적용) → 값_적용후=값.",
    "mirror(pre=0)": "값(적용전)=0이므로 값_적용후도 0(어떤 경과조치도 0을 실질변경시키지 않음, 대시/0 컨벤션 일관).",
    "mirror(TIR=TER=TIRR=X)": "요구자본측 3개 경과조치 축(TIR/TER/TIRR) 전부 X 확인 → 법인세조정액/기타요구자본은 요구자본 산출의 파생항목이라 세 축 모두 비활성이면 불변. 값_적용후=값.",
    "mirror(TFI=X,TAC=X)": "가용자본측 2개 경과조치 축(TFI/TAC) 전부 X 확인 → 기본자본/보완자본 재분류·증액 효과 없음. 값_적용후=값.",
}


def fmt(x):
    r = round(x, 4)
    if abs(r - round(r)) < 1e-9:
        return str(int(round(r)))
    s = f"{r:.4f}".rstrip("0").rstrip(".")
    return s


for code, items in final.items():
    if not items:
        continue
    patch_path = ROOT / "data" / "_derived" / f"_patch_2026q2_{code}.json"
    if patch_path.exists():
        data = json.loads(patch_path.read_text(encoding="utf-8"))
        existing_items = {c.get("항목번호") for c in data.get("cells", [])}
    else:
        data = {"company_code": code, "quarter": "2026.2Q", "cells": [], "notes": "", "unfixable": []}
        existing_items = set()

    added = []
    for it_str, info in sorted(items.items(), key=lambda kv: int(kv[0])):
        it = int(it_str)
        if it in existing_items:
            print(f"  SKIP {code} item{it}: already in patch file (merge policy: don't overwrite)")
            continue
        val = info["value"]
        reason_key = info["reason"]
        if reason_key.startswith("RAW:"):
            basis = reason_key[4:]
        elif reason_key in REASON_TEXT:
            basis = REASON_TEXT[reason_key]
        elif reason_key.startswith("derive"):
            basis = ("파생 산출(게이트 자체 항등식과 동일 공식, src/solvency/validation/kics_json_rules.py import 검산): "
                      + reason_key)
        elif reason_key.startswith("copy"):
            basis = "같은 표(공통적용경과조치 TFI표)의 대응 항목에서 그대로 복사: " + reason_key
        elif reason_key.startswith("mirror(parent"):
            basis = "상위항목(item17 또는 item19)이 미러/무경과조치로 확정되어 하위 census 완결을 위해 같은 원리로 미러: " + reason_key
        else:
            basis = reason_key
        item_name = label.get((code, it), f"item{it}")
        cell = {
            "항목번호": it,
            "항목명": item_name,
            "값": None,
            "값_적용후": fmt(val),
            "근거": f"POST_TRANSITION_PARENT/CHILD_MISSING 해소(2026-09-01 세션, 값_적용후만 채움, 값(적용전)은 기존 마스터에 이미 있어 건드리지 않음). {basis}",
        }
        data["cells"].append(cell)
        added.append(it)

    if added:
        note_add = f" || [2026-09-01 POST_TRANSITION 해소] items {added} 값_적용후 신규(16개 생보사 라운드, 상세근거는 각 셀 근거 필드)."
        data["notes"] = (data.get("notes") or "") + note_add
        patch_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"WROTE {patch_path.name}: +{len(added)} cells {added}")
    else:
        print(f"NOCHANGE {code}: nothing to add")
