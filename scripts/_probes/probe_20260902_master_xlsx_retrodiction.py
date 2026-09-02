# -*- coding: utf-8 -*-
"""신설 룰 `MASTER_XLSX_*` 를 **사고 당시 워크북에 되돌려 재본다** (PM-2026-09-02 §2).

"이 룰이었으면 잡았나" 는 수사가 아니라 측정으로 답해야 한다. 2026-09-02 의 두 수정 커밋은
**xlsx 만** 건드렸으므로(각 `1 file changed`) 마스터 JSON 은 그때와 지금이 같다. 따라서
그때의 워크북을 git 에서 꺼내 **오늘의 마스터**로 대조하면, 그날 게이트가 봤어야 할 것이
그대로 재현된다.

기대(2026-09-02 실측):

    d1f1e7f~1  (두 수정 전)        RED=5   자본비율전망 DRIFT 1111 / ROW_MISSING 169 / ROW_EXTRA 169
                                          K-ICS공시   DRIFT   33 / ROW_MISSING 121
    ee11c1d~1  (자본비율전망만 고침) RED=2   K-ICS공시   DRIFT   33 / ROW_MISSING 121
    HEAD       (현재)              RED=0   (clean, 13시트 53,288행)

숫자가 두 수정 커밋이 스스로 기록한 값과 정확히 일치한다(d1f1e7f "변경 셀 1111 · 재키잉 169행",
ee11c1d "변경 셀 33 · 추가 행 121") — 즉 이 룰은 두 사고를 **사람이 발견하기 전에** 차단했을 것이다.

워크북은 임시 디렉토리로만 꺼내고 **작업트리의 xlsx 는 건드리지 않는다**(읽기 전용 게이트).

    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
        scripts/_probes/probe_20260902_master_xlsx_retrodiction.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import check_master_xlsx_drift as D        # noqa: E402

REVS = [("d1f1e7f~1", "두 수정 전", 5),
        ("ee11c1d~1", "자본비율전망만 고친 뒤", 2),
        ("HEAD", "현재", 0)]


def workbook_at(rev: str, dest: Path) -> Path:
    out = dest / f"{rev.replace('~', '_').replace('/', '_')}.xlsx"
    blob = subprocess.run(["git", "show", f"{rev}:insurequant_master_tables.xlsx"],
                          cwd=str(ROOT), capture_output=True, check=True).stdout
    out.write_bytes(blob)
    return out


def main() -> int:
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for rev, label, expect_red in REVS:
            path = workbook_at(rev, tmp)
            findings, stat = D.scan(path=path)
            red = [f for f in findings if f["severity"] == "RED"]
            ok = len(red) == expect_red
            bad += 0 if ok else 1
            print(f"\n### {rev}  ({label})   RED={len(red)} (기대 {expect_red}) "
                  f"{'OK' if ok else '<<< 불일치'}")
            print(f"    대조 행 {stat['rows_compared']} · 드리프트 셀 {stat['cells_drifted']}")
            for f in sorted(red, key=lambda f: (f["sheet"], f["rule"])):
                print(f"    {f['rule']:26s} [{f['sheet']}] count={f['count']}")
    print("\n" + "=" * 70)
    print("RETRODICTION: " + ("모든 시점이 기대와 일치" if not bad else f"{bad}개 시점 불일치"))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
