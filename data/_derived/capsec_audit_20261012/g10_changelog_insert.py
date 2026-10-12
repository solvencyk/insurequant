# -*- coding: utf-8 -*-
"""g10: insert the 27th-round entry at the top of docs/changelog_validation.md (below the intro, above the 26th round) and update the 'Last updated' line.  Newline style preserved."""
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
p = ROOT + "docs/changelog_validation.md"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw[:4000] else "\n"
t = raw.decode("utf-8")
marker = "## 2026-10-12 (26차) -- 골든 갱신 + AIG R3 박제 등재 (티켓 `20261012T1400Z`)"
assert t.count(marker) == 1
entry = """## 2026-10-12 (27차) -- 소진율·전망 복원 독립 감사 (티켓 `20261012T2040Z`, 읽기 전용)

- **범위·방법**: 오케스트레이터 티켓 4항목(① 47사 독립 재계산 ② 규정 대조 ③ 전망 7사 손계산 ④ 화면 대 JSON 10사 이상·375px). 대상 = publishing `dbbffcb5`·`24a3dd6c`, designer `496d359e`·`47f983ea`(HEAD `8fe48b1b` 까지 대상 파일 동일, `git diff dbbffcb5..HEAD` 로 확인). 스크립트는 `scripts/`·`src/` 를 import 하지 않고 `audit_io.py` 로 git 고정판만 읽는다 -- 공유 워킹트리에서 publishing 이 도중에 등재부·JSON 을 고치는 것을 겪어 도입했고, 처음 `ef62969` 로 잰 결과는 `dbbffcb5` 재측정 뒤 지웠다. 마스터·등재부·HTML·`public_exports`·게이트 코드·공유 티켓은 건드리지 않았다. 재현물 전부 `data/_derived/capsec_audit_20261012/`.
- **① 재계산(2026.2Q, 허용오차 0.1%p)**: 기본자본 47/47 · 인정한도(항목 14 값 × 50%) 47/47 · 초과분 필드(두 JSON) 47/47 · 보완자본 정의 문자 그대로 45/47 · 적용 전 열 46/46. 불일치 2 = 미래에셋(24.5 대 0.0)·DB생명(31.6 대 0.0): 항목 54 인쇄값에 2023년 이후 신규채가 섞여 발행연도로 덮어쓴 것(문서화됨). 발행사 헤드라인 항목 3 으로 닫는 검산은 42/46 -- 안 닫힌 4 = 위 2사 · IBK(TAC 1,138.9억을 발행사가 한도 밖에 둠: 76.0 대 107.6) · 스위스리(항목 49 인쇄 0, 4,274억). 100%+ 5사(tier1 DB손보 151.6·하나생명 238.2·아이엠라이프 221.7, tier2 동양 105.0·농협손해 103.9)는 tier2 두 곳이 발행사 항목 3 = 한도 + 49(+54)로 닫히고 tier1 세 곳은 X ≥ 초과분 필요조건을 만족한다. (`b1_summary_dbbffcb5.txt`, `b2_gap_and_regulation_dbbffcb5.txt`)
- **② 규정 대조 13항(`b3_regulation_check_dbbffcb5.txt`)**: MATCH 8 · MATCH_WITH_CAVEAT 3 · INTERPRETATION 2. 어긋나는 점 = 보완자본 분자가 발행사 인쇄 항목 54 를 기발행분으로 쓰는데 규정의 제외 기준은 발행일(시행일 이전)이다(메리츠 0.2→32.2, 흥국생명 10.6→37.0, 농협생명 18.8→21.1 ...; 이미 `TODO.md` ③). 기본자본 두 갈래(기발행 15%/신규 10%) `max` 결합과 TAC 층은 규정에 문장이 없다(해석). 증권 분류 근거 등급(`c5_evidence_grade_dbbffcb5.txt`): PRIMARY 34 · OWNER 6 · SECONDARY 2 · INDIRECT 1 · ISSUER_TABLE_ONLY 5 -- DB손보 제3회는 owner 지시에만 기댄다.
- **증권별 X 검정(`c2_per_security_xtest_dbbffcb5.txt`, 양방향, 19 발행 블록)**: AGREE 11 · AGREE(weak) 2 · DISAGREE 2 · UNDECIDED 4. DISAGREE = DB손보 제3회, 제4·5회(2026.1Q+2Q 합산 X 증가 +8,914.9 대 기본자본형 기대 +5,942.1[잔차 3.2σ]·보완자본형 기대 +8,802.0[잔차 0.1σ]; 제1·2회는 기본자본형으로 맞음 -- `c2b_dbnonlife_reverse_test.txt`). UNDECIDED = 코리안리 제5·6회 · 농협생명 제5회 · 푸본 2023-02(첫 마스터 분기가 발행 분기라 흐름이 없거나 다른 항목이 같은 분기에 들어옴). 하나생명 제1회·교보 2024-11 의 기본자본형 전환은 발행사 처리와 일치. 뒤집기 영향표: `b4_tier1_what_if_dbbffcb5.txt`.
- **③ 전망 손계산(`d1_forward_handcalc_dbbffcb5.txt`)**: 한화생명·DB손보·하나손보·하나생명·교보·메리츠·코리안리 35 시리즈점 차이 0(콜일 상환·SCR 선형 보간·한도 재계산·후순위 잔존만기 체감·단위·연도 경계), 총자본 경로는 분류와 무관하게 불변, 직전 커밋 `ef62969` 대비 230점 차이 0, `baseline_basis_flag` 잔존 0. 한도 기준을 보간 SCR 대신 경과조치 적용 전 SCR 로 둔 변형은 하나생명만 최대 1.22%p 달라진다(모델 선택 사항). 추가로 46사 전체의 비율이 자기 자본/SCR 과 같은지(`d2_forward_internal_consistency_dbbffcb5.txt`): 3사가 다르다 -- 예별(5년 모두 0.0 으로 잘림)·롯데(기본자본비율 0.0)는 `capacity_exhausted` 자름, 마이브라운은 SCR 20.3억 반올림. 기준선 금액은 46/46 마스터와 일치, 기준선 비율은 발행사 인쇄 비율과 최대 0.40%p 차.
- **④ 화면(`e6_screen_results_dbbffcb5.txt`)**: 47사 전부를 페이지의 `<select>` 로 골라 도넛·숫자 줄·전망·발행현황 막대/셀·툴팁 본문을 독립 기대값과 대조 -- 불일치 0, 가로 넘침 0/47, 부제·캡션·? 팝오버·툴팁 문구는 정의 메모 §5 와 글자까지 같음. 공개 시트 3종 47/47/460점 불일치 0(`e7`), 발행현황 타임라인 JSON 대 채권 원장 값 차이 0(`e9`). 툴팁은 Chart.js 툴팁 객체를 `setActiveElements` 로 구동해 본문을 읽고(`e4`) 일부 회사는 실제 마우스 호버로도 확인, 박스 폭은 Chart.js 계산식으로 쟀다(`e5`, 하나생명 실제 호버 329px = 식 329px 로 보정). 페이지는 CSP 때문에 `eval` 불가라 `<script src>` 주입, 창이 안 보이면 Chart.js 가 그리지 않아 공유 이미지가 비는 것을 확인(제품 결함 아님).
- **발견 7건(전부 발주, 직접 수정 없음)**: S-1 전망 노트가 잘린 0.0 을 써서 거짓 개선 인쇄(예별 「+41.8%p」·롯데 기본자본 「+5.4%p」, 실제 −0.24/+4.77, −1.57%p) · S-2 같은 노트의 음수 ASCII 마이너스(△ 규칙 위반) · S-3 375px 도넛 툴팁 폭 초과 6사(329·341·349 대 캔버스 325; 글자까지 잘리는 곳은 푸본·동양·농협손해) · S-4 「경과조치 기발행 후순위」가 인쇄값이라 신규채 포함 · S-5 DB손보 제1·2회 콜일자 엇갈림(발행사 문서끼리도 불일치; 셀의 금액 짝 의심) · S-6 기본자본 인정한도를 33사가 15% 로 인쇄(정의는 10% 원칙) · S-7 하나손해 원장 미갱신(총발행액 1,000억 대 항목 6 1,999억). 발주: publishing `20261012T2235Z`(S-4~S-7 + 분류 결정 4건), designer `20261012T2236Z`(S-1~S-3).
- **한계**: 전망은 7사 손계산 + 46사 내부 정합까지이고 나머지 사의 콜 사다리는 원장을 믿는다(원장 47행 중 22행이 2025-12-31 기준; 한화생명은 반기 잔액표로 일치 확인, 하나손해만 간극). 공유 이미지·실제 호버는 창이 보이는 구간에서만 확인했다. 툴팁 폭은 Pretendard 로드 상태의 값이라 글꼴이 다르면 수 px 달라진다. 규정 쪽은 별표22·해설서 PDF 쪽수로 읽었고(`a1_*`), 발행사 서류 해석이 필요한 4건은 판정하지 않고 owner 결정으로 올렸다.
- **모델**: Sonnet 5.5, 토큰 약 1.4M(전 구간), 소요시간은 오케스트레이터 측정.

"""
t = t.replace(marker, entry.replace("\n", nl) + marker, 1) if nl == "\n" else t.replace(marker, entry.replace("\n", nl) + marker, 1)
t = t.replace("> Last updated: 2026-10-12 (26차 골든 갱신 + AIG R3 등재)", "> Last updated: 2026-10-12 (27차 소진율·전망 복원 독립 감사)", 1)
open(p, "wb").write(t.encode("utf-8"))
print("ok newline", repr(nl))
