"""면제 원장 갱신 — item47 스코프 결함 수정에 따른 두 가지 (2026-08-24 iter-3).

① KR0068 2025.2Q **해제**. 등재사유("발행사 잔차, 인과 미규명 — owner 가 오차 용인")가
   반증됐다: 원인은 발행사가 아니라 우리 룰의 `item47` 스코프 가정이었고, 룰을 고치자 다리가
   잔차 0.26 으로 닫힌다. 게이트 registry 에서 뺐으므로 이 기록은 고아가 된다 —
   `status=CONTRADICTED` 로 남겨 두면 같은 (회사,분기)가 다시 등재되는 순간 게이트가
   `EXEMPTION_CITATION_CONTRADICTED` RED 를 띄운다(이 저장소의 확립된 해제 관행).

② KR0075 2024.3Q·2024.4Q·2025.1Q **박제잔차 갱신**. 마스터 셀은 한 칸도 안 움직였다.
   룰이 기대값을 재는 식이 EXCL → INCL 로 바뀌어 잔차가 이동했을 뿐이다. 종전 값은
   `expected_residual_alt_reading` 에 남긴다(KR0068 이 만든 선례) — 안 남기면 다음 세션이
   "박제값이 등재 기록과 다르다"로 읽고 되돌린다.

재현: python scripts/fix_20260824_i47_scope_ledger.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"

_WHY_SCOPE = (
    "2026-08-24 iter-3: 룰 `_tier2_branch` 가 회사별 item47 스코프를 인식하도록 고쳐졌다"
    "(`kics_json_rules._tier2_i47_scope_map`). KR0075 는 자기 결정적 버킷 18표가 전부 INCL "
    "(EXCL 0) 이라 INCL 사로 판정된다 — item47 이 item49(해약환급금 초과분)를 포함해 인쇄되고 "
    "한도는 나머지 채무성 자본(item47 − item49)에만 걸린다. 기대값이 "
    "`min(item47, item48) + item49` 에서 `min(item47 − item49, item48) + item49` 로 바뀌면서 "
    "잔차가 이동했다. **마스터 값은 한 칸도 안 바뀌었다**(박제 cells 가 그대로 통과한다) — "
    "면제의 대상인 발행사 자기모순은 그대로이고 측정자만 정확해졌다. 새 값이 더 정직하다는 "
    "방증: 구성 잔차가 다리 잔차와 같은 값으로 수렴한다(2024.3Q +14.86 vs 다리 +15 · "
    "2024.4Q +87.22 vs 다리 +87). 종전 −221/−242 는 서로 다른 두 불일치가 있는 것처럼 "
    "보이게 했지만 실제로는 하나다. 스코프 판정은 item47 ≠ item48 인 나머지 9분기에서 나오므로 "
    "`TIER2_DUPLICATE_ROW` 로 이미 플래그된 이 세 분기에 기대고 있지 않다 "
    "(scripts/_probes/probe_20260824_kr0075_scope_evidence.py)."
)

_NEW_PINS = {
    ("KR0075", "2024.3Q"): {"3_tier2_composition|적용전": 14.86,
                            "51_tfi_tier2_composition|적용전": 14.53},
    ("KR0075", "2024.4Q"): {"3_tier2_composition|적용전": 87.22,
                            "51_tfi_tier2_composition|적용전": 86.75},
    ("KR0075", "2025.1Q"): {"3_tier2_composition|적용전": 61.41,
                            "51_tfi_tier2_composition|적용전": 61.19},
}


def main() -> None:
    orig = LEDGER.read_text(encoding="utf-8", newline="")
    d = json.loads(orig)
    # 원장은 indent=2 + CRLF 로 저장돼 있다. 포맷이 바뀌면 diff 가 전체 파일이 되어
    # 무엇이 실제로 달라졌는지 리뷰가 불가능해진다 — round-trip 을 먼저 확인한다.
    assert json.dumps(d, ensure_ascii=False, indent=2).replace("\n", "\r\n") == orig, (
        "원장 포맷이 indent=2/CRLF 가 아니다 — 쓰기 전에 포맷을 다시 확인하라")
    touched = []
    for e in d["entries"]:
        if e.get("registry") != "_TIER2_ISSUER_INCONSISTENT":
            continue
        key = (e.get("company"), e.get("quarter"))

        if key == ("KR0068", "2025.2Q"):
            e["status"] = "CONTRADICTED"
            e["refuted_by"] = (
                "validation 2026-08-24 iter-2 (인과 규명) + iter-3 (룰 수정·해제). "
                "raw 대조 근거는 티켓 "
                "inbox/_resolved/20260824T0410Z__validation__KR0068_2025.2Q__"
                "tier1_bridge_residual_unexplained.md §답변 iter-2."
            )
            e["resolved_note"] = (
                "2026-08-24 해제. 등재사유는 '발행사가 만든 잔차인데 인과를 모른다' 였고 "
                "owner 가 원문을 보고 오차를 용인해 `VERIFIED_BY_OWNER` 로 등재됐다. "
                "**그 전제가 반증됐다** — 잔차 −30,095 는 발행사가 만든 값이 아니라 우리 룰이 "
                "만든 값이었다. 한화생명은 item47 에 item49 를 포함해 인쇄하는데(INCL) 룰이 "
                "item47 을 채무성 자본만이라고 가정해 한도초과를 item49 만큼(69,995.55) "
                "과대계산했고, 2025.2Q 는 이 회사에서 한도가 실제로 구속한 유일한 분기라 그 "
                "과대값이 다리에 그대로 들어갔다. 룰을 스코프 인식으로 고치자 한도초과가 "
                "70,821.29 → 825.74 로 내려가고 "
                "213,475 − (30,921 − 825.74) − 100,874 = 82,505.74 vs 인쇄 82,506 = **잔차 "
                "0.26** 으로 닫힌다(tol 2.0). 게이트가 `TIER2_EXEMPTION_INERT` 로 먼저 "
                "'등재를 풀어라' 를 인쇄했고 그에 따라 registry 에서 뺐다. 기록을 지우지 않는 "
                "이유: 같은 (회사,분기)가 다시 면제로 등재되면 status=CONTRADICTED 가 즉시 "
                "RED 를 띄운다 — 반증된 사유가 조용히 되살아나는 경로를 막는다. "
                "**owner 판단이 틀렸다는 뜻이 아니다**: owner 는 '원문이 그렇게 적혀 있다' 를 "
                "확인한 것이고 그건 지금도 참이다. 틀린 것은 그 원문을 읽는 우리 식이었다."
            )
            touched.append("KR0068 2025.2Q -> CONTRADICTED (해제)")
            continue

        if key in _NEW_PINS:
            old = dict(e.get("expected_residual") or {})
            new = dict(old)
            new.update(_NEW_PINS[key])
            e["expected_residual"] = new
            e["expected_residual_alt_reading"] = {
                **{k: v for k, v in old.items() if k in _NEW_PINS[key]},
                "_why": (
                    "2026-08-24 이전(EXCL 읽기) 값. " + _WHY_SCOPE
                ),
            }
            e["note"] = (e.get("note", "") + " ").strip() + " ⚠️ " + _WHY_SCOPE
            touched.append(f"{key[0]} {key[1]} pins {old} -> {new}")

    out = json.dumps(d, ensure_ascii=False, indent=2).replace("\n", "\r\n")
    LEDGER.write_text(out, encoding="utf-8", newline="")
    assert LEDGER.read_bytes()[:3] != b"\xef\xbb\xbf", "BOM 이 붙었다"
    json.loads(LEDGER.read_text(encoding="utf-8"))  # 구조 재검증
    for t in touched:
        print("  " + t)
    print(f"wrote {LEDGER} ({len(touched)} entries touched)")


if __name__ == "__main__":
    main()
