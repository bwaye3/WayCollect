# Watch Register

A local-first, air-gapped register for a physical collection — built for
tracking watches, but the schema works for any high-value objects with
provenance, service history, and insurance needs.

No servers. No accounts. No telemetry. No network calls of any kind, at runtime
or at rest — `connect-src` is `'none'` in the CSP, so the app *cannot* make a
request even if something tried to.

Everything the app stores on your machine is encrypted with AES-256-GCM. There
is no readable copy of your collection on disk. The app opens locked; your
passphrase decrypts the register into memory for the session, and locking it —
manually, on launch, or via the idle timer — discards the key.

Full detail on the security model is in the app itself: **How it works** and
**Succession & recovery** in the footer.

## Security model

**Encrypted at rest.** The register is a single sealed blob. Not a database
file, not a cache — there is nothing on disk to read without your passphrase.

**One master key, wrapped twice.** A random master key encrypts your data. Your
passphrase never encrypts the data directly; it *wraps* that master key
(PBKDF2-SHA256, 250,000 rounds). A printable recovery key, shown once during
setup, wraps the same master key independently. Either opens the register;
neither can be derived from the other. Changing your passphrase re-wraps the
key in milliseconds — none of your data is re-encrypted, and the recovery key
keeps working.

**Locking is not a screen over readable data.** Locking drops the master key.
A locked app has nothing to read until a valid secret is supplied.

**There is no reset.** No backdoor, no email recovery, no support channel that
can let you back in. Lose the passphrase *and* the recovery key and the
collection is unrecoverable by anyone, permanently. Store the recovery key on
paper, offline, where your estate documents live.

**What it doesn't protect against.** Malware running as you while the register
is unlocked, and a passphrase written on a sticky note. Encryption at rest is
not encryption against everything.

**Vault files.** Alongside the encrypted local store you can export a portable
`.vault.json` — the same envelope encryption in a file you control — for
offsite backup, moving between machines, or handing to an executor.
**Vault-only mode** writes nothing to the machine at all: memory only, you open
and save vault files by hand. That's the borrowed-computer mode.

**Shard-ready by design.** Because a passphrase wraps a master key rather than
encrypting data directly, that key can carry more wraps. The recovery key is
the first. Shamir's Secret Sharing (any K of N shares) can be added later
without re-encrypting anything.

## How building works here

**Builds happen on GitHub's servers, not your computer.** Push a version tag,
GitHub Actions compiles the macOS and Windows binaries, and a draft release
appears with the installers attached. Nothing gets compiled locally — no Rust
toolchain to install, no compiler running on your machine.

```bash
git tag v1.2.0
git push origin v1.2.0
```

Then watch the **Actions** tab. In a few minutes a **draft release** appears
under **Releases** with the `.dmg` (macOS) and `.msi`/`.exe` (Windows)
attached. Drafts are private to you until you publish them.

> **Bump the version in three places before tagging** — `src-tauri/tauri.conf.json`,
> `src-tauri/Cargo.toml` and `package.json`. The tag does *not* set the version.
> If you skip this, every release produces identically-named installers and you
> cannot tell which build you're running.

You can also trigger a build without tagging — **Actions → Build desktop app →
Run workflow**. The resulting release is labelled `untagged-<sha>`.

### First launch — read this before you're confused by a warning

These builds are **ad-hoc signed** (no Apple Developer or Windows
code-signing certificate is configured). Signing costs ~$99/yr (Apple) and
~$100–300/yr (Windows), and only matters when distributing to people who'd
otherwise see a warning.

- **macOS:** Right-click (or Control-click) the app → **Open** → **Open** again
  in the dialog. Once per machine.
- **Windows:** SmartScreen shows "Windows protected your PC." Click
  **More info** → **Run anyway**.

See Tauri's [macOS](https://v2.tauri.app/distribute/sign/macos/) and
[Windows](https://v2.tauri.app/distribute/sign/windows/) signing guides to
remove this friction.

## What's actually in this repo

```
├── src/index.html          the app itself — single-file, zero build step
├── src-tauri/               Rust shell that turns it into a native app
│   ├── tauri.conf.json      window config, strict CSP (connect-src: 'none')
│   ├── capabilities/         permissions — no filesystem/shell/network granted
│   └── icons/                pre-generated, all platforms
└── .github/workflows/       the GitHub Actions build pipeline
```

`src/index.html` is the entire frontend — one HTML file, no CSS/JS
dependencies, no build tooling. `frontendDist` in `tauri.conf.json` points
straight at it; there's nothing for a bundler to do.

> **A packaging gotcha worth knowing.** Inline `style=""` attributes do **not**
> work in the packaged app. Tauri injects a nonce into `style-src`, and per the
> CSP spec a nonce makes `'unsafe-inline'` inert — so style attributes are
> parsed, kept in the DOM, and then ignored. Anything that must actually apply
> belongs in the stylesheet. JS `el.style.x = …` is CSSOM and is unaffected.
> This never reproduces in a browser, where no nonce is injected.

**Current scope, honestly stated:** the register is encrypted at rest and
locked behind a passphrase, using browser-standard WebCrypto and IndexedDB
inside the native shell. Rust-side filesystem commands — native vault
read/write, wipe-on-exit, hardware key support — are the documented next step,
not yet built.

## Local development (optional, and not on a work machine)

You don't need this for normal use — the GitHub Actions build is the whole
point. To iterate with live reload:

```bash
npm install
npx tauri dev
```

This **does** require a local Rust toolchain (via [rustup](https://rustup.rs)).
Only do this on a machine you're fine installing a compiler on.

## Your data never goes in this repo

Check `.gitignore` — it excludes anything named like a vault export or plain
JSON export. The repo holds the *app*; your *collection* lives on your own
machine and in vault files you keep separately. Never commit a `.vault.json`
or a plain export here, even to a private repo.

## Contact

Built by **Bradley Waye**.

- **Bugs, questions, suggestions** — [open an issue](https://github.com/bwaye3/WayCollect/issues).
  Answers there are visible to the next person with the same question.
- **Commercial licensing, partnership, or acquisition** —
  <bradwaye@gmail.com>. See the licence below for what needs one.

## License

[PolyForm Noncommercial License 1.0.0](./LICENSE) — free for personal and other
noncommercial use, including hobby, research, educational, and charitable use.

**Commercial use requires a separate licence.** That includes using it inside a
dealership, auction house or other business, bundling it with a product or
service, or licensing the source. Email the address above and say what you have
in mind.

The source is deliberately readable: a security tool whose claims can't be
audited isn't worth trusting. Source-available is not the same as open source,
and this is the former.
