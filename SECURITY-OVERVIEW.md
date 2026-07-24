# Watch Register — Security Architecture

Written for external review. Every claim below is checkable against
`src/index.html`, `src-tauri/`, and `.github/workflows/` in this repository —
line references included where useful. **Reviewers: please attack the
"Known limitations" section first; it is where the real weaknesses are.**

Version described: **v1.15.0**. macOS and Windows desktop application built
with Tauri v2 (Rust shell + system WebView).

---

## 1. Threat model

**Protects against**

| Threat | Mechanism |
|---|---|
| Stolen or lost laptop | Data is AES-256-GCM ciphertext at rest; no plaintext copy on disk |
| Someone using an unlocked machine | App locks on launch and on an idle timer; locking discards the key |
| Drive imaging, backup extraction, cloud sync of the app folder | Same — the artifact is ciphertext without the passphrase |
| Data exfiltration by the application itself | The app has no network capability at all (§2) |
| Vendor/server compromise | There is no server, no account, and no vendor-held copy |
| Supply-chain drift | 419 crates pinned in `Cargo.lock`, enforced by `cargo check --locked` |

**Explicitly does not protect against**

- Malware with code execution on the machine **while the register is unlocked**
- Keyloggers or shoulder-surfing of the passphrase
- Physical coercion
- A passphrase or recovery key stored insecurely by the user
- Anything after the user exports plaintext themselves (an explicit,
  labelled action)

---

## 2. Air-gap: the network claim

The claim is not "we choose not to transmit." It is that **the application
cannot make a network request**, enforced at three independent layers.

**Layer 1 — Content Security Policy** (`src-tauri/tauri.conf.json`)

```
default-src 'self'; script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline'; img-src 'self' data:;
connect-src 'none'
```

`connect-src 'none'` blocks `fetch`, `XMLHttpRequest`, `WebSocket`,
`EventSource` and `navigator.sendBeacon` at the engine level. `default-src
'self'` with no external origins means no CDN, font, analytics or pixel loads
are possible. `img-src` permits only `self` and `data:` URIs — user photographs
are embedded as `data:` and never fetched.

**Layer 2 — No network code exists.** Grepping the entire 1.5 MB frontend:

```
fetch(                 0   (1 match, in a comment stating there are none)
XMLHttpRequest         0
WebSocket              0
EventSource            0
navigator.sendBeacon   0
importScripts          0
src="http              0
href="http             0
```

There are no `<script src>`, `<link href>`, webfont, or remote-image
references. The frontend is a single self-contained HTML file with zero
runtime dependencies.

**Layer 3 — No capability granted.** Tauri v2 gates all native access through
explicit capability grants. The complete grant is:

```json
{ "permissions": ["core:default"] }
```

No HTTP plugin, no shell, no arbitrary filesystem access. The Rust
dependency tree is three direct crates: `tauri`, `serde`, `serde_json`. There
is no HTTP client anywhere in the tree.

**Consequences accepted for this design:** no sync, no cloud backup, no
automatic market-price feeds, no crash reporting, no analytics, no update
check. All are deliberate; the absence of a network path is the product.

---

## 3. Cryptography

Standard primitives via WebCrypto (`crypto.subtle`). No third-party crypto
library, no hand-rolled algorithms.

**Envelope design.** A random 256-bit master key (MK) encrypts the register.
The passphrase never encrypts data directly — it derives a KEK that *wraps*
the MK.

```
MK          = generateKey(AES-GCM, 256)
KEK         = PBKDF2-SHA256(passphrase, salt=16B random, 250,000 iterations)
wrapped_MK  = AES-GCM-wrap(MK, KEK, iv=12B random)
ciphertext  = AES-GCM(register_json, MK, iv=12B random)
```

**Two independent wraps.** The same MK is wrapped a second time by a printable
recovery key (100 bits of entropy, Crockford base32 — no I/L/O/U, so it can be
transcribed from paper without ambiguity). Either secret opens the register;
neither can be derived from the other. Changing the passphrase re-wraps the MK
only — no data is re-encrypted, and the recovery key continues to work.

This design was chosen so Shamir's Secret Sharing can later be added as an
additional wrap for inheritance, without re-encrypting existing data.

**Key handling.** The MK exists only in memory, as a non-extractable WebCrypto
`CryptoKey` (`unwrapKey(..., extractable=false, ["decrypt"])`). It is never
serialised, never written to disk, and never crosses the Rust boundary. Locking
sets `MK = null` and clears the decrypted register from memory — a locked app
is not a screen over readable data; there is nothing to read.

**Salts and IVs** are freshly generated per operation from
`crypto.getRandomValues` — 16 bytes for PBKDF2 salts, 12 bytes for AES-GCM IVs.
AES-GCM provides authenticated encryption, so tampering with the stored blob
causes decryption to fail rather than yield attacker-influenced plaintext.

**No recovery path exists by design.** No backdoor, no escrow, no reset. Losing
both the passphrase and recovery key means permanent, total loss. This is
stated plainly to the user before setup completes.

---

## 4. Storage

**At rest.** The register — including photographs and attached PDFs — is
serialised, sealed, and stored as a single ciphertext blob. A canary test
confirmed that maker, model, serial numbers, owner name and values do not
appear anywhere in the raw on-disk bytes.

**Two locations, deliberately.** As of v1.15.0 the sealed blob is written both
to IndexedDB and to a file at a path the application controls
(`<app data dir>/register.vault`), via Rust commands in `src-tauri/src/lib.rs`.

The file is currently a **mirror only** — IndexedDB remains the source of truth
and nothing reads from the file yet. It exists so it can be verified before
anything depends on it; the app provides a "Verify native file copy" action
that reads it back and compares byte-for-byte against the database.

*Why:* WebKit derives its storage location by hashing an origin salt it
controls. When that salt regenerated on a test machine, the register was
silently orphaned — no error, an app that appeared freshly installed. Storage
identity must belong to the application, not the webview.

Writes are atomic (temp file + rename), so an interrupted write cannot truncate
the only copy.

**Only ciphertext crosses the Rust boundary.** The blob is sealed in the
webview before `store_write` is called. The Rust side never sees a passphrase,
a key, or plaintext.

**Vault export.** Users can export a portable `.vault.json` using the same
envelope encryption, for offsite backup or handing to an executor.

---

## 5. Application boundary

`app.withGlobalTauri` is enabled so the page can invoke the three storage
commands. This exposes the Tauri IPC bridge to page context.

**Assessment:** the risk of an exposed IPC bridge is that hostile script
reaches it. No *remote* script can — `connect-src 'none'` and `default-src
'self'` mean nothing external loads. The three exposed commands read and write
one fixed filename inside the app's own data directory; none accept a
caller-supplied path.

**A reviewer found the gap in the original version of this claim, and it was
real.** An earlier draft asserted there was "no user-supplied HTML rendering
path". That was wrong. Imported files supplied their own record identifiers,
which were interpolated unescaped into a `data-id` attribute — a crafted
import could break out of the attribute and install a working event handler.
Combined with the exposed bridge, that is a genuine path from "user opens a
malicious backup file" to "script invokes native commands".

Fixed in v1.17.0 at both levels: identifiers and URLs are escaped at render,
and imported records have their identifiers regenerated rather than trusted,
with attachment payloads filtered to an allowlist of `data:` types
(`javascript:`, `data:text/html` and SVG are all rejected). 17 assertions
cover it.

The residual risk is unchanged in kind: any future unescaped interpolation of
untrusted data becomes reachable because the bridge is exposed. **This remains
the weakest structural claim in the design.** The stronger fix — dropping
`withGlobalTauri` in favour of an imported `invoke` — currently conflicts with
the zero-build-step frontend, and that trade has not been made yet.

---

## 6. Build and supply chain

- Builds run on GitHub-hosted runners from a tagged commit. Nothing is
  compiled on a developer machine.
- `Cargo.lock` pins 419 crates; CI runs `cargo check --locked`, so a
  dependency cannot change what ships without a reviewable commit.
- Zero npm runtime dependencies in the frontend. No bundler, no transpiler,
  no minifier — the shipped `index.html` is the reviewed `index.html`.
- A pre-release check gate (`tools/check-frontend.py`) fails the build if
  `connect-src 'none'` is ever removed from the CSP, among other guards.
- Source is public and readable. A security tool whose claims cannot be
  audited is not worth trusting.

**Current gap:** builds are ad-hoc signed, not notarized by Apple. Users see a
Gatekeeper warning on first launch. Notarization is planned.

---

## 7. Known limitations

Listed deliberately. A reviewer should start here.

1. **Unlocked-state memory exposure.** While unlocked, the decrypted register
   is in webview memory. Malware running as the user, or a memory dump of a
   running process, would expose it. Standard for any application with
   decrypted data in memory; no mitigation attempted.
2. **`withGlobalTauri` exposes the IPC bridge** to page context (§5). One
   XSS path through imported files was found by review and fixed; the
   structural exposure remains.
3. **Not notarized.** Users must bypass Gatekeeper on first launch, which is
   exactly the habit a security tool should not be teaching.
4. **PBKDF2 rather than Argon2id.** 250,000 SHA-256 iterations is above the
   OWASP floor (210,000) but PBKDF2 is not memory-hard, so it is weaker
   against GPU/ASIC attack than Argon2id would be. The constraint is
   WebCrypto, which does not implement Argon2. Moving key derivation into
   Rust would allow Argon2id and is the clearest available hardening.
5. **No rate limiting on unlock attempts.** An attacker with the file can
   attempt offline derivation without restriction; security rests entirely on
   passphrase entropy and the KDF cost.
6. **No secure deletion.** Deleting the register unlinks the file; it does not
   overwrite. SSD wear-levelling makes true erasure unreliable anyway, but this
   is not currently attempted or claimed.
7. **Recovery key is displayed on screen once.** If the machine is already
   compromised at setup time, it is captured. There is no way to avoid this
   without out-of-band delivery.
8. **Migration exposure (historical).** Databases created before at-rest
   encryption retain plaintext in freed SQLite pages until overwritten. New
   installs are unaffected; the fix for an affected machine is a clean rebuild
   from an encrypted vault export.

---

## 8. Verification steps for a reviewer

```bash
# no network primitives in the frontend
grep -cE "fetch\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon" src/index.html

# CSP forbids all outbound connections
python3 -c "import json;print(json.load(open('src-tauri/tauri.conf.json'))['app']['security']['csp'])"

# complete set of granted native capabilities
cat src-tauri/capabilities/*.json

# entire Rust dependency surface
sed -n '/\[dependencies\]/,/^\[/p' src-tauri/Cargo.toml

# all cryptography, ~40 lines
grep -n "crypto.subtle" src/index.html
```

Runtime: launch the app, open developer tools, and confirm the Network panel
stays empty through a full session including save, export and document
attachment.

---

*Watch Register — Bradley Waye. Source-available under PolyForm Noncommercial
1.0.0. Security reports: open an issue, or email for anything sensitive.*
