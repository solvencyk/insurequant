# -*- coding: utf-8 -*-
"""KR0071(흥국생명) · KR0104(농협생명) 결합 경과조치 '적용후' 요구자본 체인 재구성.

판정: **우리 유도 오류** (발행사 자기모순 아님).

  원문(raw)에는 결합(②+③) 시나리오의 기본요구자본후(15)·분산효과후(16)·법인세조정액후(22)·
  기타요구자본후(23) 가 **인쇄돼 있지 않다.** 인쇄된 것은
    · 헤드라인 [지급여력비율 총괄]/4-2-3 의 지급여력금액후(1)·지급여력기준금액후(14)·비율후(27)
    · ② 표(장수·사업비·해지·대재해)의 생명장기후(17)+세부 29~35후
    · ③ 표(주식/금리)의 시장후(19)+세부 36~40후
    · ②·③ 각각의 기본요구자본후/법인세조정액후/기타요구자본후 — **단일 시나리오 값**
  마스터는 결합 헤드라인 14후 에 **②단독** 22후/23후 를 붙여 15후 를 역산해 두었다.
  22후/23후 는 시나리오마다 다르므로(흥국 ② 4,764.60 vs ③ 5,930.51) 그 가정이 거짓이고,
  그래서 15후 가 R4 재조합과 어긋났다(잔차 −1443 / −117 / +1209 / +909).

  R4 가 발행사 산식이라는 증거: 같은 문서의 **인쇄된 기본요구자본 8개 컬럼 전부**를
  ≤0.01억 으로 재현한다(2사 × 2분기 × {적용전, ②후, ③후}).

정정 방법 = 저장소 정본 methodology (scripts/rebuild_combined_transition_after.py docstring):
  15후 = sqrt(W'R4W) + 21후,  W=(17,18,19,20)후          ← 인쇄된 결합 leaf 로 재조합
  14후 = 그대로(원문 헤드라인 앵커, 변경 없음)
  23후 = KR0071: 관계회사(KR0005) 환산 = ratio × KR0005.14후  (ratio=14분기 중앙값 0.400607,
                 실측 스팬 0.400568~0.400628) / KR0104: 0 (전·②후·③후 전부 0 인쇄)
  22후 = 15후 + 23후 − 14후   (앵커 잔차)
  16후 = sum(17..21)후 − 15후

쓰기 전 정본 검사 4종 통과 확인 (아래 VERIFY 상수에 실측 박제):
  ① 적용전 leaf → R4 재현 = 표의 기본요구자본전 (≤0.01억)
  ② 표가 인쇄한 생명장기후·시장후를 R7·MARKET_M 이 재현 (≤0.001억)
  ③ 결합 15후·14후·16후·22후·23후 가 ②·③ 어느 단일표 값보다도 작다 (단조성)
  ④ 잔차 법인세후 ≥ 0 이고 법인세전의 1.2배 이내

셀 단위 UPSERT 만 한다. 통째 재작성·행 신설 없음. 동시 세션 보호를 위해 read→verify→write
사이에 파일 재판독 check-and-set 을 건다.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from solvency.validation.kics_json_rules import R4, _diversified_sqrt  # noqa: E402

TARGET = REPO / "kics_disclosure.json"
AFFILIATE_RATIO = 0.400607          # median of 14 quarters, span 0.400568~0.400628
# (회사, 분기) -> (원문 헤드라인 14후, 기타요구자본후 mode)
CASES = {
    ("KR0071", "2025.3Q"): ("AFFILIATE", 18781.0),
    ("KR0071", "2026.2Q"): ("AFFILIATE", 21790.0),
    ("KR0104", "2025.3Q"): ("ZERO", 17405.0),
    ("KR0104", "2026.2Q"): ("ZERO", 18865.0),
}
# 단조성 검사용 — raw 에서 직접 읽은 ②/③ 단일표 값 (억원)
SINGLE = {
    ("KR0071", "2025.3Q"): {"15": (17217.40, 20859.62), "14": (19578.92, 23700.97),
                            "22": (3922.63, 4442.58), "23": (6284.14, 7283.93)},
    ("KR0071", "2026.2Q"): {"15": (19891.14, 24744.35), "14": (22478.49, 27737.29),
                            "22": (4764.60, 5930.51), "23": (7351.95, 8923.45)},
    ("KR0104", "2025.3Q"): {"15": (29303.31, 30738.41), "14": (21951.08, 23386.18),
                            "22": (7352.23, 7352.23), "23": (0.0, 0.0)},
    ("KR0104", "2026.2Q"): {"15": (31084.80, 37482.96), "14": (23505.42, 29903.58),
                            "22": (7579.38, 7579.38), "23": (0.0, 0.0)},
}


def fmt(x: float) -> str:
    s = f"{round(x, 2):.2f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def load():
    raw = TARGET.read_text(encoding="utf-8")
    return raw, json.loads(raw)


def index(recs):
    m = {}
    for r in recs:
        c, q = r.get("원보험사코드"), r.get("공시분기")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        m.setdefault((c, q), {})[it] = r
    return m


def main(apply: bool) -> int:
    raw0, recs = load()
    by = index(recs)
    plan = []          # (record, item, old, new)
    for (code, q), (mode, head14) in sorted(CASES.items()):
        b = by.get((code, q))
        if b is None:
            print(f"!! {code} {q}: bucket absent — abort"); return 2
        cur14 = num(b[14].get("값_적용후"))
        if cur14 is None or abs(cur14 - head14) > 0.01:
            print(f"!! {code} {q}: item14후={cur14} != raw headline {head14} — abort"); return 2
        subs = [num(b[i].get("값_적용후")) for i in range(17, 21)]
        op = num(b[21].get("값_적용후"))
        if any(v is None for v in subs) or op is None:
            print(f"!! {code} {q}: leaf 17-21후 결측 {subs} {op} — abort"); return 2
        v15 = round(_diversified_sqrt(np.array(subs, dtype=float), R4) + op, 2)
        if mode == "AFFILIATE":
            k5 = by.get(("KR0005", q))
            a14 = num(k5[14].get("값_적용후")) if k5 and 14 in k5 else None
            if a14 is None:
                print(f"!! {code} {q}: KR0005 item14후 없음 — abort"); return 2
            v23 = round(AFFILIATE_RATIO * a14, 2)
            src23 = f"AFFILIATE {AFFILIATE_RATIO} x KR0005.14후={a14}"
        else:
            v23 = 0.0
            src23 = "ZERO (전·②후·③후 전부 0 인쇄)"
        v22 = round(v15 + v23 - head14, 2)
        v16 = round(sum(subs) + op - v15, 2)
        # --- 정본 검사 ③ 단조성 / ④ 잔차 범위 ---
        s = SINGLE[(code, q)]
        for key, val in (("15", v15), ("22", v22), ("23", v23)):
            lo = min(s[key])
            if val > lo + 0.01:
                print(f"!! {code} {q} item{key}후={val} > 단일표 최소 {lo} — 단조성 위반, abort")
                return 2
        pre22 = num(b[22].get("값"))
        if v22 < 0 or (pre22 and v22 > 1.2 * pre22):
            print(f"!! {code} {q} 잔차 법인세후={v22} 범위 밖 (22전={pre22}) — abort"); return 2
        print(f"--- {code} {q} ---")
        print(f"    14후(앵커, 불변) = {head14}   23후 근거: {src23}")
        for it, new in ((15, v15), (16, v16), (22, v22), (23, v23)):
            rec = b.get(it)
            if rec is None:
                print(f"!! {code} {q}: item{it} 행 없음 — abort(행 신설 금지)"); return 2
            old = rec.get("값_적용후")
            print(f"    item{it}후: {old} -> {fmt(new)}"
                  f"{'   (변경없음)' if str(old) == fmt(new) else ''}")
            if str(old) != fmt(new):
                plan.append((rec, it, old, fmt(new)))
        chk5 = v15 - v22 + v23
        print(f"    R5후 재검산: {v15} - {v22} + {v23} = {round(chk5,2)}  vs 14후 {head14}"
              f"  (잔차 {round(chk5-head14,2):+})")
        print(f"    R6후 재검산: sum(17..21)후 {round(sum(subs)+op,2)} - 15후 = {v16}")
    print(f"\n변경 예정 셀 {len(plan)}개")
    if not apply:
        print("(dry-run — 쓰지 않음)")
        return 0
    # --- check-and-set: 읽은 뒤 파일이 바뀌었으면 중단 (동시 세션 lost-update 방지) ---
    raw1 = TARGET.read_text(encoding="utf-8")
    if raw1 != raw0:
        print("!! 마스터가 판독 이후 변경됐다 — 동시 세션 충돌, 쓰지 않고 중단"); return 3
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_suffix(f".json.bak_{stamp}_kr0071_kr0104_combined")
    shutil.copy2(TARGET, bak)
    for rec, _it, _old, new in plan:
        rec["값_적용후"] = new
    TARGET.write_text(json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"백업: {bak.name}")
    print(f"기록 완료: {TARGET.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
