import subprocess, hashlib, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
b = subprocess.run(["git", "-C", R, "show", "HEAD:IFRS17_BS.json"], capture_output=True).stdout
print("HEAD blob sha", hashlib.sha256(b).hexdigest()[:8], "has CRLF:", b"\r\n" in b)
crlf = b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
print("HEAD as CRLF sha", hashlib.sha256(crlf).hexdigest()[:8])
w = open(R + "IFRS17_BS.json", "rb").read()
print("working sha", hashlib.sha256(w).hexdigest()[:8], "CRLF:", b"\r\n" in w)
for f in ["PL_breakdown.json", "CSM_waterfall.json", "CSM_amortization.json", "CSM_sensitivity.json", "NB_CSM_multiple.json", "CSM_waterfall_provenance.json", "PL_breakdown_provenance.json"]:
    hb = subprocess.run(["git", "-C", R, "show", "HEAD:" + f], capture_output=True).stdout
    wb = open(R + f, "rb").read()
    print(f, "identical to HEAD (raw)" if hb == wb else ("identical modulo EOL" if hb.replace(b"\r\n", b"\n") == wb.replace(b"\r\n", b"\n") else "DIFFERENT"))
