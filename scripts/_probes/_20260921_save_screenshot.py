import json
import base64

with open(
    r"C:\Users\sangwook.cho\.claude\projects\C--Users-sangwook-cho-Desktop-insurequant\8c0afc6e-aced-4947-80b1-d3bcff7ee649\tool-results\mcp-Claude_Browser-javascript_tool-1789952884779.txt",
    "r", encoding="utf-8"
) as f:
    data = json.load(f)

text = data[0]["text"]
# text is a JS string literal with surrounding quotes (JSON.stringify-style from the tool), strip if present
text = text.strip()
if text.startswith('"') and text.endswith('"'):
    text = json.loads(text)

prefix = "data:image/png;base64,"
assert text.startswith(prefix), text[:50]
b64 = text[len(prefix):]
png_bytes = base64.b64decode(b64)

out_path = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\8c0afc6e-aced-4947-80b1-d3bcff7ee649\scratchpad\kics_sens_lina_2026Q2.png"
with open(out_path, "wb") as f:
    f.write(png_bytes)
print("wrote", len(png_bytes), "bytes to", out_path)
