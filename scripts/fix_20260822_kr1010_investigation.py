# -*- coding: utf-8 -*-
"""KR1010(교보라이프플래닛생명보험) 12개 분기 — [지급여력비율의 경과조치 적용에 관한 사항]
1) 공통적용 경과조치 관련 표(item47/48/49/50/51) 존재 여부 재검증.

대상 분기: 2023.2Q 2023.3Q 2023.4Q 2024.1Q 2024.2Q 2024.3Q 2024.4Q 2025.1Q 2025.2Q
           2025.3Q 2025.4Q 2026.1Q  (2023.1Q는 이미 적재됨 — 이 스크립트 대상 아님)

## 결론: 12개 분기 전부 "진짜결측" — 채울 값 없음

기존 자동추출기(`fix_20260822_tfi_tier_full_scan.py::extract_tfi_full`)가 12개 분기 전부에서
"'공통적용'+'보완자본'+'한도' 3키워드 동시 페이지 없음"으로 미검출 처리한 것을, raw PDF
원문(fitz 텍스트 레이어, 전부 정상 밀도 — 스캔본 아님)을 12개 분기 전부 직접 읽어 재확인했다.

**원문 자체가 표를 안 그린다.** 이 회사는 "4-2-2. 지급여력비율의 경과조치 적용에 관한
세부사항" 도입부에 "당사의 경과조치 적용 사항은 다음과 같습니다"라는 요약표(2023.3Q부터
등장, 2023.2Q는 요약표 없이 바로 서술)를 두는데, 거기서 "공통적용 > 가용자본 > 제도시행前
기발행자본증권가용자본 인정범위 확대(TFI) > 적용여부 = X"로 12개 분기 전부 명시한다.
그 아래 "[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치 관련" 섹션은
아래 두 변형 중 하나로만 나타나고, **어느 쪽도 47-51 표(6줄: 지급여력금액/기본자본/보완자본/
보완자본한도적용전/보완자본한도/초과분/지급여력기준금액)를 인쇄하지 않는다**:

  - 변형A(2023.2Q~2024.2Q): "해당 사항 없음" / "해당사항 없음" / "(해당없음)" 명시
  - 변형B(2024.3Q~2026.1Q): 위 문구 대신 바로 아래 "2) 선택적용 경과조치 관련 ① 자본감소분
    경과조치"의 각주("당사는 자본감소분 경과조치를 적용하지 않아...")가 섹션1) 바로 밑에
    잘못 복사돼 나온다(원문 자체의 편집 아티팩트로 보임 — TFI가 아니라 TAC 각주). 어느 쪽도
    표는 없다 — 이 회사 필링의 일관된 관례는 "경과조치가 실제 적용 안 되는 항목은 표 자체를
    안 그린다"(같은 페이지의 "2)① 자본감소분"도 TAC=X라 표가 없고, "②③"은 TIR/TER=O라
    표가 있음 — 표 유무가 적용여부와 1:1 대응). 이 관례는 2023.1Q(이미 적재, 아래 참고)에서
    TFI=?(적용여부 요약표 자체가 아직 없던 최초 분기)였을 때 표가 실제로 인쇄됐던 것과도
    모순 없다 — 처음 한 번 표를 냈다가, 이후 회사가 TFI 대상 기발행자본증권이 없다는 게
    분명해지며 2Q부터 "해당없음"으로 굳어진 것으로 보인다(2023.1Q raw 자체에 적용여부
    요약표가 없어 그 분기의 TFI 상태를 문서상 직접 확인할 수는 없다 — 다만 표 값 자체가
    경과조치 전=후 완전동일(163.83=163.83, 100,080=100,080)이라 TFI 적용이 이 회사 숫자에
    실질적 영향이 없었다는 점은 일관된다).

4Q 두 개(2024.4Q/2025.4Q)는 K-ICS 외부 감사보고서 첨부(연간 결합 PDF, 190여 페이지)까지
포함하는데, 그 별첨 "C.3.1 경과조치 적용내역"에도 TFI 언급이 전혀 없고(선택적용 TIR/TER만
언급), 별첨의 "지급여력금액" 감사표도 경과조치 적용전=후 완전동일(2024.4Q 135,519,901천원
양쪽 동일, 2025.4Q 122,890,095천원 양쪽 동일) — 본문 요약과 정확히 일치해 별첨에 숨은
TFI 표가 없다는 것도 교차확인했다.

**결론: 채울 항목 0건.** "값을 지어내지 마라"·"틀린 값을 싣느니 빈 칸" 원칙에 따라 47/48/49/
50/51 을 이 12개 분기에 0으로도, 다른 값으로도 채우지 않는다 — 원문이 표 자체를 안 그리는
것과 "표가 있는데 전부 0"은 다른 사실이다(대조: 메트라이프·카카오페이 등은 원문이 실제로
0을 인쇄한 표를 갖고 있어 ALL_ZERO_TRIVIAL 로 적재됨 — 이 회사는 그 표 자체가 없다).

## 이 스크립트의 역할

값을 채우는 스크립트가 아니라 **재검증 스크립트**다 — 기존 추출기(재사용, 재구현 아님)를
12개 분기에 다시 돌려 "미검출"이 여전히 재현되는지 자동 확인하고, 위 결론을 census로 출력한다.
UPSERT 대상(`KR1010_CONFIRMED_VALUES`)은 항상 비어 있다 — 향후 raw가 정정판으로 교체되어
실제로 표가 생기면 그때 이 딕셔너리를 채우고 실행하면 된다(idempotent: 이미 있는 셀은 skip).

Usage:
  ...python scripts/fix_20260822_kr1010_investigation.py --dry-run
  ...python scripts/fix_20260822_kr1010_investigation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import fix_20260822_tfi_tier_full_scan as F  # noqa: E402  (reuse extract_tfi_full — no reinvention)
import fix_20260821_tier2_limit_lines as T2  # noqa: E402  (reuse _pdf/q2p/_num)

TARGET = REPO / "kics_disclosure.json"

QUARTERS = ["2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q",
            "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]

# 원문 인용 근거(페이지는 1-based, raw PDF 기준) — 최종보고와 동일 내용의 기계가독 사본.
CITATIONS = {
    "2023.2Q": "p12: '1) 공통적용 경과조치 관련 / 해당 사항 없음' (요약표 없음, 최초 간이서술)",
    "2023.3Q": "p11 적용여부표 TFI=X; p13: '1) 공통적용 경과조치 관련 / 해당사항 없음'",
    "2023.4Q": "p29 적용여부표 TFI=X; p31: '1) 공통적용 경과조치 관련 (해당없음)'",
    "2024.1Q": "p13 적용여부표 TFI=X; p15: '1) 공통적용 경과조치 관련 / 해당사항 없음'",
    "2024.2Q": "p14 적용여부표 TFI=X; p16: '1) 공통적용 경과조치 관련 / 해당사항 없음'",
    "2024.3Q": "p13 적용여부표 TFI=X; p15: '1) 공통적용 경과조치 관련' 아래 표 없음"
               "(TAC 각주만 잘못 복사, 원문 편집 아티팩트)",
    "2024.4Q": "p50 적용여부표 TFI=X; p52 동일 패턴; 별첨감사보고서 p141-150"
               "(C.3.1엔 TIR/TER만 언급, 지급여력금액 135,519,901천원 전=후 동일 — TFI無 교차확인)",
    "2025.1Q": "p17 적용여부표 TFI=X; p19: '1) 공통적용 경과조치 관련' 아래 표 없음",
    "2025.2Q": "p18 적용여부표 TFI=X; p20: '1) 공통적용 경과조치 관련' 아래 표 없음",
    "2025.3Q": "p17 적용여부표 TFI=X; p19: '1) 공통적용 경과조치 관련' 아래 표 없음",
    "2025.4Q": "p50 적용여부표 TFI=X; p52 동일 패턴; 별첨감사보고서 p134-145"
               "(C.3.1엔 TIR/TER만 언급, 지급여력금액 122,890,095천원 전=후 동일 — TFI無 교차확인)",
    "2026.1Q": "p17 적용여부표 TFI=X; p19: '1) 공통적용 경과조치 관련' 아래 표 없음",
}

# 채울 값 없음 — 12개 분기 전부 진짜결측 확정(위 docstring 참고). 향후 raw 정정판이 나오면
# 여기에 {q: {47: (pre,post), 48: (...), ...}} 형태로 채우고 아래 main()의 UPSERT 루프가 그대로 쓴다.
KR1010_CONFIRMED_VALUES: dict[str, dict[int, tuple]] = {}


def main() -> int:
    dry = "--dry-run" in sys.argv

    data = None
    existing = set()
    if TARGET.exists():
        import json
        data = json.loads(TARGET.read_text(encoding="utf-8"))
        existing = {(r["원보험사코드"], r["공시분기"], int(r["항목번호"])) for r in data}
        kr1010_rows = [r for r in data if r["원보험사코드"] == "KR1010"]
        print(f"로드 전 row_count = {len(data):,}  (KR1010 = {len(kr1010_rows)}행)")

    print(f"\n=== 재검증: extract_tfi_full() 을 12개 분기에 재실행 (기존 추출기 재사용) ===")
    reconfirmed = 0
    unexpected = []
    for q in QUARTERS:
        pdf = T2._pdf(T2.q2p(q), "KR1010")
        if pdf is None:
            print(f"  {q}: raw 없음(예상 밖 — 확인 필요)")
            unexpected.append(q)
            continue
        found, anchor, reason = F.extract_tfi_full(pdf)
        cite = CITATIONS.get(q, "")
        if not found:
            print(f"  {q}: 미검출 재확인 (reason={reason}) — {cite}")
            reconfirmed += 1
        else:
            # 자동추출기가 뭔가를 찾았다면 이 세션의 수기판정과 모순 -- 억지로 무시하지 않고 표면화.
            print(f"  {q}: [예상 밖] 추출기가 값을 찾음 found={found} anchor={anchor} — 수기재검토 필요")
            unexpected.append(q)

    print(f"\n재확인(미검출 그대로) = {reconfirmed}/{len(QUARTERS)}  |  예상 밖 = {len(unexpected)}")
    if unexpected:
        print(f"  예상 밖 분기: {unexpected}  <- 이 스크립트의 '진짜결측' 결론과 모순, 수기 재검토 필요")

    print(f"\n=== 결론: KR1010 12개 분기 전부 진짜결측(TFI 적용여부=X, 표 자체 없음) ===")
    print("적재 대상 0건 — kics_disclosure.json 안 건드림. 근거는 이 파일 docstring 참고.")

    # --- UPSERT (현재는 KR1010_CONFIRMED_VALUES 가 비어 있어 항상 no-op) ---
    new_rows = []
    if data is not None:
        info = next((r for r in data if r["원보험사코드"] == "KR1010"), None)
        ITEM_LABELS = {
            47: "보완자본 한도 적용 전", 48: "보완자본 한도",
            49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
            50: "기본자본(TFI표, 공통적용경과조치)", 51: "보완자본(TFI표, 공통적용경과조치)",
        }
        for q, items in KR1010_CONFIRMED_VALUES.items():
            for it, (pre, post) in items.items():
                if ("KR1010", q, it) in existing:
                    print(f"  [SKIP] KR1010 {q} item{it} 이미 존재")
                    continue
                new_rows.append({
                    "원보험사코드": "KR1010", "원수사명": info["원수사명"],
                    "티커": info.get("티커"), "생손보여부": info.get("생손보여부"),
                    "항목번호": it, "항목명": ITEM_LABELS[it], "공시분기": q,
                    "값": str(pre), "값_적용후": str(post),
                })

    print(f"\n신규 셀 = {len(new_rows)}건")
    if dry:
        print("(dry-run; 파일 안 씀)")
        return 0
    if not new_rows:
        print("쓸 셀 없음")
        return 0

    data.extend(new_rows)
    import json
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(new_rows)}행 INSERT, wrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
