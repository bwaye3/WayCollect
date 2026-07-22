# Watch Register

A local-first, air-gapped register for a physical collection — built for tracking
watches, but the schema works for any high-value objects with provenance,
service history, and insurance needs.

No servers. No accounts. No telemetry. No network calls of any kind, at
runtime or at rest. Your data lives in an AES-256-GCM encrypted vault file you
own, or in this browser's local storage if you choose convenience over
portability. Full detail on the security model is in the app itself — click
**How it works** and **Succession & recovery** in the footer.

This repo wraps that app in [Tauri](https://tauri.app) to produce a real,
installable desktop app instead of a browser tab.

## How building works here

**Builds happen on GitHub's servers, not your computer.** Push a version tag,
GitHub Actions compiles the macOS and Windows binaries, and a draft release
appears with the installers attached. Nothing gets compiled locally — no Rust
toolchain to install, no compiler running on your machine.

```bash
git tag v0.1.0
git push origin v0.1.0
```

Then watch the **Actions** tab. In a few minutes, a **draft release** appears
under **Releases** with the `.dmg` (macOS) and `.msi`/`.exe` (Windows)
attached. Drafts are private to you until you publish them.

You can also trigger a build without tagging — go to **Actions → Build desktop
app → Run workflow**. Useful for testing changes before committing to a
version number.

### First launch — read this before you're confused by a warning

These builds are **unsigned** (no Apple Developer or Windows code-signing
certificate is configured). That's a cost/bureaucracy tradeoff, not a bug —
signing costs ~$99/yr (Apple) and ~$100–300/yr (Windows) and only matters if
you're distributing to people who'd otherwise see a scary warning.

- **macOS:** Gatekeeper will refuse to open it the normal way. Right-click
  (or Control-click) the app → **Open** → **Open** again in the dialog. You
  only need to do this once per machine.
- **Windows:** SmartScreen will show "Windows protected your PC." Click
  **More info** → **Run anyway**.

If you ever want to distribute this to people who shouldn't have to click
through a warning, see Tauri's [macOS](https://v2.tauri.app/distribute/sign/macos/)
and [Windows](https://v2.tauri.app/distribute/sign/windows/) signing guides.

## What's actually in this repo

```
├── src/index.html          the app itself — single-file, zero build step
├── src-tauri/               Rust shell that turns it into a native app
│   ├── tauri.conf.json      window config, strict CSP (connect-src: 'none')
│   ├── capabilities/         permissions — no filesystem/shell/network granted
│   └── icons/                pre-generated, all platforms
└── .github/workflows/       the GitHub Actions build pipeline
```

`src/index.html` is the same self-contained app whether you run it as a plain
browser file or through this Tauri wrapper — one HTML file, no CSS/JS
dependencies, no build tooling. `frontendDist` in `tauri.conf.json` points
straight at it; there's nothing for a bundler to do.

**v1 scope, honestly stated:** this wraps the existing app in a native window.
It does not yet add Rust-side filesystem commands (native vault read/write,
wipe-on-exit, hardware key support). The app still uses the same
browser-standard WebCrypto and IndexedDB it always did — you get a real
installed app with an icon and no browser chrome, not yet deeper OS-level
guarantees. That's a deliberate, documented next step, not an oversight.

## Local development (optional, and not on a work machine)

You don't need this for normal use — the GitHub Actions build is the whole
point. If you ever want to iterate with live reload:

```bash
npm install
npx tauri dev
```

This **does** require a local Rust toolchain (via [rustup](https://rustup.rs)).
Only do this on a machine you're fine installing a compiler on.

## Your data never goes in this repo

Check `.gitignore` — it excludes anything named like a vault export or plain
JSON export. The repo holds the *app*; your *collection* lives in a vault file
you keep separately (USB stick, personal cloud drive, wherever you'd keep the
physical equivalent of a safe-deposit box key). Never commit a `.vault.json`
file here, even to a private repo.

## License

MIT — see [LICENSE](./LICENSE). Take it, use it, change it, pass it on.
