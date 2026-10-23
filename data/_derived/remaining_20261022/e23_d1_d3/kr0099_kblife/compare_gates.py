"""Read-only: compare two gate-run folders (gates_before vs gates_after) produced by run_gates.sh / gate_overlay.py.

Usage: python compare_gates.py <before_dir> <after_dir> [out_txt]
Prints, per gate, the summary lines and the set difference of findings.
data_contract findings are parsed from lines like:
    "  RED    [CSM_waterfall] RULE_NAME  교보생명보험 2023.4Q"
    "  YELLOW [PL_breakdown] CSM_AMORT_IDENTITY_PINNED  교보생명보험 2026.1Q"
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

FIND_RE = re.compile(r"^\s{2}(RED|YELLOW)\s+\[([^\]]+)\]\s+(\S+)\s+(\S+)\s+(\S+)")


def read(p):
    return Path(p).read_text(encoding="utf-8", errors="replace").splitlines()


def findings(lines):
    out = []
    for ln in lines:
        m = FIND_RE.match(ln)
        if m:
            out.append(m.groups())
    return out


def summary_lines(lines, keys=("SUMMARY", "RED=", "flagged=", "pass=", "tested=", "RED (raw", "CSM COVERAGE")):
    return [ln.strip() for ln in lines if any(k in ln for k in keys)]


def main():
    b, a = Path(sys.argv[1]), Path(sys.argv[2])
    out = []

    def emit(s=""):
        out.append(s)
        print(s)

    for g in ("master_tables", "data_contract", "csm_continuity", "csm_waterfall", "nb_csm", "csm_coverage", "live_artifacts"):
        fb, fa = b / f"{g}.txt", a / f"{g}.txt"
        if not fb.exists() or not fa.exists():
            emit(f"## {g}: missing file(s)")
            continue
        lb, la = read(fb), read(fa)
        emit("=" * 90)
        emit(f"## {g}")
        emit(f"  head(before): {read(b / (g + '.log'))[0][:230]}")
        emit(f"  head(after) : {read(a / (g + '.log'))[0][:230]}")
        sb, sa = summary_lines(lb), summary_lines(la)
        if sb != sa:
            emit("  summary lines differ:")
            for s in sb[-4:]:
                emit("    - B: " + s[:420])
            for s in sa[-4:]:
                emit("    + A: " + s[:420])
        else:
            emit("  summary lines identical: " + (sb[-1][:300] if sb else "(none)"))
        if g == "data_contract":
            fb_, fa_ = findings(lb), findings(la)
            nb_red = sum(1 for f in fb_ if f[0] == "RED")
            na_red = sum(1 for f in fa_ if f[0] == "RED")
            emit(f"  parsed findings: before RED={nb_red} YELLOW={len(fb_) - nb_red} | after RED={na_red} YELLOW={len(fa_) - na_red}")
            sb_, sa_ = set(fb_), set(fa_)
            for f in sorted(sb_ - sa_):
                emit("    removed: " + " | ".join(f))
            for f in sorted(sa_ - sb_):
                emit("    ADDED  : " + " | ".join(f))
        else:
            # generic line diff restricted to KR0073/교보 mentions and FAIL/RED/NEW lines
            kb = {ln.strip() for ln in lb if ("KB라이프" in ln or "KR0099" in ln or "FAIL" in ln or "RED" in ln)}
            ka = {ln.strip() for ln in la if ("KB라이프" in ln or "KR0099" in ln or "FAIL" in ln or "RED" in ln)}
            for ln in sorted(kb - ka):
                emit("    removed: " + ln[:300])
            for ln in sorted(ka - kb):
                emit("    ADDED  : " + ln[:300])
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
