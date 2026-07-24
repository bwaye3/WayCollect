#!/usr/bin/env python3
"""Regenerate the in-app Terms panel from TERMS-draft.md.

    python3 tools/build-terms.py

TERMS-draft.md is the source of truth — the version a human edits and a lawyer
reviews. This converts it into the markup inside src/index.html so the text a
user accepts is provably the text in the repo. Editing the HTML by hand is what
lets them drift apart, which for a legal document is worse than for a feature.
Run by hand after editing the terms, then commit both.
"""
import html as H, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "TERMS-draft.md"
TARGET = ROOT / "src" / "index.html"
START, END = "<!--TERMS:START-->", "<!--TERMS:END-->"

def inline(t):
    t = H.escape(t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)          # links go flat: no navigation from here
    t = re.sub(r"`([^`]+)`", r'<code>\1</code>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t

def build():
    md = SRC.read_text(encoding="utf-8")
    out, para = [], []
    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
    for raw in md.split("\n"):
        line = raw.rstrip()
        if line.startswith("# "):
            flush(); continue                                # title is the panel heading
        if line.startswith("## "):
            flush(); out.append(f'<div class="tos-h">{inline(line[3:])}</div>'); continue
        if line.strip() in ("---", ""):
            flush(); continue
        if line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            flush(); out.append(f'<p class="tos-foot">{inline(line.strip("*").strip())}</p>'); continue
        para.append(line.strip())
    flush()
    body = "\n      ".join(out)

    s = TARGET.read_text(encoding="utf-8")
    i, j = s.find(START), s.find(END)
    if i < 0 or j < 0:
        sys.exit("error: TERMS:START/END markers not found in src/index.html")
    s = s[:i + len(START)] + "\n      " + body + "\n      " + s[j:]
    TARGET.write_text(s, encoding="utf-8")
    print(f"wrote {len(out)} blocks into {TARGET.relative_to(ROOT)}")

if __name__ == "__main__":
    build()
