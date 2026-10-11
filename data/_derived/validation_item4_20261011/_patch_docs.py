import re
# ---- TODO_validation.md
p = "TODO_validation.md"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
s = raw.decode("utf-8").replace("\r\n", "\n")
start = s.index("- **2026-10-10 (20차)")
end = s.index("\n## 열린 일")
block20 = s[start:end].rstrip("\n")
s = s[:start] + s[end:]  # drop oldest
# fix blank line before ## 열린 일
s = s.replace("\n\n\n## 열린 일", "\n\n## 열린 일")
new_status = '''- **2026-10-11 (23차) 항목 4 주석 계보 허용 + owner 승인 등재 4칸 — 데이터계약 RED 34→11(PL 범위 24 소멸·신규 0)** — `PL_FS_NOTE_LINEAGE`(how=fs_note_csm_amort, 항목 4 한정)로 §3d 20건,
  ZERO_LEGS 23→9(src_na zleg 181→195 복귀), 법인세 0 등재 3칸(`user_pl_confirmed_cells.json`)·하노버 2025.3Q PL `MASTER_HOLE` 원천부재 장치 `_PL_SOURCE_ABSENT`(읽는 쪽 `coverage_holes(source_absent=)`).
  변이시험 신규 pytest 36건 + selftest 87→92 통과. 골든 `--update` 안 함(움직이는 것: `test_master_tables_golden` 1종). 커밋 1건, push 안 함. 남은 것: 최종 라운드 `--update`.
'''
s = s.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + new_status, 1)
s = s.replace("> 갱신 2026-10-11 (22차)", "> 갱신 2026-10-11 (23차)")
open_item = '''- [ ] **서울보증 PL `HOLE-PL` 2024.2Q·2024.3Q (통째) 2건** — `validate_master_tables` 0번 절에만 남는다(표시 분기 밖이라 데이터계약 RED 아님). KR0150 옛 분기 공시는 사이트가 내려 `NO_RAW_PDF` 최종 —
  PL 원천부재 장치 `_PL_SOURCE_ABSENT` 에 등재할지는 owner 결정(23차 티켓은 하노버 1칸만 승인, 신규 등재 안 함).
'''
s = s.replace("## 열린 일\n\n", "## 열린 일\n\n" + open_item, 1)
open(p, "wb").write(s.replace("\n", nl).encode("utf-8"))

# ---- archive
pa = "docs/todo_archive_validation.md"
raw = open(pa, "rb").read()
nl2 = "\r\n" if b"\r\n" in raw else "\n"
t = raw.decode("utf-8").replace("\r\n", "\n")
marker = "# TODO archive — `TODO_validation.md` (Status 이력, 읽기 지연)\n"
assert t.startswith(marker)
t = marker + "\n## 2026-10-11 Status 밀림 (23차 추가로 밀려난 항목, 무수정)\n\n" + block20 + "\n" + t[len(marker):]
open(pa, "wb").write(t.replace("\n", nl2).encode("utf-8"))
print("ok")
