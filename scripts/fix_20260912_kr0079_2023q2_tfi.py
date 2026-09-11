# -*- coding: utf-8 -*-
"""KR0079(미래에셋생명) 2023.2Q — 자본증권(TFI표, item47-54) 신규 UPSERT.

## 배경 (inbox `20260912T0115Z__downloader__KR0079_2023.2Q__docling_md_missing_image_pdf.md`)
raw PDF(`data/disclosure/FY2023_Q2/raw/KR0079_미래에셋생명.pdf`, 58p)는 있는데 md_inbox에 이
분기 MD가 없었다(docling head_fallback으로 재변환해도 텍스트 레이어가 페이지당 83자뿐이라
지급여력 표를 못 찾음 — `run_harness.py --stage parse --period FY2023_Q2 --pdf-root
data/disclosure/FY2023_Q2/raw --companies KR0079`로 재변환 완료, 이 회사 특유의 이미지/벡터
렌더링 PDF라 예상대로 head_fallback 그침, 신규 파싱 불가 재확인).

census 결과 items 1-9,11-28(item10 제외)·29-35·36-40·41-46 = 45칸은 **이미 마스터에 적재돼
있었다**(어느 경로로 들어갔는지는 git-untracked md_inbox라 추적 불가 — 이전 세션의 fitz
직접판독 추정) — fitz 200dpi 렌더(raw p10/p11/p15/p19/p21/p22/p23)로 45칸 전부 육안 재대조,
불일치 **0건**(아래 VERIFIED 참조). item47-54(TFI표)만 완전 결측이라 raw p12를 렌더해 신규
판독, 이 스크립트가 그 8칸을 UPSERT한다.

## item10 (6.비지배지분) — 확인 후 미착수 (의도적)
raw p11 렌더: Ⅰ.순자산 하위가 "1.보통주~5.기타포괄손익누계액" 다음 바로 "6.조정준비금"으로
이어져 **비지배지분 행 자체가 이 분기 공시에 없다**(빈칸이 아니라 행이 구조적으로 부재 —
자본조정 항목 5개 합 36,004 = item4 와 정확히 일치해 별도 6번째 항목이 없다는 것도 산수로
재확인됨). 마스터 전체 census(538개 (사,분기) 버킷 중 447개만 item10 보유, 91개는 이미 결측)
로 봐도 드문 일이 아니라 **정상 패턴** — 값 없는 행을 만들어 넣지 않는다(추측 금지).

## VERIFIED (fitz 200dpi 렌더, scripts/_probes/probe_20260912_kr0079_2023q2_render*.py) — 기존
45칸 전부 마스터와 일치, 재현 페이지:
  p10 [지급여력비율 총괄]: 지급여력비율 209.7 · 지급여력금액 40,971 · 지급여력기준금액 19,536
    (경과조치 전=후, "당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함")
  p11 [경과조치 적용 전 지급여력비율 세부]: item2-9,11-26 전항목 일치(단위 억원)
  p12 [지급여력비율의 경과조치 적용에 관한 사항] 1)공통적용경과조치: item47-54 신규판독(아래)
  p15 [생명·장기손해보험위험액-대재해위험 이외]: 사망187,389·장수24,193·장해질병650,731·
    장기재물기타-(0)·해지1,149,872·사업비299,709 (백만원) → item29-34 일치
  p19 [②금리위험액 현황]: Ⅳ.금리위험액 충격전457,925→item36 일치. Ⅲ.순자산가치 6칸
    (충격전/평균회귀/금리상승/금리하락/금리평탄/금리경사) → item41-46 전부 일치
  p21 [③주식위험액 현황] 합계569,984→item37 / [④부동산위험액 현황] 합계280,319→item38 일치
  p23 [⑤외환위험액 현황] 계109,515→item39 / [⑥자산집중위험액] 전부"-"(0)→item40 일치
  p18 "3.일반손해보험위험 관리: 해당사항 없음" → item18=0 확인

## item47-54 원문 판독 (raw p12, 단위 백만원 → 억원 = /100)
[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치 관련 (경과조치 적용 전 | 적용 후)
    지급여력비율(%)              209.7        | -
    지급여력금액                 4,097,054    | -
      기본자본                   3,037,372    | -
      보완자본                   1,059,682    | -
        보완자본 한도 적용 전     1,059,682    | -
        보완자본 한도             976,816      | -
        해약환급금 부족분 상당액 중 해약환급금 상당액 초과분  563,049 | -
        (기발행 신종자본증권)     -            | (빗금, N/A)
        (기발행 후순위채무)       496,633      | (빗금, N/A)
    지급여력기준금액             1,953,632    | (빈칸)
적용후 열은 이 표 자체는 "-"로 인쇄돼 있으나, 같은 페이지 상단 각주("당사는 경과조치를 적용하지
않아 경과조치 전·후 금액 및 비율이 동일함")와 KR0079 이미 적재된 다른 분기(2023.4Q/2024.4Q/
2025.4Q, `fix_20260901_kr0079_scanned_section_tier2.py`)가 전부 47-52를 pre=post로 미러링한
확립된 패턴을 그대로 따른다(53/54는 그 스크립트와 동일하게 post=None, 적용후 개념 자체가 없는
빗금 메모행).

## 항등식 교차검산 (CHECKS, 전부 GREEN) — 로직은 `fix_20260901_kr0079_scanned_section_tier2.py`
와 동일(item51==item47 UNCAPPED / item50+item51==item52 / item52~=item1 / item48~=item14x50%)
    item51(10596.82) == item47(10596.82)        UNCAPPED
    item50(30373.72) + item51(10596.82) = 40970.54 == item52(40970.54)
    item52(40970.54) ~= item1(40971)             D+0.46  OK(<1억)
    item48(9768.16) ~= item14(19536)x50%=9768.0  D+0.16  OK(<1억)
전부 아래 main() 실행 시 재계산해 통과 여부를 찍는다(불통과면 ABORT, 아무것도 안 씀).

## 실행
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260912_kr0079_2023q2_tfi.py [--apply]
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"
CODE = "KR0079"

LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
    52: "지급여력금액(TFI표, 공통적용경과조치)",
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}

# quarter -> {item: (값, 값_적용후)} 억원. 적용후 None = 원문 칸이 빗금(해당없음).
DATA: dict[str, dict[int, tuple[float, float | None]]] = {
    "2023.2Q": {
        47: (10596.82, 10596.82), 48: (9768.16, 9768.16), 49: (5630.49, 5630.49),
        50: (30373.72, 30373.72), 51: (10596.82, 10596.82), 52: (40970.54, 40970.54),
        53: (0.0, None), 54: (4966.33, None),
    },
}


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) is not None)
    return len(rows), len(combos), filled


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    b = census(rows)
    print(f"before: rows={b[0]} combos={b[1]} filled={b[2]}")
    idx = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in rows}
    meta = None
    for r in rows:
        if r["원보험사코드"] == CODE:
            meta = (r["원수사명"], r.get("티커"), r["생손보여부"])
            break
    if meta is None:
        print(f"ABORT: {CODE} 행이 마스터에 전혀 없다"); return 2
    nm, tk, seg = meta

    n_ins = n_upd = 0
    for q, items in DATA.items():
        for it in sorted(items):
            cur = idx.get((CODE, q, str(it)))
            if cur is None:
                n_ins += 1
                continue
            cv = cur.get("값")
            if cv is None or abs(float(cv) - items[it][0]) > 1.0:
                print(f"  ABORT {q} item{it}: 기존값 {cv!r} 이 판독값 {items[it][0]} 과 "
                      f"1억 넘게 다르다 — 손대지 않는다"); return 2
            print(f"  UPDATE {q} item{it}: {cv} -> {items[it][0]} (렌더 정밀값)")
            n_upd += 1

        # 항등식 교차검산
        g = lambda i: items[i][0]
        chk = [("item51 == item47 (UNCAPPED)", g(51), g(47)),
               ("item50 + item51 == item52", g(50) + g(51), g(52))]
        m14 = idx.get((CODE, q, "14"))
        m3 = idx.get((CODE, q, "3"))
        m1 = idx.get((CODE, q, "1"))
        if m14 is not None:
            chk.append(("item48 == item14 x 50%", g(48), float(m14["값"]) * 0.5))
        if m1 is not None:
            chk.append(("item52 == item1(지급여력금액)", g(52), float(m1["값"])))
        print(f"\n  {nm} {q}")
        for lab, a, bb in chk:
            ok = "OK" if abs(a - bb) <= 1.0 else "*** 안 닫힘 ***"
            print(f"    {lab:<32} {a:>12,.2f} vs {bb:>12,.2f}  D{a - bb:>+7,.2f}  {ok}")
            if abs(a - bb) > 1.0:
                print("    ABORT: 검산 실패"); return 2
        if m3 is not None:
            d = g(51) - float(m3["값"])
            print(f"    (참고) item51 vs item3(보완자본) sliver: D{d:+.2f} (허용, blocking 아님)")

    print(f"\nINSERT {n_ins}칸(신규 행), UPDATE {n_upd}칸(기존 행, 이번 실행에선 0이어야 정상)")
    if not apply:
        print("(dry-run) 반영하려면 --apply")
        return 0

    for q, items in DATA.items():
        anchor = idx.get((CODE, q, "46"))
        pos = rows.index(anchor) + 1 if anchor is not None else len(rows)
        for it in sorted(items):
            pre, post = items[it]
            cur = idx.get((CODE, q, str(it)))
            if cur is not None:
                cur["값"] = pre
                if post is not None:
                    cur["값_적용후"] = post
                continue
            row = {"원보험사코드": CODE, "원수사명": nm, "티커": tk, "생손보여부": seg,
                   "항목번호": it, "항목명": LABELS[it], "공시분기": q,
                   "값": pre, "값_적용후": post}
            rows.insert(pos, row); pos += 1
            idx[(CODE, q, str(it))] = row

    a = census(rows)
    print(f"after : rows={a[0]} combos={a[1]} filled={a[2]}  (+{a[0] - b[0]}행 +{a[2] - b[2]}셀)")
    if a[0] - b[0] != n_ins or a[1] - b[1] != n_ins:
        print("  ABORT: 행/콤보 증가가 예상과 다르다"); return 2

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_kr0079_2023q2tfi")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
