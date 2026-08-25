# -*- coding: utf-8 -*-
"""CSM 워터폴 단위판별 휴리스틱 전수 감사 (read-only, 파일 미기록).

`scripts/build_csm_waterfall_master.py::waterfall_for_dir` L957 은 표의 **단위 리터럴을 안 읽고**
크기로 추정한다:

    udiv = 1e6 if mag > 1e10 else (1e3 if mag > 1e8 else 1.0)   # 원/천원 -> 백만

그래서 안전조건이 이렇게 갈린다:
  * 천원 표  -> 진짜 값이 1,000억 초과 ~ 10조 이하일 때만 맞다
  * 원 표    -> 진짜 값이 100억 초과일 때만 맞다
  * 백만원 표 -> 항상 맞다
규모가 줄어드는 회사는 언젠가 임계를 넘어가며 조용히 1000배가 된다(AIG 2025.4Q 실측).

이 스크립트는 raw 디렉터리 전부에 대해
  (1) `blocks_for_dir()` + `waterfall()` 만 호출해(= `main()` 미실행) 나눗셈 **적용 전** mag 와
      heuristic 이 고를 udiv 를 뽑고,
  (2) 같은 XML 에서 CSM 차이조정표 캡션 **직전**의 `(단위: X)` 리터럴 + 문서 전체 단위
      히스토그램을 뽑아
대조한다. MISMATCH = 표가 선언한 단위와 코드가 가정한 단위가 다름 = 1000배 오차 후보.

usage:
    python scripts/_probes/probe_20260825_csm_unit_heuristic_sweep.py [회사명조각 ...]
"""
from __future__ import annotations

import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_csm_waterfall_master as bcm  # noqa: E402  (read-only import; main() 미호출)

UNIT_RE = re.compile(r"단위\s*[:：]\s*(원|천원|백만원|십억원|억원)")
CAPS = ["측정요소별 변동", "측정요소별변동", "차이조정", "보험계약마진의 변동",
        "보험계약마진 변동", "보험계약부채(자산)의 변동"]
EXPECT = {1.0: "백만원", 1000.0: "천원", 1000000.0: "원"}


def stripped(path: Path) -> str:
    raw = path.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        t = raw.decode("cp949", errors="replace")
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t)
    return re.sub(r"\s+", " ", t)


def unit_evidence(rd: Path):
    """(캡션 직전 단위 집합, 문서 전체 단위 히스토그램)."""
    near: set[str] = set()
    hist: Counter = Counter()
    for x in sorted(rd.glob("*.xml")):
        if x.name.endswith("_00761.xml"):     # blocks_for_dir 가 버리는 연결 주석
            continue
        txt = stripped(x)
        units = [(m.start(), m.group(1)) for m in UNIT_RE.finditer(txt)]
        hist.update(u for _, u in units)
        for cap in CAPS:
            for m in re.finditer(re.escape(cap), txt):
                prev = [u for pos, u in units if pos < m.start()]
                if prev:
                    near.add(prev[-1])
    return near, hist


def main() -> int:
    filters = sys.argv[1:]
    dirs = [d for d in sorted(ROOT.glob("data/dart/FY*/raw/*"))
            if d.is_dir() and any(d.glob("*.xml"))]
    if filters:
        dirs = [d for d in dirs if any(f in d.name for f in filters)]

    t0 = time.time()
    verdicts: Counter = Counter()
    bad: list[str] = []
    print(f"dirs={len(dirs)}")
    print("FY\tcode\tname\tmag\tudiv\t가정단위\t캡션직전선언\t문서히스토그램\t판정\t기말(억)")
    for d in dirs:
        fy = d.parent.parent.name
        m = re.match(r"(KR\d+)_([^_]+)", d.name)
        code, name = (m.group(1), m.group(2)) if m else ("?", d.name)
        try:
            blocks = bcm.blocks_for_dir(d, name)
            if not blocks:
                verdicts["NO-BLOCKS"] += 1
                continue
            wf, _src = bcm.waterfall(blocks, None, code)
        except Exception as e:                                   # noqa: BLE001
            verdicts["ERR"] += 1
            print(f"{fy}\t{code}\t{name}\tERR\t{type(e).__name__}: {e}")
            continue
        if not wf:
            verdicts["NO-WF"] += 1
            continue
        mag = max((abs(v) for v in wf.values() if v is not None), default=0.0)
        udiv = 1_000_000.0 if mag > 1e10 else (1_000.0 if mag > 1e8 else 1.0)
        exp = EXPECT[udiv]
        near, hist = unit_evidence(d)
        tot = sum(hist.values())
        share = hist.get(exp, 0) / tot if tot else 0.0
        if not near and not hist:
            v = "NO-UNIT-LITERAL"
        elif near:
            v = "OK" if exp in near else "MISMATCH"
        else:
            v = "OK(doc)" if share >= 0.25 else "MISMATCH(doc)"
        verdicts[v] += 1
        line = (f"{fy}\t{code}\t{name}\tmag={mag:.6g}\tudiv={udiv:g}\t{exp}\t"
                f"{'|'.join(sorted(near)) or '-'}\t"
                f"{','.join(f'{k}x{n}' for k, n in hist.most_common()) or '-'}\t{v}\t"
                f"{(wf.get(6) or 0) / udiv / 100.0:.1f}")
        if v.startswith("MISMATCH"):
            bad.append(line)
        print(line)

    print()
    print("=" * 92)
    print(f"판정 집계 ({time.time() - t0:.0f}s):", dict(verdicts))
    print("=" * 92)
    for line in bad:
        print("  MISMATCH  " + line)
    print("\n  MISMATCH = 표가 선언한 단위 != 코드가 가정한 단위. 마스터가 이미 gold "
          "(user_csm_cells.json set/exclude_companies) 로 덮여 있어도 코드는 그대로다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
