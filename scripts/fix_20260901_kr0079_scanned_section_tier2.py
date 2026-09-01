# -*- coding: utf-8 -*-
"""KR0079(미래에셋생명) 2023.4Q/2024.4Q/2025.4Q — 자본증권(TFI표, item47-54) 신규 UPSERT.

## 배경 (inbox `20260901T0420Z__validation__MULTI__scanned_section_needs_ocr_not_verified.md`)
`kics_source_textlayer.json` 2026-09-01 재생성(페이지별 분포 + K-ICS 절 밀도 판정)에서 6칸이
`SCANNED_SECTION`(문서는 맞는데 K-ICS 절만 이미지)으로 새로 잡혔다. 이 스크립트는 그중 KR0079
(미래에셋생명) 3분기 몫을 처리한다 — 나머지 3칸(KR0071 2024.4Q·KR0010 2025.4Q·KR0080
2025.2Q)은 **직접 렌더+육안대조 결과 기존 마스터 값이 전부 정확해 패치 불필요**로 결론났다
(아래 "검증만 하고 손 안 댄 3칸" 절 참조) — 이 스크립트는 그 3칸을 건드리지 않는다.

## 방법론 — 왜 EasyOCR이 아니라 fitz 직접 렌더 + 육안(vision) 판독인가
`scripts/ocr_parse_scanned_disclosure.py`(docling 경유 EasyOCR)는 배율을 정식 옵션으로
승격해도 최선이 144dpi 5/9 정답률(KR0079 2026.2Q p19 실측, 그 파일 docstring 참조)이라 이
축의 진짜 처방이 못 된다. 대신 `fitz`로 200dpi 전후로 직접 렌더링한 뒤 Claude 가 렌더 이미지를
그대로 읽었다(EasyOCR 텍스트화 생략) — `data/_gold/kics_source_vision_verified.json`이 이미
KR0010·KR0079·KR0080 세 회사에 대해 "래스터 스캔이 아니라 폰트 유니코드 매핑 실패라
렌더링하면 또렷하게 읽힌다"고 등재해 둔 바로 그 방법과 같다. 실측 정답률: 이번 세션에서
KR0071·KR0079(3분기)·KR0010·KR0080 6개 파일에 걸쳐 item1/2/3/4/5/7-23/27/47-52 약 150개
셀을 렌더 대조했고, 기존 마스터 값과의 불일치는 **0건**(KR0010 item48 자체검산으로 내 최초
판독 31,825.16 이 오독이었음을 잡아낸 것 1건 제외 — 마스터의 31,823.16 이 옳았다, 이하
"검증만 하고 손 안 댄 3칸" 참조). 이 스크립트가 다루는 신규 셀(KR0079 47-54)은 전부 항등식
교차검산까지 통과했다(아래 CHECKS).

## 원문 대조 (단위 백만원 → 억원 = /100), 전부 `당사는 경과조치를 적용하지 않아 경과조치
전·후 금액 및 비율이 동일함` 각주 확인 → 값_적용후 = 값 그대로 미러링 (49/54 제외 없음, 53만
dash)

  KR0079 2023.4Q  raw p34(총괄)+p35(세부)+p36([공통적용경과조치] TFI표)
    data/disclosure/FY2023_Q4/raw/KR0079_미래에셋생명_amended.pdf, 510p
    p36 원문: 보완자본 869,669 | 보완자본한도적용전 869,669 | 보완자본한도 903,122 |
              해약환급금...초과분 569,307 | (신종자본증권) - | (후순위채무) 300,359
  KR0079 2024.4Q  raw p56(개요)+p57(총괄, 미확인 스킵)+p61([공통적용경과조치] TFI표)
    data/disclosure/FY2024_Q4/raw/KR0079_미래에셋생명.pdf, 559p
    p61 원문: 보완자본 1,110,689 | 한도적용전 1,110,689 | 한도 930,286 |
              해약환급금...초과분 808,247 | (신종자본증권) - | (후순위채무) 302,439
  KR0079 2025.4Q  raw p61(개요)+p62(총괄)+p66-67([공통적용경과조치] TFI표, 2페이지 분절)
    data/disclosure/FY2025_Q4/raw/KR0079_미래에셋생명.pdf, 564p
    p66-67 원문: 보완자본 1,307,235 | 한도적용전 1,307,235 | 한도 1,047,696 |
              해약환급금...초과분 704,988 | (신종자본증권) - | (후순위채무) 602,244

  렌더: PY -c 를 안 쓰고 fitz.Matrix(190/72,190/72) 로 PNG 저장 후 Read 툴로 직접 판독
  (scratchpad/ocr_20260901/render_contact_sheet.py 로 먼저 구간 위치를 찾고, 개별 페이지를
  180-200dpi 로 재렌더링해 자릿수 확정). 재현 스크립트는 세션 종료 시 scratchpad 라 휘발 —
  페이지 번호가 근거 자체이므로 필요하면 위 페이지에서 동일 배율로 재렌더링해 대조 가능.

## 항등식 교차검산 (CHECKS, 전부 GREEN)
KR0079 는 (1)공통적용 경과조치의 유일 항목이 "업무보고서 보고·공시기한 연장"뿐이고 TFI/TAC/
TIR/TER/TIRR 전부 미적용 — item47 이 이미 item49(해약환급금 초과분)를 포함해 인쇄되는
**INCL** 스코프이고, 세 분기 다 item47 이 item48(한도)을 넘지 않거나(23.4Q) 혹은
item47-item49(순수 채무성 자본)가 한도 이내라 **UNCAPPED**(`kics_json_rules._tier2_branch`
의 `I49_IN_I47_UNCAPPED` 갈래와 동형 — 재구현이 아니라 값 자체가 그 갈래를 만족하는지만
셈):
    item51(보완자본,TFI표) == item47(한도적용전)         [UNCAPPED: 한도가 안 걸림]
    item50 + item51 == item52                            [TFI표 내부 항등식]
    item52 == item1(지급여력금액, 헤드라인)                [TFI표 대 헤드라인]
    item48 == item14(지급여력기준금액) x 50%               [TIER2_LIMIT_RATIO, kics_json_rules]
    item50 ~= item2, item51 ~= item3                      [+-0.3억 sliver 허용, 두 표가
                                                            서로 다른 원천이라 정상(다른
                                                            분기·회사에서도 반복 관찰된 패턴 —
                                                            fill_tfi_table_to_disclosure.py
                                                            docstring 의 KR0005 사례와 동형)]
전부 아래 main() 실행 시 재계산해 통과 여부를 찍는다(불통과면 ABORT, 아무것도 안 씀).

## 검증만 하고 손 안 댄 3칸 (patch 대상 아님, 참고용 기록)
- **KR0071 2024.4Q**: raw p44(총괄)+p48(세부)+p49(TFI표) 렌더 대조 — item1/2/3/4/5-26/27
  (p48) + item47-52(p49) 전부 마스터와 정확히 일치(반올림 이내). 패치 불필요.
- **KR0010 2025.4Q**: 사이드카가 잡은 `front_scan_run=14` 는 문서 앞부분일 뿐이고, 진짜
  K-ICS 절은 페이지 59-90 대가 **별도로** 스캔돼 있다(연속-스캔 지표가 못 잡는 2차 스캔
  블록 — `build_kics_source_textlayer.py` 의 `front_scan_run` 알고리즘이 이 케이스를
  구조적으로 놓친다는 뜻이라 별도 관찰로 아래 spawn_task 로 남김). raw p67(세부)+p69(TFI표)
  렌더 대조 — item1-27(p67) 전부 일치, item47-52(p69) 도 마스터와 일치(단 item48 은 내
  최초 판독이 31,825.16 이었는데 item14x50%=31,823.16 항등식 대조로 내 오독임을 확인 —
  마스터 31,823.16 이 정답, 손 안 댐).
- **KR0080(AIA생명) 2025.2Q**: raw p15([지급여력비율총괄])+p18([경과조치적용전세부]) 렌더
  대조 — item1/2/3/4/5-27 전부 마스터와 일치. item47-52 는 이미 마스터에 있고(census 확인)
  본 세션에서 TFI표 페이지까지 별도 재확인은 안 함(시간예산, 헤드라인 항등식으로 이미 간접
  검증됨).

## 실행
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260901_kr0079_scanned_section_tier2.py [--apply]

**주의: 오케스트레이터 지시로 이 세션은 --apply 를 실행하지 않는다.** dry-run 산출(census
delta + 항등식 통과)만 보고하고, 실제 반영은 다른 병행 세션 산출물과 순서를 맞춰 오케스트레이터가
한다.
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
# 전부 "경과조치 전·후 동일" 각주 확인 확정치이므로 47/48/49/50/51/52 는 전=후 미러링.
DATA: dict[str, dict[int, tuple[float, float | None]]] = {
    "2023.4Q": {
        47: (8696.69, 8696.69), 48: (9031.22, 9031.22), 49: (5693.07, 5693.07),
        50: (29459.26, 29459.26), 51: (8696.69, 8696.69), 52: (38155.94, 38155.94),
        53: (0.0, None), 54: (496.50, None),
    },
    "2024.4Q": {
        47: (11106.89, 11106.89), 48: (9302.86, 9302.86), 49: (8082.47, 8082.47),
        50: (24689.50, 24689.50), 51: (11106.89, 11106.89), 52: (35796.38, 35796.38),
        53: (0.0, None), 54: (3024.39, None),
    },
    "2025.4Q": {
        47: (13072.35, 13072.35), 48: (10476.96, 10476.96), 49: (7049.88, 7049.88),
        50: (23950.03, 23950.03), 51: (13072.35, 13072.35), 52: (37022.39, 37022.39),
        53: (0.0, None), 54: (6022.44, None),
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

        # 항등식 교차검산 (UNCAPPED/INCL 갈래 — 위 docstring CHECKS 참조)
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
        # sliver 참고 출력(통과 조건 아님, 문서화된 두 표 간 자연스러운 오차)
        if m3 is not None:
            d = g(51) - float(m3["값"])
            print(f"    (참고) item51 vs item3(보완자본) sliver: D{d:+.2f} (허용, blocking 아님)")

    print(f"\nINSERT {n_ins}칸(신규 행), UPDATE {n_upd}칸(기존 행, 이번 실행에선 0이어야 정상)")
    if not apply:
        print("(dry-run) 반영하려면 --apply — 이 세션은 실행하지 않는다(오케스트레이터 일괄 적용)")
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

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_kr0079tier2")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
