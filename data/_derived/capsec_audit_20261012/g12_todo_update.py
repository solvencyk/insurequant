# -*- coding: utf-8 -*-
"""g12: bookkeeping for the 29th round - (1) move the oldest Status entry of TODO_validation.md (26th round, 2 lines) VERBATIM to the top of docs/todo_archive_validation.md,
(2) insert the 29th-round Status entry on top of the list, (3) rewrite the '27차 독립 감사 후속' open item, (4) update the header line.  Newline style preserved."""
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
tp, ap = ROOT + "TODO_validation.md", ROOT + "docs/todo_archive_validation.md"
traw, araw = open(tp, "rb").read(), open(ap, "rb").read()
nl = b"\r\n" if b"\r\n" in traw[:4000] else b"\n"
anl = b"\r\n" if b"\r\n" in araw[:4000] else b"\n"
tl = traw.split(nl)
txt = [l.decode("utf-8") for l in tl]

# ---- (1) move the 26th-round entry (starts with '- **2026-10-12 (26차)', ends before the next '- **' or blank line)
i0 = [i for i, l in enumerate(txt) if l.startswith("- **2026-10-12 (26차) 골든 갱신")]
assert len(i0) == 1, i0
i = i0[0]
j = i + 1
while j < len(txt) and txt[j].startswith("  "):
    j += 1
block = tl[i:j]
print("moving %d lines (%d..%d)" % (len(block), i + 1, j))
al = araw.split(anl)
assert al[0].decode("utf-8").startswith("# TODO archive")
head, rest = al[0:2], al[2:]
section = ["## 2026-10-13 Status 밀림 (29차 소진율·전망 재측정 항목 추가로 밀려난 항목, 무수정)".encode("utf-8"), b""] + block + [b""]
new_a = anl.join(head + section + rest)
del tl[i:j]
txt = [l.decode("utf-8") for l in tl]

# ---- (2) insert the 29th-round Status entry above the 28th-round one
entry = [
    "- **2026-10-13 (29차) 소진율·전망 재측정 (티켓 `20261012T2040Z`, 대상 HEAD `6fd00720`, 읽기 전용 — 마스터·HTML·게이트 코드 무수정)** — 새 규칙(기발행 차감 = 원장 2022-12-31 이전 잔액, 콜 경과 제외)으로 보완자본 소진율 47사 독립 재계산 **47/47 일치** · 기본자본 47/47(결속 갈래 없는 33사 한도 10%, 하나생명 238.2 · 교보 70.1 · DB손보 151.6 불변) · 전망 7사 손계산 35점 차이 0(총자본·기본자본 경로 이전 판과 동일, 행 변경은 KR0050 `confidence` 뿐) · 타임라인·공개 시트 4종 불일치 0 · 화면 47사 x 1280/375 불일치 0(예별·롯데 노트 거짓 개선 제거, 툴팁 잘림 0, 공유 이미지 15사 정상).",
    "  불일치 1건: 원장 `past_call_outstanding` 가 각 행 `as_of` 기준이라 첫 콜일이 분자 기준일 이전인 3건(메리츠 2,100억 · 아이엠라이프 500억 · KB라이프 1,299.7억)이 차감에 남는다(30.8→37.5 · 56.9→70.4 · 0.0→0.8) -> publishing `20261013T0205Z`. 재현물 `data/_derived/capsec_audit_20261012/`(`h1`~`h9`·`e7`~`e10`, 기록 `h9_screen_results_6fd00720.txt`).",
    "  남은 것: publishing 답변 후 재측정(순서는 아래 열린 일) · owner 결정 잔여 5건.",
]
k = [n for n, l in enumerate(txt) if l.startswith("- **2026-10-13 (28차)")]
assert len(k) == 1, k
txt[k[0]:k[0]] = entry

# ---- (3) rewrite the open item
a = [n for n, l in enumerate(txt) if l.startswith("- [ ] **27차 독립 감사 후속**")]
assert len(a) == 1, a
b = a[0] + 1
while b < len(txt) and txt[b].startswith("  "):
    b += 1
new_open = [
    "- [ ] **29차 재측정 후속** — ① publishing `20261013T0205Z`(콜 경과 3건을 분자 기준일로 판정) 답변을 받으면 같은 순서로 재측정: `a2_dump_inputs` -> `h1_tier2_recompute_47` -> `h2_tier1_check` -> `d1_forward_handcalc` -> `d2_forward_internal_consistency` -> `h4_expected` -> `e7`~`e10` + 브라우저 `h5`·`h6`·`h7`·`h8`(사용법은 각 파일 머리 주석; 페이지가 CSP 로 `eval` 불가라 `<script src>` 주입, 유휴 창은 rAF 가 안 돌아 공유 이미지 검사는 `Chart.defaults.animation=false`).",
    "  ② owner 결정 잔여: 코리안리 제5·6회 · 농협생명 제5회 · 푸본 600억(발행사 표 X 검정으로 판정 불가) · 기본자본 두 갈래(기발행 15% / 신규 10%) 결합 규칙 · IBK TAC 위치 · 아이엠라이프 전환우선주 차감 방식(해석에 따라 16.0~70.4%) · 악사 JPY 후순위 콜일 추정 확인(29.2% 가 그 추정 위에 있다). 해소: DB손보 제1~5회 기본자본형 확정, 기발행 차감 = 원장 2022년 이전(owner 2026-10-12 밤).",
    "  ③ **전망 JSON 내부 정합 룰 제안**(게이트 코드는 이번에도 안 건드림): 모든 해 `ratio_pct = capital_eok / scr_eok x 100`(+-0.011), 어긋나면 `capacity_exhausted` 가 같이 true 일 때만 허용(`d2_forward_internal_consistency.py` 초안; 화면 쪽은 designer `scripts/check_kics_forward_note.py` 가 이미 막는다). ④ 화면 대 JSON·툴팁 폭·공유 이미지 감사는 수동 브라우저 스크립트(`h5`~`h8`)다 - 반복 도구(헤드리스)로 만들지 UH-26 과 함께 판단.",
]
txt[a[0]:b] = new_open

# ---- (4) header line
for n, l in enumerate(txt):
    if l.startswith("> 갱신 2026-10-13 (28차"):
        txt[n] = l.replace("(28차 K-ICS 최신 공시 직전 컬럼 적용 독립 검수)", "(29차 소진율·전망 재측정 + 28차 K-ICS 최신 공시 직전 컬럼 적용 독립 검수)")
        break
else:
    raise SystemExit("header line not found")
open(tp, "wb").write(nl.join(t.encode("utf-8") for t in txt))
open(ap, "wb").write(new_a)
print("done")
