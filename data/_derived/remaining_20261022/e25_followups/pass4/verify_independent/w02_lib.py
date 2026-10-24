# -*- coding: utf-8 -*-
"""Own reader (HTMLParser based, no regex table split, no repo imports)."""
import glob, os, re
from html.parser import HTMLParser
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
def raw_path(fq, code):
    fy, q = fq.split("_Q")
    c = [p for p in glob.glob(R + "data/dart/%s/raw/%s_*/**/*.xml" % (fq, code), recursive=True) if "document.zip" not in p]
    return max(c, key=os.path.getsize)
def to_num(s):
    s = s.strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "\u2013"): return None
    neg = False
    if s.startswith("(") and s.endswith(")"): neg, s = True, s[1:-1]
    if s.startswith("\u25b3"): neg, s = True, s[1:]
    try: v = float(s)
    except ValueError: return None
    return -v if neg else v
class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []; self.stack = []; self.cell = None; self.row = None
    def handle_starttag(self, tag, attrs):
        t = tag.upper()
        if t == "TABLE":
            self.stack.append({"line": self.getpos()[0], "rows": []})
        elif t == "TR" and self.stack:
            self.row = {"line": self.getpos()[0], "cells": []}
        elif t in ("TD", "TH", "TE", "TU") and self.stack:
            span = 1
            for k, v in attrs:
                if k.lower() == "colspan":
                    try: span = int(v)
                    except Exception: pass
            self.cell = {"txt": [], "span": span}
    def handle_endtag(self, tag):
        t = tag.upper()
        if t in ("TD", "TH", "TE", "TU") and self.cell is not None and self.row is not None:
            self.row["cells"].append(re.sub(r"\s+", " ", "".join(self.cell["txt"]).replace("\xa0", " ")).strip())
            self.row["cells"] += [""] * (self.cell["span"] - 1)
            self.cell = None
        elif t == "TR" and self.row is not None and self.stack:
            self.stack[-1]["rows"].append(self.row); self.row = None
        elif t == "TABLE" and self.stack:
            self.tables.append(self.stack.pop())
    def handle_data(self, d):
        if self.cell is not None: self.cell["txt"].append(d)
def read_tables(path):
    p = P()
    with open(path, encoding="utf-8", errors="replace") as f: p.feed(f.read())
    return p.tables
