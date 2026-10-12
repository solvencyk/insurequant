import warnings, glob, os, sys
warnings.simplefilter("error", SyntaxWarning)
bad = []
for d in ("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_latest_comparative_apply_audit_20261013", "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_audit_20261013"):
    for f in glob.glob(d + "/*.py"):
        try: compile(open(f, encoding="utf-8").read(), f, "exec")
        except SyntaxWarning as e: bad.append((f, str(e)))
        except SyntaxError as e: bad.append((f, "SYNTAXERR " + str(e)))
        raw = open(f, "rb").read()
        if raw.startswith(b"\xef\xbb\xbf"): bad.append((f, "BOM"))
open("p1_warn.txt", "w", encoding="utf-8").write(repr(bad))
