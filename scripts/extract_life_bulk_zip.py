# -*- coding: utf-8 -*-
"""생보협회 정기공시 일괄 ZIP 을 회사별 PDF 로 풀어 data/disclosure/<period>/pdf/ 에 넣는다.

협회 ZIP 안의 파일명은 회사마다 제각각이라(`FY2026 2Q_경영공시_vFF.pdf` 처럼 회사명이
아예 없는 것도 있다) 이름만으로는 못 가른다. 그래서 두 단계로 판정한다:

  1) 파일명에 회사 별칭이 있으면 그걸로 매핑한다.
  2) 없으면 PDF 첫 3페이지 텍스트에서 회사명을 찾아 매핑한다.

두 단계 다 실패하면 **추측하지 않고 unmatched 로 보고**한다. 잘못 매핑된 PDF 는
그 회사의 모든 지표를 통째로 오염시키므로, 빈칸이 낫다.

사용:
  python scripts/extract_life_bulk_zip.py --period FY2026_Q2
  python scripts/extract_life_bulk_zip.py --period FY2026_Q2 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

# 협회 ZIP 파일명 -> KR 코드. 별칭은 파일명에 실제로 나타나는 형태로 적는다.
ALIASES = {
    "KR0068": ["한화생명"],
    "KR0069": ["삼성생명"],
    "KR0070": ["에이비엘생명", "ABL생명"],
    "KR0071": ["흥국생명"],
    "KR0072": ["KDB생명", "케이디비생명"],
    "KR0073": ["교보생명"],
    "KR0074": ["라이나생명"],
    "KR0075": ["BNP파리바카디프생명", "비엔피파리바카디프생명"],
    "KR0076": ["iM라이프", "아이엠라이프", "IM라이프"],
    "KR0079": ["미래에셋생명"],
    "KR0080": ["AIA생명", "에이아이에이생명"],
    "KR0082": ["DB생명"],
    "KR0083": ["푸본현대생명"],
    "KR0087": ["동양생명"],
    "KR0094": ["신한라이프"],
    "KR0095": ["메트라이프생명"],
    "KR0097": ["하나생명"],
    "KR0099": ["KB라이프"],
    "KR0100": ["처브라이프생명"],
    "KR0104": ["농협생명"],
    "KR1010": ["교보라이프플래닛생명"],
    "KR1011": ["IBK연금보험"],
}
# 본문 판정용 별칭 (파일명보다 표기가 정식이라 별도로 둔다)
BODY_ALIASES = {c: a + [n] for c, a in ALIASES.items()
                for n in ()}  # 채움은 아래 _display_name 에서


def _display_name(code: str) -> str:
    """FY2026_Q1 raw/ 의 명명 규칙을 그대로 재사용한다(마스터 원수사명과 다를 수 있다)."""
    for pat in ("FY*/raw/%s_*.pdf", "FY*/pdf/%s_*.pdf"):
        for p in sorted((ROOT / "data" / "disclosure").glob(pat % code)):
            name = p.stem.split("_", 1)[1]
            # 과거 재제출본이 `_amended` 로 남아 있다. 그 접미사까지 물려받으면
            # 새 분기 파일이 KR0070_에이비엘생명보험_amended.pdf 로 저장된다.
            for suf in ("_amended", "_revised", "_final"):
                if name.endswith(suf):
                    name = name[: -len(suf)]
            return name
    return code


def _zip_name(raw: str) -> str:
    """ZIP 엔트리명 인코딩 복원 (협회 ZIP 은 cp437 로 들어온 euc-kr)."""
    try:
        return raw.encode("cp437").decode("euc-kr")
    except Exception:
        return raw


def _first_pages_text(data: bytes, pages: int = 0) -> str:
    """pages=0 이면 전문. 협회 ZIP 은 표지에 회사명이 없는 파일이 있다 —
    삼성생명 2026.2Q(`FY2026 2Q_경영공시_vFF.pdf`)는 회사명이 p56 에서야 처음 나온다.
    앞 3페이지만 읽던 때는 이 파일이 미매칭으로 떨어졌다."""
    try:
        import fitz
    except ImportError:
        return ""
    try:
        with fitz.open(stream=data, filetype="pdf") as d:
            n = len(d) if pages <= 0 else min(pages, len(d))
            return "".join(d[i].get_text() for i in range(n))
    except Exception:
        return ""


def _norm(s: str) -> str:
    return re.sub(r"[\s()（）_\-.]", "", s)


def match(name: str, body: str) -> tuple[str | None, str]:
    n = _norm(name)
    for code, aliases in ALIASES.items():
        for a in aliases:
            if _norm(a) in n:
                return code, "파일명:%s" % a
    b = _norm(body)
    for code, aliases in ALIASES.items():
        for a in list(aliases) + [_display_name(code)]:
            if a and _norm(a) in b:
                return code, "본문:%s" % a
    return None, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period", required=True, help="예: FY2026_Q2")
    ap.add_argument("--apply", action="store_true", help="실제로 쓴다 (기본은 dry-run)")
    args = ap.parse_args()

    zdir = ROOT / "data" / "disclosure" / args.period / "life_bulk"
    zips = sorted(zdir.glob("*.zip"))
    if not zips:
        print("[FATAL] 일괄 ZIP 이 없다: %s" % zdir)
        return 2
    out = ROOT / "data" / "disclosure" / args.period / "pdf"
    out.mkdir(parents=True, exist_ok=True)

    rows, unmatched = [], []
    for zp in zips:
        z = zipfile.ZipFile(zp)
        for entry in z.namelist():
            disp = _zip_name(entry)
            if not disp.lower().endswith(".pdf"):
                continue
            data = z.read(entry)
            code, how = match(disp, _first_pages_text(data))
            if code is None:
                unmatched.append(disp)
                continue
            dest = out / ("%s_%s.pdf" % (code, _display_name(code)))
            rows.append((code, dest.name, len(data), how, disp))
            if args.apply:
                dest.write_bytes(data)

    rows.sort()
    print("%-8s %-34s %10s  %-16s %s" % ("code", "dest", "bytes", "판정근거", "zip 안 이름"))
    for code, dest, n, how, disp in rows:
        print("%-8s %-34s %10s  %-16s %s" % (code, dest, f"{n:,}", how, disp[:46]))
    dup = [c for c in {r[0] for r in rows} if sum(1 for r in rows if r[0] == c) > 1]
    print("\n매칭 %d건 · 중복코드 %s · 미매칭 %d건" % (len(rows), dup or "없음", len(unmatched)))
    for u in unmatched:
        print("  UNMATCHED:", u)
    if not args.apply:
        print("\n(dry-run — 실제로 쓰려면 --apply)")
    else:
        (ROOT / "data" / "disclosure" / "_meta" / args.period).mkdir(parents=True, exist_ok=True)
        (ROOT / "data" / "disclosure" / "_meta" / args.period / "life_bulk_extract.json").write_text(
            json.dumps([{"code": c, "dest": d, "bytes": n, "how": h, "zip_entry": z}
                        for c, d, n, h, z in rows], ensure_ascii=False, indent=1), encoding="utf-8")
        print("\n[wrote] %d개 PDF -> %s" % (len(rows), out))
    return 0 if not unmatched and not dup else 1


if __name__ == "__main__":
    raise SystemExit(main())
