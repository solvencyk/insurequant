import re
import subprocess
import sys

def main():
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.DOTALL)
    print(f"found {len(scripts)} inline script blocks")
    for i, s in enumerate(scripts):
        tmp = f"scripts/_probes/_20260921_check_block_{i}.js"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(s)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        status = "OK" if r.returncode == 0 else "FAIL"
        print(f"block {i}: {status}")
        if r.returncode != 0:
            print(r.stderr)

if __name__ == "__main__":
    main()
