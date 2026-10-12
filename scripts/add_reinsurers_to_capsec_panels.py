# -*- coding: utf-8 -*-
"""재보사 8곳(KR1101~KR1108)을 K-ICS.html 하단 두 패널(자본성증권 소진율 도넛 · Forward Outlook)에 더한다.

## 왜 필요한가 (inbox/publishing/20261011T0410Z, owner 2026-10-11)

K-ICS.html 은 `kics_forward_capital.json`(Forward Outlook)과 `kics_tier{1,2}_utilization.json`(도넛)에서
**회사명 정확일치(+부분포함)** 로 행을 찾는다. 이 셋은 2026-09-01~09-23 에 만들어졌고, 재보사 8곳은
그 뒤(2026-10-09)에 마스터 `kics_disclosure.json` 에 들어왔다. 그래서 세 파일 어디에도 행이 없었고
화면은 「forward simulation 데이터 없음」·「데이터 없음」을 그렸다 (원인 = 데이터 부재, 이름 불일치 아님:
드롭다운 value 는 원수사명 전체이고 약칭은 라벨에만 쓴다).

## 이 스크립트가 하는 일 (모두 **추가만** — 기존 39사 행은 한 바이트도 안 건드린다)

1. `data/bonds/capital_securities_fy2026h1.json` 에 재보사 8곳의 **빈 레코드(bonds: [])** 를 더한다.
   게이트(`CAPSEC_COVERAGE_REGRESSION`)가 「소스에 회사 레코드가 없다 = 미검증」을 RED 로 보기 때문에,
   무발행이면 빈 레코드로 명시해야 「스캔 후 0」과 구분된다. 근거(경영공시 항목값)를 레코드 notes 에 적는다.
2. `output/tier{1,2}_utilization/*_20262Q.json` 과 배포본 `kics_tier{1,2}_utilization.json` 에 재보사 행을 더한다.
   행을 만들 때의 값은 임시다 - 최종값은 `apply_disclosure_utilization.py` 가 규정 근거 산식
   (`capital_utilization_rules.py`, 2026-10-12)으로 47사 전체를 다시 계산해 덮는다.
   재보사 특수사항(아래 REINSURER_NOTES) 은 행의 `reinsurer_basis` 필드에 근거와 함께 남긴다
   (apply 도 이 사전을 import 해 note 를 맞춘다).

## 재보사에서 공시값을 그대로 못 쓰는 두 경우 (지어내지 않고 비우거나 0 으로 두되 이유를 기록)

  · item6 이 음수: 스위스리 (3)억 = 자본항목 표의 마이너스 계정. 발행이 아니므로 분자는 0.
  · item47(보완자본 한도 적용 전)이 비었거나 모순:
      - 결측(뮌헨·퍼시픽라이프리·마이브라운): 보완자본(item3)=0 이고 한도(SCR x 50%)>0 이면
        한도 적용 전 금액도 0 이다(한도에 걸려 줄어든 부분이 없다는 뜻) -> 0.
      - RGA 5,499: 같은 표에서 보완자본 0 · 한도 0 인데 한도 적용 전만 5,499 = 지급여력금액과 같은 값.
        보완자본 항목이 아니라 발행사가 칸을 잘못 채운 것으로 보고 0 으로 둔다(원값은 note 에 보존).
      - 스위스리: 보완자본(item3) 4,274억은 전액 해약환급금 부족분 상당액 중 해약환급금준비금 상당액
        초과분이라 [별표22] Ⅲ.2.마 단서로 한도 계산 대상이 0 이다. 한도 적용 전 인쇄값 0 을 그대로 써
        **0.0** 으로 둔다(2026-10-12 owner 결정 ⑤ — 종전 'numerator_undisclosed' 빈 칸 경로는 없앴다).

## 이 스크립트는 행을 **만들기만** 한다 (2026-10-12)

소진율 값의 정본은 `scripts/apply_disclosure_utilization.py`(규정 근거 산식, `capital_utilization_rules.py`)다.
이 스크립트로 행을 새로 만들었으면 그 뒤에 apply 를 돌려 47사 전체를 같은 산식으로 덮는다.

## 실행

  python scripts/add_reinsurers_to_capsec_panels.py            # dry-run (진단만)
  python scripts/add_reinsurers_to_capsec_panels.py --apply    # 반영 (기존 파일은 --backup-dir 로 복사)

이 스크립트 뒤에 forward 빌더를 같은 인자로 돌린다(기존 행 불변 검증은 별도 스크립트
`scripts/_tmp_verify_forward_existing_rows.py` 대신 runlog 의 명령 참고):
  python scripts/forward_capital_simulation.py --baseline-quarter 2026.2Q --tier-quarter 2026.2Q \
      --bonds-source data/bonds/capital_securities_fy2026h1.json

`build_capital_securities_fy2026h1.py` 는 파일을 통째로 다시 쓰므로, 그 빌더를 다시 돌리면 1번 레코드가
사라진다 — 돌린 뒤 이 스크립트를 한 번 더 `--apply` 하면 된다(멱등).
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

QUARTER = "2026.2Q"
AS_OF = "2026-06-30"
CODES = ["KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"]
TIER1_RATE = 0.15
TIER2_RATE = 0.50

KICS = ROOT / "kics_disclosure.json"
BONDS = ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json"
T1_DEPLOY = ROOT / "kics_tier1_utilization.json"
T2_DEPLOY = ROOT / "kics_tier2_utilization.json"
T1_OUT = ROOT / "output" / "tier1_utilization" / "tier1_utilization_20262Q.json"
T2_OUT = ROOT / "output" / "tier2_utilization" / "tier2_utilization_20262Q.json"

# 재보사별 근거. 원문(md_inbox/FY2026_Q2/<code>_*.md)을 직접 읽어 확인한 것만 적는다.
REINSURER_NOTES = {
    "KR1101": {"t2": "zero_derived", "why":
        "신종자본증권 0 · 보완자본 0. 경과조치표의 '보완자본 한도 적용 전'·'기발행' 칸이 공란이라 item47 이 마스터에 없다 -> "
        "보완자본 0 이고 한도>0 이므로 한도 적용 전도 0 으로 도출."},
    "KR1102": {"t2": "zero_disclosed", "why":
        "신종자본증권 '-' · 보통주 이외의 자본증권 (3)억(마이너스 계정, 발행 아님) · 기발행 신종/후순위 '-'. 보완자본 4,274억(= "
        "'보완자본으로 재분류하는 항목' 4,274억)은 전액 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분(감사 K-ICS 상세 Ⅲ.3)"
        "이고 경과조치 표 '보완자본 한도 적용 전'은 0(대시)이다 - [별표22] Ⅲ.2.마 단서로 한도 계산 대상이 0 이라 보완자본 소진율 0% "
        "(2026-10-12 owner 결정 ⑤, 종전 '확정 불가 -> 빈 칸' 해제. 항목 49 는 채우지 않는다). 기본자본 자본증권 소진율은 0%."},
    "KR1103": {"t2": "zero_disclosed", "why":
        "신종자본증권 '-' · 기발행 신종/후순위 '-' · 보완자본 공란/'-'. 마스터 item47=0."},
    "KR1104": {"t2": "zero_disclosed", "why":
        "신종자본증권 '-' · 보통주 이외의 자본증권 0 · 보완자본 0 · 기발행 신종/후순위 0 · 후순위채권 '-' · 신종자본증권 '-'. 마스터 item47=0."},
    "KR1105": {"t2": "zero_issuer_cell_inconsistent", "why":
        "신종자본증권 '-' · 보통주 이외의 자본증권 0 · 보완자본 0 · 기발행 칸 공란. 경과조치표 '보완자본 한도 적용 전' 5,499억은 같은 표의 "
        "지급여력금액(5,499)과 같은 값인데 보완자본·보완자본 한도는 0 이라 발행사가 칸을 잘못 채운 것으로 본다 -> 0 으로 두고 원값은 "
        "item47_raw 에 보존."},
    "KR1106": {"t2": "zero_disclosed", "why":
        "신종자본증권 0 · 기발행 신종/후순위 0 · 보완자본 0. 마스터 item47=0. 요구자본 경과조치 적용사(item14 값 3,897 > 값_적용후 3,627.26)."},
    "KR1107": {"t2": "zero_derived", "why":
        "신종자본증권 0 · 보통주 이외의 자본증권 0 · 보완자본 0 · 기발행 신종/후순위 0 · 한도 적용 전 0(원문). 마스터에 item47 이 없어 "
        "보완자본 0 + 한도>0 으로 0 도출(원문 표값과 일치)."},
    "KR1108": {"t2": "zero_derived", "why":
        "신종자본증권 '-' · 보통주 이외의 자본증권 '-' · 보완자본 '-' · 한도 적용 전 '-' · 기발행 '-'. 마스터에 item47 이 없어 보완자본 0 + 한도>0 으로 0 도출."},
}


def _f(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_items():
    out = {c: {} for c in CODES}
    for r in json.loads(KICS.read_text(encoding="utf-8")):
        if r.get("공시분기") != QUARTER or r.get("원보험사코드") not in out:
            continue
        out[r["원보험사코드"]][int(r["항목번호"])] = _f(r.get("값"))
        out[r["원보험사코드"]]["name"] = r.get("원수사명")
    return out


# ---------- 포맷 보존 입출력: 기존 파일을 파싱->덤프했을 때 바이트가 같은 설정을 찾는다 ----------
def detect_fmt(path: Path):
    raw = path.read_bytes().decode("utf-8")
    doc = json.loads(raw)
    for indent in (2, 1):
        for nl in ("\r\n", "\n"):
            for tail in ("", nl):
                txt = json.dumps(doc, ensure_ascii=False, indent=indent)
                txt = txt.replace("\n", nl) + tail
                if txt == raw:
                    return doc, dict(indent=indent, nl=nl, tail=tail)
    raise SystemExit(f"[FATAL] 라운드트립 불가(포맷 미상): {path}")


def write_fmt(path: Path, doc, fmt):
    txt = json.dumps(doc, ensure_ascii=False, indent=fmt["indent"]).replace("\n", fmt["nl"]) + fmt["tail"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(txt)


def bond_record(code, it):
    n = REINSURER_NOTES[code]
    return {
        "code": code,
        "company": it["name"],
        "as_of": AS_OF,
        "source_file": f"kics_disclosure.json ({QUARTER} item6/item47/item53/item54; 원문 md_inbox/FY2026_Q2/{code}_{it['name']}.md)",
        "has_capital_securities": False,
        "bs_hybrid_mn": 0,
        "bs_subordinated_mn": 0,
        "total_hybrid_outstanding_mn": 0,
        "total_subordinated_outstanding_mn": 0,
        "confidence": "medium",
        "bonds": [],
        "notes": ("재보사(2026-10-11 추가). DART per-bond 원천 없음 — K-ICS 경영공시 기준 무발행 확인. " + n["why"]),
    }


def tier_rows(code, it):
    n = REINSURER_NOTES[code]
    scr = it.get(14)
    item6, item47, item3 = it.get(6), it.get(47), it.get(3)
    t1_lim = round(scr * TIER1_RATE, 2)
    issued = 0.0 if (item6 is None or item6 <= 0) else round(item6, 2)
    t1 = {
        "company": it["name"], "code": code, "quarter": QUARTER, "scr_eok": scr,
        "tier1_hybrid_limit_eok": t1_lim,
        "tier1_hybrid_limit_strict_eok": round(scr * 0.10, 2),
        "tier1_hybrid_issued_eok": issued,
        "tier1_hybrid_excess_eok": None,
        "tier1_hybrid_recognized_eok": issued,
        "tier1_hybrid_overflow_eok": round(max(0.0, issued - t1_lim), 2),
        "utilization_pct": round(issued / t1_lim * 100, 1),
        "utilization_pct_strict": round(issued / (scr * 0.10) * 100, 1),
        "data_source": f"kics_disclosure item6 / (item14 x {TIER1_RATE:.0%})",
        "quality_flag": "ok", "issued_source": "disclosure_item6", "excess_source": "missing",
        "legacy_hybrid_transition_eok": 0.0,
        "tier1_grandfathered_hybrid_eok": it.get(53) or 0.0,
        "utilization_pct_raw": 0.0, "numerator_as_of": AS_OF,
        "hybrid_outstanding_eok": 0.0, "subordinated_outstanding_eok": 0.0, "bond_balance_as_of": None,
        "reinsurer_basis": {"item6_raw": item6, "note": n["why"]},
    }
    t2_lim = round(scr * TIER2_RATE, 2)
    kind = n["t2"]
    if kind == "zero_disclosed":
        num, util, qf = round(item47 or 0.0, 2), round((item47 or 0.0) / t2_lim * 100, 1), "ok"
    else:   # zero_derived / zero_issuer_cell_inconsistent: 보완자본(item3)=0 로부터 도출
        assert (item3 or 0.0) == 0.0, (code, item3)
        num, util, qf = 0.0, 0.0, ("ok" if kind == "zero_derived" else "issuer_item47_inconsistent")
    t2 = {
        "company": it["name"], "code": code, "quarter": QUARTER,
        "tier2_limit_eok": t2_lim, "numerator_eok": num, "utilization_pct": util,
        "data_source": "kics_disclosure item47 / (item14 x 50%)",
        "tier2_eok": item3, "pre_limit_eok": num, "lapse_excess_eok": None,
        "hybrid_eok": 0.0, "subordinated_eok": 0.0, "proxy_utilization_pct": None,
        "quality_flag": qf,
        "new_subordinated_recognized_eok": 0.0, "new_subordinated_gross_eok": 0.0,
        "tier1_overflow_into_tier2_eok": 0.0,
        "grandfathered_hybrid_eok": it.get(53) or 0.0, "grandfathered_subordinated_eok": it.get(54) or 0.0,
        "numerator_as_of": AS_OF if num is not None else None,
        "hybrid_outstanding_eok": 0.0, "subordinated_outstanding_eok": 0.0, "bond_balance_as_of": None,
        "reinsurer_basis": {"item47_raw": item47, "item3_raw": item3, "note": n["why"]},
    }
    if kind == "zero_issuer_cell_inconsistent":
        t2["reinsurer_basis"]["item47_raw_issuer_cell"] = 5499.0
    return t1, t2


def add_to(path: Path, fmt_doc, fmt, key, rows, id_key, backup_dir, apply):
    doc = copy.deepcopy(fmt_doc)
    have = {r[id_key] for r in doc[key]}
    new = [r for r in rows if r[id_key] not in have]
    if not new:
        print(f"  {path.relative_to(ROOT)}: 이미 재보사 행 있음 — 변경 없음")
        return
    doc[key].extend(new)
    if "count" in doc:
        doc["count"] = len(doc[key])
    if "n_companies" in doc:
        doc["n_companies"] = len(doc[key])
    print(f"  {path.relative_to(ROOT)}: +{len(new)}행 -> {len(doc[key])}")
    if apply:
        shutil.copy2(path, backup_dir / path.name)
        write_fmt(path, doc, fmt)


def main() -> int:
    # 2026-10-12: 모듈 최상위에서 main() 으로 옮겼다 - apply_disclosure_utilization.py 가 REINSURER_NOTES 를
    # import 하는데, import 만으로 호출자의 stdout 래퍼를 갈아끼우면 옛 래퍼가 GC 되며 버퍼를 닫는다.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--backup-dir", default=None)
    a = ap.parse_args()
    bdir = Path(a.backup_dir) if a.backup_dir else None
    if a.apply:
        if not bdir:
            raise SystemExit("--apply 는 --backup-dir 가 필요하다")
        bdir.mkdir(parents=True, exist_ok=True)

    items = load_items()
    for c in CODES:
        miss = [i for i in (1, 14) if items[c].get(i) is None]
        if miss:
            raise SystemExit(f"[FATAL] {c} 필수 항목 결측 {miss}")

    b_rows, t1_rows, t2_rows = [], [], []
    for c in CODES:
        b_rows.append(bond_record(c, items[c]))
        t1, t2 = tier_rows(c, items[c])
        t1_rows.append(t1)
        t2_rows.append(t2)
        print(f"  {c} {items[c]['name']:12s} T1 {t1['utilization_pct']}% (발행 {t1['tier1_hybrid_issued_eok']} / 한도 {t1['tier1_hybrid_limit_eok']}) "
              f"| T2 {t2['utilization_pct']}% ({t2['quality_flag']})")

    for path, key, rows, idk in ((BONDS, "companies", b_rows, "code"),
                                 (T1_DEPLOY, "results", t1_rows, "code"), (T1_OUT, "results", t1_rows, "code"),
                                 (T2_DEPLOY, "results", t2_rows, "code"), (T2_OUT, "results", t2_rows, "code")):
        doc, fmt = detect_fmt(path)
        add_to(path, doc, fmt, key, rows, idk, bdir, a.apply)
    if not a.apply:
        print("(dry-run; 파일 안 씀)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
