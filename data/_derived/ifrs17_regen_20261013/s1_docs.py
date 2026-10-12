# -*- coding: utf-8 -*-
"""TODO_publishing.md Status rotation (new bullet on top, oldest verbatim to the archive) + changelog entry. usage: s1_docs.py <artifact-commit-hash>"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
H = sys.argv[1]


def rd(p):
    b = (ROOT / p).read_bytes().decode("utf-8")
    return b.replace("\r\n", "\n"), "\r\n" in b


def wr(p, t, crlf):
    (ROOT / p).write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))


t, crlf = rd("TODO_publishing.md")
lines = t.split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith("## Status"))
end = next(i for i, l in enumerate(lines) if l.startswith("## 열린 일"))
blocks, cur = [], []
for l in lines[start + 1:end]:
    if l.startswith("- **") and cur:
        blocks.append(cur)
        cur = []
    cur.append(l)
blocks.append(cur)
blocks = [b for b in blocks if any(x.strip() for x in b)]
new = [
    f"- **2026-10-13 parser-ifrs17 `b8c37fff`(249 셀) 파생 산출물 재생성(커밋 `{H}` · push 보류)** — RED NB_VS_WATERFALL(메리츠 2023.3Q) 해소: `NB_CSM_multiple.json` 12칸(동양 2023.1Q·2Q, 메리츠 2023.3Q·4Q) · `data/compare/panel_compare.json` 69잎(63 = b8c37fff·NB, 6 = 기존 낡음) · `data/csm_combo/panel_csm_combo.json` 8잎 · xlsx `신계약CSM배수` 12칸 · 공개본 `신계약CSM배수`. `viz_build_ifrs17_panels`·`viz_build_csm_waterfall` 은 `data/dart/extracted` 를 읽어 재실행해도 HEAD 와 바이트 동일(변경 없음).",
    "  남은 것: ① validation: viz 골든 2종·IFRS17 골든(이 커밋 뒤에 실행) ② 증빙 `data/_derived/ifrs17_regen_20261013/`.",
    "",
]
kept = blocks[:2]
dropped = blocks[2:]
newbody = [""] + new
for b in kept:
    newbody += b if (b and b[-1] == "") else b + [""]
wr("TODO_publishing.md", "\n".join(lines[:start + 1] + newbody + lines[end:]).replace("> 갱신 2026-10-12 ·", "> 갱신 2026-10-13 ·", 1), crlf)

a, acrlf = rd("docs/todo_archive_publishing.md")
al = a.split("\n")
ins = []
for b in dropped:
    ins += b if (b and b[-1] == "") else b + [""]
wr("docs/todo_archive_publishing.md", "\n".join(al[:2] + ins + al[2:]), acrlf)

c, ccrlf = rd("docs/changelog_publishing.md")
entry = f"""## 2026-10-13 — parser-ifrs17 `b8c37fff` 파생 산출물 재생성 (NB 배수 · 비교 패널 · CSM 콤보 · xlsx/공개본, 커밋 `{H}` + 공개본 커밋, 커밋만 · push 보류)

- 배경: `b8c37fff` 가 `CSM_waterfall`·`PL_breakdown`·`IFRS17_BS` 의 249셀을 고쳤으나 파생 파일을 다시 만들지 않아 `validate_live_artifacts` RED `NB_VS_WATERFALL` 메리츠 2023.3Q(NB 12,346.8 대 워터폴 12,197.6).
- 재생성(확립된 빌더만, 마스터는 안 씀): `build_nb_csm_multiple.py` -> `NB_CSM_multiple.json` **12칸**(동양 2023.1Q 신계약CSM 1,762.7 -> 1,762.9 · 2023.2Q 당분기 1,825.1 -> 1,824.9, 메리츠 2023.3Q 12,346.8 -> 12,197.6 · 2023.4Q 당분기 3,659.7 -> 3,808.9 과 배수). `viz_build_compare_panel.py` -> `data/compare/panel_compare.json` **69잎**(재구성 시험 `z2_attribute_panels.py`: 63잎 = b8c37fff + NB, 6잎 = b8c37fff 이전부터 낡아 있던 현대해상·삼성생명 지표). `viz_build_csm_combo_panel.py` -> `data/csm_combo/panel_csm_combo.json` **8잎**(메리츠·동양·흥국화재 2023 분기 CSM 4칸 + `est_unreliable` 명단 1사 교체). xlsx `신계약CSM배수` 12칸 `sync_master_xlsx_sheet.py` 시트 반영, 공개본 `신계약CSM배수`·manifest 재생성.
- 변경 없음(재실행으로 확인): `viz_build_ifrs17_panels.py`(csm_amort_schedule · insurance_pl_breakdown · bs_snapshot · sensitivity_heatmap) 와 `viz_build_csm_waterfall.py` 는 `data/dart/extracted` 를 읽어 산출이 HEAD 와 바이트 동일. 손해율·유지율·`data/company_segment.json` 은 이 마스터들을 티커 조회로만 읽어 재생성 대상 아님. `downstream_kpis.json` 은 어느 화면도 안 읽어 건드리지 않음(기존 보류).
- 크기: 지시한 249셀 범위 안(NB 12칸 + 패널은 그 파생값). 249셀 밖의 큰 변동 없음; 단 `panel_compare` 의 6잎은 이전부터 낡은 상태였다.
"""
marker = "---\n\n"
i = c.index(marker) + len(marker)
wr("docs/changelog_publishing.md", c[:i] + entry + "\n" + c[i:], ccrlf)
print("ok", len(dropped), "bullet(s) archived")
