#!/usr/bin/env python3
"""
Regenerate the in-app FAQ panel from FAQ-draft.txt.

    python3 tools/build-faq.py

FAQ-draft.txt is the source of truth: it is the version a human reviews and
edits. This script converts it to the <details> accordions inside
src/index.html, replacing whatever is there. Editing the HTML by hand is what
lets the reviewable text and the shipped panel drift apart, which is the whole
thing this avoids.

This is NOT a frontend build step -- src/index.html remains a complete,
standalone file that Tauri ships as-is. Run this by hand when the FAQ text
changes, then commit the result.

Draft format:

    ================================================================
    SECTION 1 - TITLE            (an em dash, not a hyphen)
    ================================================================

    Q1. The question?

    A1. The answer. Continuation lines are indented to line up under the
        text, not under the "A1.".

        Blank line starts a new paragraph.

        - bullet, which may
          wrap across lines
        - another bullet

        1. numbered step
        2. another step

        LABEL - description        (all-caps label + em dash = definition row)

Answers may not contain "See Q5"-style cross references: the panel has no
visible numbers, so refer to questions by name instead.
"""

import html as H
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "FAQ-draft.txt"
TARGET = ROOT / "src" / "index.html"

SECTION_TITLES = {
    "SECURITY": "Security",
    "WHAT THIS APP IS FOR": "What this app is for",
    "GETTING STARTED": "Getting started",
    "RECORDING YOUR WATCHES": "Recording your watches",
    "THE MONEY": "The money",
    "PHOTOS AND DOCUMENTS": "Photos and documents",
    "WHAT THIS APP DELIBERATELY DOES NOT DO": "What it deliberately does not do",
    "WHEN SOMETHING LOOKS WRONG": "When something looks wrong",
    "ABOUT AND CONTACT": "About and contact",
}

DEF_ROW = re.compile(r"^[A-Z][A-Z0-9 ()\-]{2,}\s+—\s")
LEAD_LABEL = re.compile(r"^([A-Z][A-Z0-9 ()\-]{2,})(\s+—\s+)(.*)$", re.S)
LEAD_CAPS = re.compile(r"^([A-Z]{4,})\b(.*)$", re.S)
BULLET = lambda s: s.lstrip().startswith("- ")
NUMBERED = lambda s: bool(re.match(r"^\d+\.\s", s.lstrip()))


def parse(text):
    """-> [(section_title, [(question, [answer_line, ...])])]"""
    sections, cur, mode, qbuf, abuf, qtext, indent = [], None, None, [], [], None, 4

    def flush():
        nonlocal qtext, abuf
        if qtext is not None and cur is not None:
            cur[1].append((qtext, list(abuf)))
        qtext, abuf = None, []

    for line in text.split("\n"):
        if line.startswith("SECTION "):
            flush()
            cur = (line.split("—", 1)[1].strip(), [])
            sections.append(cur)
            mode, qbuf = None, []
            continue
        if re.match(r"^Q\d+\.", line):
            flush()
            mode, qbuf = "q", [re.sub(r"^Q\d+\.\s*", "", line)]
            continue
        m = re.match(r"^(A\d+\.\s+)(.*)$", line)
        if m:
            qtext = " ".join(" ".join(qbuf).split())
            mode, abuf, indent = "a", [m.group(2)], len(m.group(1))
            continue
        if mode == "q":
            if line.strip():
                qbuf.append(line.strip())
        elif mode == "a":
            if line.startswith("="):
                flush()
                mode = None
            else:
                keep = len(line) > indent and line[:indent].isspace()
                abuf.append(line[indent:] if keep else line.strip())
    flush()
    return sections


def blocks(answer_lines):
    """Split an answer into paragraph blocks, splitting a block at its first
    list item so an intro line followed immediately by bullets still works."""
    out, buf = [], []
    for line in answer_lines:
        if not line.strip():
            if buf:
                out.append(buf)
                buf = []
        else:
            buf.append(line.rstrip())
    if buf:
        out.append(buf)

    split = []
    for b in out:
        idx = next((i for i, l in enumerate(b) if (BULLET(l) or NUMBERED(l)) and i > 0), None)
        if idx and not (BULLET(b[0]) or NUMBERED(b[0])):
            split.append(b[:idx])
            split.append(b[idx:])
        else:
            split.append(b)
    return split


def merge_items(block, is_start):
    """Fold wrapped continuation lines into the list item they belong to."""
    items = []
    for line in block:
        if is_start(line) and (len(line) - len(line.lstrip())) <= 1:
            items.append([line.strip()])
        elif items:
            items[-1].append(line.strip())
        else:
            items.append([line.strip()])
    return [" ".join(" ".join(i).split()) for i in items]


def block_html(b):
    if BULLET(b[0]):
        items = merge_items(b, BULLET)
        return '<ul class="faq-ul">' + "".join(f"<li>{H.escape(i[2:])}</li>" for i in items) + "</ul>"
    if NUMBERED(b[0]):
        items = merge_items(b, NUMBERED)
        return '<ol class="faq-ul">' + "".join(
            f'<li>{H.escape(re.sub(r"^\d+\.\s*", "", i))}</li>' for i in items) + "</ol>"
    if len(b) > 1 and all(DEF_ROW.match(x.strip()) for x in b):
        rows = ""
        for x in b:
            m = LEAD_LABEL.match(" ".join(x.split()))
            rows += f"<div><b>{H.escape(m.group(1))}</b> — {H.escape(m.group(3))}</div>"
        return f'<div class="faq-defs">{rows}</div>'
    text = " ".join(" ".join(b).split())
    m = LEAD_LABEL.match(text)
    if m:
        return f"<p><b>{H.escape(m.group(1))}</b> — {H.escape(m.group(3))}</p>"
    m = LEAD_CAPS.match(text)
    if m:
        return f"<p><b>{H.escape(m.group(1))}</b>{H.escape(m.group(2))}</p>"
    return f"<p>{H.escape(text)}</p>"


def main():
    draft = DRAFT.read_text(encoding="utf-8")

    stale = re.findall(r"[Ss]ee Q\d+", draft)
    if stale:
        sys.exit(f"error: draft uses numbered cross references {stale} — the panel "
                 "has no visible numbers. Refer to questions by name instead.")

    sections = parse(draft)
    total = sum(len(qs) for _, qs in sections)
    if not total:
        sys.exit("error: parsed no questions — check the draft format")

    parts = []
    for name, qs in sections:
        title = SECTION_TITLES.get(name, name.capitalize())
        parts.append(f'<div class="faq-sec">{H.escape(title)}</div>')
        for q, a in qs:
            inner = "".join(block_html(b) for b in blocks(a))
            parts.append(f'<details class="faq"><summary>{H.escape(q)}</summary>{inner}</details>')
    panel = "\n    ".join(parts)

    src = TARGET.read_text(encoding="utf-8")
    start = '<div class="modal-body dialog-text u-lh17">\n    <div class="faq-sec">'
    i = src.find(start)
    if i < 0:
        sys.exit("error: could not find the FAQ panel in src/index.html")
    j = src.find("\n  </div>", i)
    head = '<div class="modal-body dialog-text u-lh17">\n    '
    src = src[:i] + head + panel + src[j:]
    TARGET.write_text(src, encoding="utf-8")

    unknown = [n for n, _ in sections if n not in SECTION_TITLES]
    if unknown:
        print(f"note: unmapped section titles {unknown} — add them to SECTION_TITLES")
    print(f"wrote {total} questions across {len(sections)} sections into {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
