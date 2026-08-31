"""Supplemental fix: KR0069 items 29,30,31,33,34 (값_적용후) -- the CHILD_MISSING gap that
build_20260901_life16_final.py's cascade logic missed (item17 was already mirrored in the
live master by a PRIOR session, not newly resolved by this one, so the "mirror children
when parent newly resolved as mirror" condition never fired for it). Same evidentiary
basis already documented in this company's own patch file for items 2/3: raw PDF p.18
'당사는 공통 및 선택 경과조치를 적용하지 않았습니다' -- explicit no-transition statement.
item17_후(133314) == item17_전(133314) exactly confirms this at the parent level too.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
name = {}
values = {}
for r in records:
    if r.get("원보험사코드") == "KR0069" and r.get("공시분기") == "2026.2Q":
        it = int(r.get("항목번호"))
        name[it] = r.get("항목명")
        values[it] = r.get("값")

targets = [29, 30, 31, 33, 34]
patch_path = ROOT / "data" / "_derived" / "_patch_2026q2_KR0069.json"
data = json.loads(patch_path.read_text(encoding="utf-8"))
existing = {c["항목번호"] for c in data["cells"]}

added = []
for it in targets:
    if it in existing:
        print(f"SKIP item{it}: already in patch file")
        continue
    data["cells"].append({
        "항목번호": it,
        "항목명": name[it],
        "값": None,
        "값_적용후": values[it],
        "근거": ("POST_TRANSITION_CHILD_MISSING 해소(2026-09-01 세션): 부모 item17_적용후(133314)가 "
                 "item17_적용전(133314)과 정확히 일치(이미 마스터에 존재, 이번 세션 미변경) — 이 patch 파일의 "
                 "item2/3 근거에 이미 기록된 raw PDF p.18 '당사는 공통 및 선택 경과조치를 적용하지 않았습니다' "
                 "명시 문장과 동일 근거로 생명장기 하위위험(29-35)도 비적용. item32는 값(전)=0(<5 material floor) "
                 "이라 census 미대상, item35는 이미 마스터에 존재(값_적용후=값 mirror 기존 반영)."),
    })
    added.append(it)

if added:
    data["notes"] = (data.get("notes") or "") + f" || [2026-09-01 CHILD_MISSING 보완] items {added} 값_적용후 신규 미러(item17 기존 mirror 확정에 따른 하위 census 완결)."
    patch_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {patch_path.name}: +{len(added)} cells {added}")
