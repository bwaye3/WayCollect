#!/usr/bin/env python3
"""
Fast checks over the single-file frontend and the manifests.

    python3 tools/check-frontend.py

Catches the specific classes of bug this project has actually shipped, all of
which pass a normal build and fail silently in the packaged app:

  1. Inline style="" attributes      -- Tauri injects a nonce into style-src,
                                        which makes 'unsafe-inline' inert, so
                                        these are parsed and then ignored.
  2. Inline on*="" handlers          -- dead for the same reason.
  3. Version drift across the three  -- a tag does not set the app version, so
     manifests                          forgetting one produces installers that
                                        cannot be told apart.
  4. FAQ panel out of sync with      -- the panel is generated from the draft;
     FAQ-draft.txt                      hand-editing it lets them diverge.
  5. Broken JS or JSON               -- a syntax error still packages fine.

Exit code is non-zero if anything fails, so CI can gate on it.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "src" / "index.html"

failures = []
notes = []


def strip_comments(src):
    """Blank out HTML and CSS/JS block comments, preserving newlines so reported
    line numbers stay accurate. Without this the guards below match the comments
    that document the very problem they check for."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    src = re.sub(r"<!--.*?-->", blank, src, flags=re.S)
    src = re.sub(r"/\*.*?\*/", blank, src, flags=re.S)
    return src


def fail(msg):
    failures.append(msg)


def check_inline_styles(src):
    hits = []
    for m in re.finditer(r'\sstyle\s*=\s*"', src):
        line = src[: m.start()].count("\n") + 1
        hits.append(line)
    if hits:
        fail(f"inline style=\"\" attributes on line(s) {hits} — these are silently "
             f"ignored in the packaged app (CSP nonce makes 'unsafe-inline' inert). "
             f"Move the declaration into the <style> block as a class.")


def check_inline_handlers(src):
    hits = []
    for m in re.finditer(r'\son(click|change|input|submit|load|error)\s*=\s*"', src):
        line = src[: m.start()].count("\n") + 1
        hits.append((m.group(0).strip(), line))
    if hits:
        fail(f"inline event handlers {hits} — dead in the packaged app for the same "
             f"reason as inline styles. Use addEventListener or a delegated "
             f"[data-act] handler.")


def check_versions():
    tauri = json.loads((ROOT / "src-tauri" / "tauri.conf.json").read_text())["version"]
    pkg = json.loads((ROOT / "package.json").read_text())["version"]
    cargo = re.search(r'^version\s*=\s*"([^"]+)"',
                      (ROOT / "src-tauri" / "Cargo.toml").read_text(), re.M).group(1)
    # Cargo.lock pins this crate's own version too, so --locked fails the
    # build if a bump misses it. Four files, not three.
    lock_path = ROOT / "src-tauri" / "Cargo.lock"
    lock = None
    if lock_path.exists():
        m = re.search(r'name = "watch-register"\nversion = "([^"]+)"', lock_path.read_text())
        lock = m.group(1) if m else None

    versions = {"tauri.conf.json": tauri, "package.json": pkg, "Cargo.toml": cargo}
    if lock is not None:
        versions["Cargo.lock"] = lock

    if len(set(versions.values())) != 1:
        pairs = "  ".join(f"{k}={v}" for k, v in versions.items())
        fail(f"version mismatch: {pairs} — all must agree. Cargo.lock pins this "
             f"crate's own version, so a bump that misses it fails cargo check "
             f"--locked; the others produce identically-named installers.")
    else:
        notes.append(f"version {tauri} consistent across {len(versions)} manifests")


def check_csp():
    cfg = json.loads((ROOT / "src-tauri" / "tauri.conf.json").read_text())
    csp = cfg.get("app", {}).get("security", {}).get("csp", "")
    if "connect-src 'none'" not in csp:
        fail("connect-src 'none' is missing from the CSP — the app's core claim is "
             "that it cannot make a network request.")
    else:
        notes.append("CSP still pins connect-src 'none'")


def check_js_syntax(src):
    i = src.find("<script")
    j = src.rfind("</script>")
    if i < 0 or j < 0:
        fail("could not locate the inline <script> block")
        return
    body = src[src.index(">", i) + 1: j]
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(body)
        tmp = f.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    Path(tmp).unlink(missing_ok=True)
    if r.returncode != 0:
        fail(f"inline JavaScript does not parse:\n{r.stderr.strip()}")
    else:
        notes.append("inline JavaScript parses")


def check_faq_in_sync():
    draft = ROOT / "FAQ-draft.txt"
    builder = ROOT / "tools" / "build-faq.py"
    if not draft.exists() or not builder.exists():
        return
    before = INDEX.read_text(encoding="utf-8")
    r = subprocess.run([sys.executable, str(builder)], capture_output=True, text=True, cwd=ROOT)
    after = INDEX.read_text(encoding="utf-8")
    if r.returncode != 0:
        INDEX.write_text(before, encoding="utf-8")
        fail(f"tools/build-faq.py failed:\n{r.stdout}{r.stderr}")
        return
    if before != after:
        INDEX.write_text(before, encoding="utf-8")
        fail("the in-app FAQ does not match FAQ-draft.txt — run "
             "`python3 tools/build-faq.py` and commit the result.")
    else:
        notes.append("in-app FAQ matches FAQ-draft.txt")


def check_wire_targets():
    """Every $("#id") that wire() attaches to at init must exist in the static
    HTML. wire() runs before any dynamic markup is built, so a reference to an
    element created later in openForm() returns null and throws -- which aborts
    init() entirely: no data load, no terms gate, a blank app. Shipped once in
    v1.23.0 (the svcAddBtn move) and invisible to a normal build."""
    raw = INDEX.read_text(encoding="utf-8")
    m = re.search(r"function wire\(\)\{", raw)
    if not m:
        return
    i = m.end(); depth = 1; j = i
    while j < len(raw) and depth:
        if raw[j] == "{": depth += 1
        elif raw[j] == "}": depth -= 1
        j += 1
    wire = raw[i:j]
    static = raw[: raw.index("<script")]
    ids = set(re.findall(r'\$\("#([\w-]+)"\)', wire))
    missing = sorted(i for i in ids if f'id="{i}"' not in static)
    if missing:
        fail(f"wire() references {missing}, which do not exist in the static HTML "
             f"-- these throw at boot and abort init() (blank app, no data). "
             f"Attach them where they are built, or delegate from document.")
    else:
        notes.append(f"all {len(ids)} wire() targets exist in static HTML")


def check_terms_in_sync():
    """The text a user legally accepts must be the text in the repo."""
    src = ROOT / "TERMS-draft.md"
    builder = ROOT / "tools" / "build-terms.py"
    if not src.exists() or not builder.exists():
        return
    before = INDEX.read_text(encoding="utf-8")
    r = subprocess.run([sys.executable, str(builder)], capture_output=True, text=True, cwd=ROOT)
    after = INDEX.read_text(encoding="utf-8")
    if r.returncode != 0:
        INDEX.write_text(before, encoding="utf-8")
        fail(f"tools/build-terms.py failed:\n{r.stdout}{r.stderr}")
        return
    if before != after:
        INDEX.write_text(before, encoding="utf-8")
        fail("the in-app Terms do not match TERMS-draft.md — run "
             "`python3 tools/build-terms.py` and commit the result.")
    else:
        notes.append("in-app Terms match TERMS-draft.md")


def main():
    raw = INDEX.read_text(encoding="utf-8")
    src = strip_comments(raw)
    check_inline_styles(src)
    check_inline_handlers(src)
    check_js_syntax(raw)
    check_versions()
    check_csp()
    check_faq_in_sync()
    check_wire_targets()
    check_terms_in_sync()

    for n in notes:
        print(f"  ok    {n}")
    for f in failures:
        print(f"  FAIL  {f}")
    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print(f"\nall {len(notes)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
