# -*- coding: utf-8 -*-
import fitz, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def dump_page(path, pageno, y_round=1):
    doc = fitz.open(path)
    page = doc[pageno - 1]
    words = page.get_text("words")  # x0,y0,x1,y1,text,block,line,word_no
    # group by (block,line)
    lines = {}
    for w in words:
        x0, y0, x1, y1, text, block, line, wno = w
        key = (block, line)
        lines.setdefault(key, []).append((x0, y0, x1, y1, text))
    # sort lines by average y0
    line_items = []
    for key, ws in lines.items():
        ws.sort(key=lambda t: t[0])
        avg_y = sum(w[1] for w in ws) / len(ws)
        line_items.append((avg_y, key, ws))
    line_items.sort(key=lambda t: t[0])
    print(f"=== {path} page {pageno} ({page.rect.width:.1f} x {page.rect.height:.1f}) ===")
    for avg_y, key, ws in line_items:
        raw = " ".join(w[4] for w in ws)
        compact = raw.replace(" ", "")
        xs = ",".join(f"{w[0]:.0f}" for w in ws)
        print(f"y={avg_y:7.1f} block/line={key} x=[{xs}]")
        print(f"    raw : {raw}")
        print(f"    cmp : {compact}")

if __name__ == "__main__":
    path = sys.argv[1]
    pageno = int(sys.argv[2])
    dump_page(path, pageno)
