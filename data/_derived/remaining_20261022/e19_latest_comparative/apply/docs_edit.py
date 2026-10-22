# -*- coding: utf-8 -*-
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")

def rw(rel, fn):
    p = ROOT / rel
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    s = raw.decode("utf-8").replace("\r\n", "\n")
    s = fn(s)
    p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))

# ---------------- TODO
BLOCK = """- **2026-10-22 18차: 7사 19버킷 PL 최신 비교열 적재(티켓 20261022T0900Z, owner 「그럼 걔네도 바꿔라」)** — 흥국화재 4 · NH농협손보 4 · 동양 4 · ABL 3 · 푸본현대 2 · DB생명 1 · 농협생명 1버킷의 Tier-1 PL 171칸(별도 기준, 후속 공시 전기 누계 열)을 gold 로 적재. 계획 172칸 전부 필링 XML 줄 번호로 독립 재독해 172/172 일치, 1칸(농협생명 2023.3Q 항목 32, 반올림 0.034 차이)은 「마스크된 gold 칸 = 등재부 박제 필요」라 제외했다.
  이음매 단일분기: 3개월 열 인쇄값 `set_dangi` 20칸(흥국 4 · DB생명 4 · 푸본현대 2024.3Q 8 · 농협생명 4), 인쇄값 없는 `null_dangi` 17칸(NH농협손보·동양 2023.4Q). 실제 `build_pl()` 두 번 실행(옛 gold/새 gold) 차이 235칸만 셀 단위 반영: 값 171 + 값_당분기 215(그중 단일분기 파생 64). 계획서가 적은 단일분기 244개와 빌드 0건 불일치, git HEAD 대비 독립 diff 전부 통과(다른 회사·다른 필드 0).
  게이트 전→후: 데이터계약 RED 0→1(xlsx `손익분해PL` 동기화 지연뿐) · master_tables SUMMARY 불변(골든 `--update` 불필요; OCI_VS_BS_AOCI 23건 집합만 교체, tax22 「최신 비교열로만 통과」 4→22) · 연속성/워터폴/NB 불변 · PL 골든·gold_overlay·identity 통과 · rule_coverage 102/104(실패 2 = xlsx 청결 1 + 새 22칸을 반영하도록 고친 tax22 테스트는 수정 후 통과).
  남은 것: publishing = xlsx `손익분해PL` 386셀·panel/public_exports 재생성 / 유지 32버킷(블록 불닫힘)·부속 53버킷은 이번 범위 밖 / 푸본현대 2024.3Q·4Q, DB생명 2023.1Q·2Q, 농협생명 2023.1Q·2Q 는 옛 판 그대로(owner gold 겹침 또는 승인 범위 밖). 커밋 안 함.
  근거·재현 `data/_derived/remaining_20261022/e19_latest_comparative/apply/`(`INDEX.txt` · `e19_apply.py --verify`/`--revert --apply` · `e19_diff_vs_head.txt`) · `docs/changelog_parser_ifrs17.md` 18차.
"""

def todo(s):
    head = "## Status (최신 3개)\n\n"
    assert s.count(head) == 1
    s = s.replace(head, head + BLOCK, 1)
    old = "- [ ] **다른 회사 같은 유형(최신 비교열 미반영) — owner 결정 필요(화면 숫자가 크게 바뀜)**"
    new = "- [ ] **다른 회사 같은 유형(최신 비교열 미반영) — owner 결정 19버킷은 18차에 적재 완료, 남은 것 = 유지 32버킷·부속 53버킷(owner 미결정)**"
    assert s.count(old) == 1
    return s.replace(old, new, 1)

rw("TODO_parser_ifrs17.md", todo)

# ---------------- changelog
CL = """## 2026-10-22 (18차: 7사 19버킷 PL 최신 비교열 적재 — 티켓 20261022T0900Z)

커밋 안 함, push 안 함. 서브에이전트·docling 안 씀. `build_root_masters.main()`·`build_pl_breakdown`·xlsx·public_exports·CSM 마스터 미접촉. 증거 `data/_derived/remaining_20261022/e19_latest_comparative/apply/`(`INDEX.txt`).

- **owner 질문(「재공시 vs 현행 공시 충돌 RED 는 없다고 했는데 왜 또 고치나」)에 대한 답**: RED 가 있어서 고친 것이 아니다. 게이트는 한 판(원 공시 한 벌) 안의 산술만 보므로 옛 값도 새 값도 각자 닫혀 RED 가 없었고 지금도 없다(적재 전후 RED 변화는 xlsx 동기화 지연 1건뿐). 이번 적재는 owner 결정(2026-10-22 「교보생명과 같이 최신 비교열로」)이다.
- **확인**: 계획서 7개의 172칸을 필링 XML 줄(값·단위·행 라벨·열 ACONTEXT/위치·이전 마스터값)로 독립 재독(`e19_verify_plans.py`) 172/172, 이음매 3개월 열 20/20. 1칸 제외: 농협생명 2023.3Q 항목 32(−3,080 → −3,080.034, 반올림만) — gold 값이 빌더 소스와 0.05 이내면 「마스크 칸」이 되어 등재부(ledger) 박제가 있어야 테스트가 통과하므로 박제 없이 원 인쇄값을 둔다(항목 25 − 부분합 잔차 0.034 백만원).
- **적재**: gold set +171(495→666, 마스크 29 불변) · null_dangi +17 · set_dangi +20 · PL 235칸(값 171, 값_당분기 215) · 출처표 19블록(income_statement) + 병합 노트 키 · `GOLD_OVERLAY_CENSUS` PL (666, 29) · `_TAX22_LATEST_COMPARATIVE_ONLY` 22칸(테스트가 교보 4칸만 박아 둬서 확장). 하네스 `e19_apply.py`(교보 `apply_kr0073_oci.py` 일반화; 옛 gold/새 gold 두 번의 실제 `build_pl()` 차이만 반영해 기존 드리프트 495셀은 건드리지 않음).
- **효과**: 총포괄손익은 대체로 불변이고 순이익 ↔ OCI 이동(흥국화재 투자손익 −2.1~−1.7억대 아님: 억원 단위 −57~−211; 동양 2023.4Q 투자손익 1,250.31→849.54억 등 상세 `onscreen_eok.txt`). 인접 분기 단일분기가 같이 정리됨(흥국 2024.3Q · NH·ABL·동양 2024.4Q · DB생명 2023.4Q · 푸본현대 2024.3Q · 농협생명 2023.4Q 파생 칸).
- **게이트 전→후**: 데이터계약 RED 0→1(MASTER_XLSX_DRIFT 손익분해PL) · master_tables 출력 SUMMARY 동일(tax22 「최신 비교열로만 통과」 4→22, OCI_VS_BS_AOCI 23건 집합만 교체) · 연속성/워터폴/NB/live_artifacts 불변 · gold_overlay 7 · identity 14 · master_tables 골든 · PL 골든 통과 · 지문 RED 0 · rule_coverage 104 중 xlsx 청결 1건만 실패.
- **남은 것**: publishing xlsx `손익분해PL` 동기화·panel·public_exports / 옛 판으로 남는 인접 분기(푸본현대 2024.3Q·4Q, DB생명 2023.1Q·2Q, 농협생명 2023.1Q·2Q·4Q 무변경) / 유지 32·부속 53버킷.

"""

def chlog(s):
    marker = "## 2026-10-22 (17차"
    assert s.count(marker) == 1
    return s.replace(marker, CL + marker, 1)

rw("docs/changelog_parser_ifrs17.md", chlog)
print("ok")
