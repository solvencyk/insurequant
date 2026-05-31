# -*- coding: utf-8 -*-

"""Extract IFRS 17 contract assumption-sensitivity tables from K-ICS quarterly MD.



Section headers typically include contiguous ``가정민감도``, ``4-6-5)`` / ``5)`` lines,

hyphen bullets ``- (5)``, or appendix titles combining ``보험위험`` and ``민감도``.



Stops before solvency shock blocks like ``6-8.`` risk sensitivity.



Output rows match ``sensitivity_extractor.to_jsonable()`` shape.

"""

from __future__ import annotations


import json

import re

from dataclasses import dataclass, field

from pathlib import Path


from .insurance_pl_extractor import _first_col_labels, _flat_header

from .sensitivity_extractor import (
    ExtractedSensitivityTable,
    _classify_kind,
    _score_table,
    is_mvp_table,
    to_jsonable,
)

from .universe import is_excluded


_SENS = "\uac00\uc815\ubbfc\uac10\ub3c4"

# IFRS17 contract grid section title may omit the word \uac815 (e.g. Appendix (10) title).

_BOHEOM_WIHEOM = "\ubcf4\ud5d8\uc704\ud5d8"

_MINGAMDO = "\ubbfc\uac10\ub3c4"


def load_kics_code_to_name(repo_root: Path) -> dict[str, str]:

    path = repo_root / "kics_disclosure.json"

    data = json.loads(path.read_text(encoding="utf-8"))

    out: dict[str, str] = {}

    for row in data:
        code = row.get("\uc6d0\ubcf4\ud5d8\uc0ac\ucf54\ub4dc")

        name = row.get("\uc6d0\uc218\uc0ac\uba85")

        if code and name:
            out[str(code)] = name

    return out


def operational_insurer_pairs(repo_root: Path) -> list[tuple[str, str]]:

    m = load_kics_code_to_name(repo_root)

    return [(c, m[c]) for c in sorted(m) if not is_excluded(m[c])]


def ifrs17_measurement_ok_insurers(repo_root: Path) -> list[tuple[str, str]]:

    path = (
        repo_root / "data" / "dart" / "extracted" / "_batch_measurement_summary.json"
    )

    rows = json.loads(path.read_text(encoding="utf-8"))

    cmap = load_kics_code_to_name(repo_root)

    inv: dict[str, str] = {}

    for c, n in cmap.items():
        inv[n] = c

    out: list[tuple[str, str]] = []

    for r in rows:
        if r.get("status") != "ok":
            continue

        kn = r["kics_name"]

        code = inv.get(kn)

        if code is None:
            continue

        out.append((code, kn))

    out.sort(key=lambda x: x[0])

    return out


_END_PATTERNS = (
    re.compile(r"^##\s*\u2164[\s\.\u3000]"),
    re.compile(r"^#{1,3}\s*[6-9]\d?\)\s"),
    re.compile(r"^#{1,3}\s*4-6-[6-9]"),
    re.compile(r"^#{1,3}\s*6-8[\.\)]"),
    re.compile(r"^\s*-\s*\(\s*6\s*\)"),
    re.compile(r"^\s*[\u2022\u00b7]\s*\(\s*6\s*\)"),
)


_SOLVENCY_ONLY = (
    "\uc9c0\uae09\uc5ec\ub825\uae08\uc561",
    "\uc9c0\uae09\uc5ec\ub825\uae30\uc900\uae08\uc561",
    "\uae30\ubcf8\uc694\uad6c\uc790\ubcf8",
)


def _compact_heading(s: str) -> str:

    return re.sub(r"\s+", "", s)


def _has_compact_gajeong_mingamdo(compact_line: str) -> bool:
    """\uac00\uc815\ubbfc\uac10\ub3c4 contiguous, or \uac00\uc815 near \ubbfc\uac10\ub3c4 (spaced heading)."""

    if _SENS in compact_line:
        return True

    i = compact_line.find("\uac00\uc815")

    if i < 0:
        return False

    return "\ubbfc\uac10\ub3c4" in compact_line[i : i + 32]


def _is_section_start(line: str) -> bool:

    s = line.strip()

    if s.startswith("\u203b") or s.startswith("\uc8fc") or s.startswith("*"):
        return False

    compact = _compact_heading(s)

    has_gmj = _has_compact_gajeong_mingamdo(compact)

    if s.startswith("#"):
        if has_gmj:
            return True

        # Appendix: "\ubcf4\ud5d8\uc704\ud5d8 ... \ubbfc\uac10\ub3c4" (not solvency-only "\uc704\ud5d8 \ubbfc\uac10\ub3c4").

        if _BOHEOM_WIHEOM in compact and _MINGAMDO in compact:
            return True

        return False

    if re.match(r"^[-*\u2022\u00b7]\s*\(\s*5\s*\)\s", s):
        return has_gmj

    return False


def _is_section_end(line: str) -> bool:

    s = line.strip()

    return any(pat.match(s) for pat in _END_PATTERNS)


def _find_spans(lines: list[str]) -> list[tuple[int, int]]:

    spans: list[tuple[int, int]] = []

    n = len(lines)

    i = 0

    while i < n:
        if _is_section_start(lines[i]):
            start = i

            j = start + 1

            while j < n and not _is_section_end(lines[j]):
                j += 1

            spans.append((start, j))

            i = j

        else:
            i += 1

    return spans


def _split_table_block(
    raw_rows: list[list[str]],
) -> tuple[list[list[str]], list[list[str]]]:

    if not raw_rows:
        return [], []

    if len(raw_rows) == 1:
        return raw_rows, []

    r0, r1 = raw_rows[0], raw_rows[1]

    if len(r0) == len(r1):
        if r0 and r1 and r0[0] == r1[0] and (len(r0) < 2 or r0[1] == r1[1]):
            return raw_rows[:2], raw_rows[2:]

    return [raw_rows[0]], raw_rows[1:]


def _looks_like_separator(line: str) -> bool:

    s = line.strip()

    if not s.startswith("|"):
        return False

    core = s.replace("|", "").replace(":", "").replace("-", "").replace(" ", "")

    return len(core) == 0


def _parse_row(line: str) -> list[str]:

    return [c.strip() for c in line.strip().strip("|").split("|")]


def _iter_tables_in_lines(
    lines: list[str], base_line_no: int
) -> list[tuple[int, list[list[str]], str]]:

    i = 0

    out: list[tuple[int, list[list[str]], str]] = []

    while i < len(lines):
        if not lines[i].strip().startswith("|"):
            i += 1

            continue

        start_i = i

        rows: list[list[str]] = []

        while i < len(lines) and lines[i].strip().startswith("|"):
            if _looks_like_separator(lines[i]):
                i += 1

                continue

            rows.append(_parse_row(lines[i]))

            i += 1

        if not rows:
            continue

        caption = _caption_before(lines, start_i)

        abs_line = base_line_no + start_i

        out.append((abs_line, rows, caption))

    return out


def _caption_before(lines: list[str], table_start: int) -> str:

    buf: list[str] = []

    j = table_start - 1

    while j >= 0:
        s = lines[j].strip()

        if not s:
            if buf:
                break

            j -= 1

            continue

        if s.startswith("|"):
            break

        buf.append(s)

        j -= 1

    buf.reverse()

    return " ".join(x for x in buf if x)[:2000]


def _joined_header_cells(header: list[list[str]]) -> str:

    return " ".join(c for row in header for c in row)


def _is_contract_sensitivity_grid(
    header: list[list[str]], body: list[list[str]]
) -> bool:

    h = _joined_header_cells(header)

    bjoin = " ".join(" ".join(r) for r in body[:25])

    blob = h + " " + bjoin

    blob_compact = blob.replace(" ", "")

    lic_flow = "\uc774\ud589 \ud604\uae08\ud758\ub984".replace(" ", "")

    csm_phrase = "\ubcf4\ud5d8\uacc4\uc57d\ub9c8\uc9c4"

    if any(k in blob for k in _SOLVENCY_ONLY):
        if csm_phrase.replace(" ", "") not in blob_compact:
            return False

    if ("\uc774\ud589" in blob and "\ud604\uae08" in blob) and (
        "\ub9c8\uc9c4" in blob or "\uacc4\uc57d\ub9c8\uc9c4" in blob
    ):
        return True

    if lic_flow in blob_compact or "\uc774\ud589\ud604\uae08" in blob_compact:
        if "\ub9c8\uc9c4" in blob_compact:
            return True

    if "\uc794\uc5ec\ubcf4\uc7a5" in blob and "\ubbfc\uac10\ub3c4" in blob:
        return True

    if "\ubcc0\ub3d9\uae08\uc561" in blob and (
        "\uc774\ud589" in h or "\ud604\uae08" in h
    ):
        if "\ub9c8\uc9c4" in h:
            return True

    if "\uae08\ub9ac\uc704\ud5d8" in blob and "\ubcf4\ud5d8\uacc4\uc57d" in blob:
        if "100bp" in blob or "100 bp" in blob.lower():
            return True

    return False


@dataclass
class MdExtractResult:
    tables: list[dict] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)

    section_spans: list[tuple[int, int]] = field(default_factory=list)


def extract_kics_sensitivity_from_md(
    md_text: str,
    company_name: str,
    *,
    min_score: int = 3,
    mvp_only: bool = False,
) -> MdExtractResult:

    lines = md_text.splitlines()

    spans = _find_spans(lines)

    result = MdExtractResult(section_spans=[(s + 1, e + 1) for s, e in spans])

    for s, e in spans:
        chunk = lines[s:e]

        tables = _iter_tables_in_lines(chunk, base_line_no=s + 1)

        for line_no, grid, caption in tables:
            header_rows, body = _split_table_block(grid)

            if not body:
                continue

            if not _is_contract_sensitivity_grid(header_rows, body):
                continue

            stub = ExtractedSensitivityTable(
                caption=caption,
                header=header_rows,
                rows=body,
                footnotes=[],
                line_no=line_no,
            )

            joined = (
                caption
                + _joined_header_cells(header_rows)
                + " ".join(_first_col_labels(body))
            )

            has_neg = ("\uae08\uc735\uc0c1\ud488" in joined) or (
                "\uc218\uc9003" in joined
            )

            score, block_type, slice_label, slice_policy, table_kind, reasons = (
                _score_table(
                    stub,
                    company_name,
                )
            )

            score += 2

            reasons.append("kics_md: IFRS17 contract sensitivity grid")

            stub.score = score

            stub.reasons = reasons

            stub.table_kind = (
                table_kind
                if table_kind != "unknown"
                else _classify_kind(
                    caption,
                    _first_col_labels(body),
                    _flat_header(stub),
                )
            )

            if stub.table_kind == "unknown":
                stub.table_kind = "sensitivity_analysis"

                reasons.append("kics_md: table_kind default sensitivity_analysis")

            stub.block_type = block_type

            stub.slice_label = slice_label

            stub.slice_policy = slice_policy

            if has_neg:
                stub.score = 0

                stub.mvp_candidate = False

                stub.reasons.append("skip: monetary instrument / level-3 wording")

            else:
                stub.mvp_candidate = is_mvp_table(stub)

            if stub.score < min_score:
                continue

            if mvp_only and not stub.mvp_candidate:
                continue

            result.tables.append(to_jsonable(stub))

    return result


def write_kics_sensitivity_json(path: Path, tables: list[dict], meta: dict) -> None:

    out: list[dict] = []

    for tbl in tables:
        row = dict(tbl)

        for k, v in meta.items():
            row.setdefault(k, v)

        out.append(row)

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
