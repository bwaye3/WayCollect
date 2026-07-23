# CLAUDE.md

Context for Claude Code working in this repo. This project moved here from a
claude.ai conversation — this file is the memory that actually carries over.

## What this is

A local-first, air-gapped register for a physical watch collection. Built for
one person's personal use, licensed PolyForm Noncommercial 1.0.0, repo is public but **no personal
data lives in it** — see "Never do this" below.

## Architecture — read this before changing structure

- `src/index.html` is the **entire frontend**. One file. HTML + CSS + JS
  inline, zero build step, zero npm frontend dependencies. This is
  deliberate, not unfinished — do not introduce a bundler, framework, or
  build step for the frontend without discussing it first. `tauri.conf.json`
  → `frontendDist` points straight at the `src/` folder; there is nothing
  for a bundler to do.
- `src-tauri/` is a thin Rust shell (`lib.rs`/`main.rs` are near-default
  Tauri boilerplate). **v1 does no custom Rust work** — no filesystem
  commands, no vault logic in Rust. The app still uses the same
  browser-standard WebCrypto (AES-256-GCM, envelope encryption) and
  IndexedDB it used as a plain browser file. Native filesystem control
  (real wipe-on-exit, no-download-dialog vault read/write) is the
  documented next increment, not yet built.
- `package.json` exists **only** to let `npx tauri` run (the CLI ships as a
  precompiled npm binary — no Rust needed to use it for icon-gen, `info`,
  etc.). There is no frontend build script because there's nothing to build.

## CSP — inline styles do not work in the packaged app

Tauri injects a nonce into `style-src` when it bundles the frontend. Per the
CSP spec, a nonce in a directive makes `'unsafe-inline'` **inert** — so every
inline `style=""` attribute is parsed, kept in the DOM, and then applied to
nothing. `<style>` blocks are fine (Tauri nonces them). JS `el.style.x = ...`
is CSSOM, not an attribute, and is unaffected.

This never reproduces in a browser, because nothing injects a nonce there.
Symptoms are unsized `<img>` blowing table rows to full height and
`display:none` elements rendering visibly, while the DOM stays functional
(clicks still work) — which misleads toward layout theories. Put anything that
must actually apply in the stylesheet. Utility classes live at the end of the
`<style>` block so they win the ties inline styles used to win.

## Never do this

- **Never commit anything that looks like real collection data** — a
  `.vault.json`, a plain JSON export, anything with real serials/values/PII.
  `.gitignore` already blocks the common patterns and was tested with
  `git check-ignore` against realistic filenames — extend it, don't bypass
  it. This repo is public; anything committed is visible forever, even
  after deletion.
- **Never add `beforeBuildCommand`/`beforeDevCommand`** to `tauri.conf.json`
  unless the zero-build-step design is being deliberately abandoned — ask
  first.
- **Never weaken the CSP** in `tauri.conf.json` → `app.security.csp`.
  `connect-src 'none'` is intentional: the whole point of the app is that it
  never makes a network request. If a feature seems to need `connect-src`
  opened up, that's a sign the feature doesn't belong in this app.

## Build & release — GitHub Actions only, by design

Builds happen on GitHub's hosted runners, never locally. This is a
deliberate constraint (avoiding a Rust toolchain on a monitored work
laptop), not a limitation to "fix" by adding local build docs.

**Bump the version in THREE files before tagging** — `src-tauri/tauri.conf.json`,
`src-tauri/Cargo.toml`, `package.json`. The git tag does not set the app
version. This was missed for v0.1.0 through v0.1.3, so every one of those
builds produced an identically-named `Watch Register_0.1.0_*.dmg` with no way
to tell them apart — which made "is the fix actually in the build I'm testing?"
unanswerable and cost two ambiguous debugging rounds.

```bash
# 1. bump the three manifests to X.Y.Z first
git commit -am "…"
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

pushes a tag → `.github/workflows/build.yml` builds macOS (aarch64 +
x86_64) and Windows → draft GitHub Release with installers attached.
`workflow_dispatch` also works for a test build without tagging, but the
resulting release will be labeled `untagged-<sha>` instead of a clean
version — expected, harmless, just delete it if it's confusing.

**macOS signing:** `tauri.conf.json` → `bundle.macOS.signingIdentity: "-"`
is already set (ad-hoc signing). Without it, Apple Silicon downloads from
GitHub Releases fail with a misleading "is damaged, move to Trash" dialog —
this is a documented Tauri gotcha for exactly this CI-build scenario, not
Gatekeeper's normal "unidentified developer" warning, and right-click→Open
does **not** fix it. If it ever recurs, `xattr -cr path/to/App.app` is the
client-side workaround; the real fix is keeping `signingIdentity` set.

**No local Rust in this sandbox history:** the project was originally
validated without ever running a full `cargo build` locally — Rust
available in that environment was too old for Tauri v2's dependency tree,
and there was no path to a newer one. Config files were verified via
`tauri info` (parses `Cargo.toml`/`tauri.conf.json` without compiling) and
JSON/TOML/YAML syntax checks instead. The first real compile happened on
GitHub Actions and succeeded on the second attempt (first attempt was
unsigned, hence the signing fix above).

## Editing tauri.conf.json specifically

If editing this file via a pasted block ever produces `nothing to commit,
working tree clean` after a supposed edit — the paste didn't land (this
happened once; a terminal editor/clipboard issue). Verify with `grep` for
the specific key you added before committing. Prefer writing the file via
`cat > file << 'EOF' ... EOF` (quoted heredoc) over paste-into-editor for
this specific file — the `$schema` key at the top will get silently
mangled by bash if the heredoc delimiter isn't quoted.

## Product naming

App name (`productName`, window title) is **"Watch Register."** The GitHub
repo is named **WayCollect**. These are intentionally different — not a
bug, not inconsistent branding to fix. Don't rename one to match the other
without being asked.

## Roadmap (not yet built, in rough priority order)

1. Native Rust filesystem commands (real vault read/write/wipe, replacing
   the browser download-dialog flow).
2. Shamir's Secret Sharing for the vault's master key (K-of-N shares) —
   the envelope-encryption design (`seal()`/`unseal()` in `src/index.html`)
   was specifically built so this drops in without re-encrypting existing
   vaults.
3. Sync the blank template used for the public repo/build with whatever
   schema changes land — they can drift if fields are added to a personal
   copy and not mirrored back here.