"""Census for inbox 20260831T0700Z: classify the three docling failure forms.

For every FY2026_Q2 md_inbox MD:
  * read frontmatter (source_page_ranges / keyword_hit_pages / parse_spec_hash)
  * recompute the CURRENT parse_spec_hash (tells us which MDs are stale wrt the
    keyword-list fixes and would actually be re-converted)
  * scan the raw PDF with BOTH pypdf (what _find_keyword_pages uses) and fitz
    (ground truth) for the required K-ICS section anchors
  * classify each (company, anchor):
      FORM_A  anchor page exists in PDF but is NOT inside source_page_ranges
      FORM_C  anchor page IS inside source_page_ranges (and/or hit pages) but the
              anchor text never appears in the MD body
      OK      anchor present in MD
      NO_SRC  anchor not found in the raw PDF at all (scan/legit-absent)

Output: JSON to data/_derived/_probe_docling_3forms_census.json + stdout table.
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from solvency.parser import docling_parser as DP  # noqa: E402

PERIOD = "FY2026_Q2"
MD_DIR = REPO / "md_inbox" / PERIOD
PDF_DIR = REPO / "data" / "disclosure" / PERIOD / "pdf"

# Anchors: (key, regex over whitespace-stripped text)
ANCHORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("6-4_시장위험", re.compile(r"6-4\.?\s*시장위험")),
    ("금리위험액현황", re.compile(r"금리위험액\s*현황")),
    ("주식위험액현황", re.compile(r"주식위험액\s*현황")),
    ("부동산위험액현황", re.compile(r"부동산위험액\s*현황")),
    ("외환위험액현황", re.compile(r"외환위험액\s*현황")),
    ("자산집중위험액현황", re.compile(r"자산집중위험액\s*현황")),
    ("6-8_위험민감도", re.compile(r"6-8\.?\s*위험\s*민감도")),
    ("금리민감도", re.compile(r"금리\s*민감도")),
)


def _norm(s: str) -> str:
    return "".join(s.split())


def _read_front(md: Path) -> tuple[dict[str, str], str]:
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    _, _, rest = text.partition("---\n")
    front, _, body = rest.partition("\n---\n")
    meta: dict[str, str] = {}
    for raw in front.splitlines():
        if ":" not in raw:
            continue
        k, _, v = raw.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    return meta, body


def _ranges_to_set(spec: str) -> set[int]:
    out: set[int] = set()
    for chunk in (spec or "").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, _, b = chunk.partition("-")
            try:
                out.update(range(int(a), int(b) + 1))
            except ValueError:
                continue
        else:
            try:
                out.add(int(chunk))
            except ValueError:
                continue
    return out


def main() -> int:
    import fitz  # PyMuPDF
    from pypdf import PdfReader

    rows = []
    for md in sorted(MD_DIR.glob("*.md")):
        meta, body = _read_front(md)
        code = meta.get("company_code", "")
        if not code:
            continue
        pdf = PDF_DIR / f"{meta.get('company_dirname', md.stem)}.pdf"
        if not pdf.exists():
            cands = list(PDF_DIR.glob(f"{code}_*.pdf"))
            pdf = cands[0] if cands else None
        if pdf is None:
            rows.append({"company": code, "error": "no_pdf"})
            continue

        item = DP.PdfInput(
            company_code=code,
            company_dirname=pdf.stem,
            period=PERIOD,
            pdf_path=pdf.resolve(),
        )
        cur_spec = DP._parse_spec_hash(item)

        sel = _ranges_to_set(meta.get("source_page_ranges", ""))
        hits = {
            int(x) for x in (meta.get("keyword_hit_pages", "") or "").split(",") if x.strip().isdigit()
        }

        doc = fitz.open(str(pdf))
        total_fitz = doc.page_count
        fitz_pages = []
        for i in range(total_fitz):
            fitz_pages.append(_norm(doc.load_page(i).get_text() or ""))
        doc.close()

        # pypdf text (what the keyword scanner actually sees)
        try:
            reader = PdfReader(str(pdf))
            pypdf_pages = [_norm(p.extract_text() or "") for p in reader.pages]
        except Exception as exc:  # noqa: BLE001
            pypdf_pages = []
            print(f"  !! pypdf failed {code}: {exc}")

        nbody = _norm(body)
        anchor_rows = {}
        for key, pat in ANCHORS:
            pdf_pages = [i + 1 for i, t in enumerate(fitz_pages) if pat.search(t)]
            in_md = bool(pat.search(nbody))
            if not pdf_pages:
                verdict = "OK_MD_ONLY" if in_md else "NO_SRC"
            elif in_md:
                verdict = "OK"
            elif any(p in sel for p in pdf_pages):
                verdict = "FORM_C"  # selected but content missing from MD
            else:
                verdict = "FORM_A"  # never selected
            anchor_rows[key] = {
                "pdf_pages": pdf_pages,
                "in_selected": [p for p in pdf_pages if p in sel],
                "in_hitpages": [p for p in pdf_pages if p in hits],
                "in_md": in_md,
                "verdict": verdict,
                # does pypdf even see the anchor text on that page?
                "pypdf_sees": [
                    p for p in pdf_pages if pypdf_pages and p <= len(pypdf_pages) and pat.search(pypdf_pages[p - 1])
                ],
            }

        # per-page text-density comparison pypdf vs fitz (scan detection + backend gap)
        dens_fitz = sum(len(t) for t in fitz_pages) / max(1, total_fitz)
        dens_pypdf = (sum(len(t) for t in pypdf_pages) / max(1, len(pypdf_pages))) if pypdf_pages else 0.0

        rows.append(
            {
                "company": code,
                "dirname": pdf.stem,
                "run_id": meta.get("run_id", ""),
                "spec_stored": meta.get("parse_spec_hash", ""),
                "spec_current": cur_spec,
                "spec_stale": meta.get("parse_spec_hash", "") != cur_spec,
                "total_pages": total_fitz,
                "selected_pages": len(sel),
                "coverage_ratio": round(len(sel) / max(1, total_fitz), 4),
                "n_hit_pages": len(hits),
                "hit_cap_saturated": len(hits) >= 20,
                "source_page_ranges": meta.get("source_page_ranges", ""),
                "density_fitz": round(dens_fitz, 1),
                "density_pypdf": round(dens_pypdf, 1),
                "anchors": anchor_rows,
            }
        )

    out = REPO / "data" / "_derived" / "_probe_docling_3forms_census.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n=== {PERIOD} docling window census ({len(rows)} companies) ===\n")
    hdr = f"{'code':<8}{'pages':>6}{'sel':>5}{'cov':>7}{'hits':>5}{'stale':>7}  {'dens f/p':>13}  anchors"
    print(hdr)
    print("-" * 150)
    tally: dict[str, int] = {}
    for r in sorted(rows, key=lambda x: x.get("company", "")):
        if r.get("error"):
            print(f"{r['company']:<8} ERROR {r['error']}")
            continue
        bad = []
        for k, a in r["anchors"].items():
            tally[a["verdict"]] = tally.get(a["verdict"], 0) + 1
            if a["verdict"] in ("FORM_A", "FORM_C"):
                bad.append(f"{k}:{a['verdict']}@{a['pdf_pages']}")
        print(
            f"{r['company']:<8}{r['total_pages']:>6}{r['selected_pages']:>5}"
            f"{r['coverage_ratio']:>7.2f}{r['n_hit_pages']:>5}"
            f"{'STALE' if r['spec_stale'] else '-':>7}"
            f"  {r['density_fitz']:>6.0f}/{r['density_pypdf']:<6.0f}  " + ("; ".join(bad) if bad else "clean")
        )
    print("\nverdict tally:", json.dumps(tally, ensure_ascii=False))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
