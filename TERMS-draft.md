# Terms of Service & End-User Licence Agreement

Watch Register v1.x · Last updated 24 July 2026

---

## 1. What you are licensed

**Licensed, not sold.** Subject to these Terms you are granted a personal,
non-exclusive, non-transferable licence to install and use this Application on
machines you own or control.

**What the licence covers, and what is already free.** The source code of this
Application is public and licensed under the
[PolyForm Noncommercial 1.0.0](./LICENSE) licence: anyone may read, audit,
build and use it for personal, charitable, educational or research purposes at
no charge, and nothing in these Terms restricts that. What is licensed here is
the *distributed build* — the compiled, signed, packaged Application and its
updates. Commercial use of the software in any form requires a separate
licence from WayeCollect Software LLC ("the Company").

**Duration.** The licence is perpetual for the product generation you
purchased, and includes updates released within that generation. It is not
tied to version numbers: minor and patch releases are frequent and never
affect your access. A future generation representing a substantially
redesigned product may be offered separately.

**Termination.** The licence terminates if you materially breach these Terms
and do not remedy the breach within 32 days of written notice, matching the
cure period in the PolyForm licence. Termination does not affect data you have
already created — your vault files and register remain yours and remain
readable by any build you already hold.

---

## 2. Local-first architecture, and what that means for you

**The Application cannot transmit your data.** This is not a promise of
restraint; it is an architectural constraint. The Content Security Policy sets
`connect-src 'none'`, which disables `fetch`, `XMLHttpRequest`, `WebSocket`,
`EventSource` and `sendBeacon` at the engine level. The application grants no
network capability and contains no HTTP client. There are no servers, no
accounts, no telemetry, no analytics, no crash reporting and no update checks.

**No personal data is collected.** The developer receives nothing about you,
your collection, your usage or your device — not in aggregate, not
anonymised, not at all. There is no data controller, no processor, and no
data to subject to an access or deletion request, because none is ever
transmitted or held.

**Where your data lives.** Your register is stored as a single encrypted blob
in two places on your own machine: the application's local database and a file
at `register.vault` inside the application's data directory. Photographs and
attached documents are inside that blob. Encryption is AES-256-GCM via the
platform's WebCrypto implementation; a random master key encrypts your data
and is itself wrapped by keys derived from your secrets using PBKDF2-SHA256 at
250,000 iterations.

**Two ways in, both yours alone.** Your register can be opened by your
passphrase or by the recovery key shown once during setup. Neither can be
derived from the other. The developer holds neither, can reconstruct neither,
and has no mechanism to recover either.

**Your responsibilities.** You are solely responsible for choosing and
safeguarding your passphrase, for storing your recovery key somewhere safe and
separate, for the security of your device, and for maintaining your own
backups — including any encrypted `.vault.json` files you export.

**Unrecoverable loss.** If you lose **both** your passphrase and your recovery
key, your register cannot be opened by anyone, including the Company. This
is a deliberate property of the design, disclosed to you before setup
completes and repeatedly in the Application. Likewise, hardware failure or
deletion without a backup is unrecoverable. **The developer accepts no
liability of any kind for data that becomes unrecoverable for these or any
other reasons.**

---

## 3. Valuations, insurance and financial figures

**Every figure originates with you.** The Application does not appraise, does
not fetch market prices, and does not connect to any pricing service — it
cannot, per Section 2. Market values, purchase prices, insured values and any
figure the Application displays are values **you entered**. Totals, gains,
losses and coverage warnings are arithmetic performed on your own inputs.

**Informational only.** Those outputs exist for personal record-keeping and
organisation. They are not an appraisal, a valuation, or financial, tax, legal
or insurance advice. The developer is not a licensed appraiser, broker,
adjuster, fiduciary or advisor, and no professional relationship is created by
your use of the Application.

**Insurance figures in particular.** Coverage indicators — including whether a
piece is flagged as underinsured, and any payout ceiling calculated from a
policy type you selected — are estimates derived from what you entered. They
do not reflect your actual policy, your insurer's terms, or how a claim would
be settled. Printed schedules and registers are working documents you produce,
not certified appraisals.

**Verify before relying on any of it.** Confirm valuations with a qualified
appraiser and coverage with your insurer or broker. **The developer assumes no
liability for denied or disputed claims, underinsurance, valuation
discrepancies, tax positions, or any financial outcome connected to figures
displayed by the Application.**

---

## 4. Source code, auditability and permitted use

**The source is public, deliberately.** A security tool whose claims cannot be
independently verified is not worth trusting. You are explicitly encouraged to
read, analyse, build and audit the source code, and to verify every claim in
these Terms and in the security documentation against it. Nothing in these
Terms restricts that, and no clause here should be read as prohibiting reverse
engineering of published source.

**Reporting a vulnerability.** Security issues may be reported through the
project's issue tracker, or by email for anything sensitive. Findings are
welcome, including ones that contradict the Company's own claims.

**What is restricted.** You may not resell, sublicense, rent, lease, or
redistribute the Application or a modified version of it, and you may not use
it commercially, except under a separate licence from the Company.
"Commercial" is as defined in the PolyForm Noncommercial 1.0.0 licence, which
governs the source code and takes precedence in any conflict with this
section. Branding, name, logo and documentation remain the Company's
property.

---

## 5. As-is delivery, liability and governing law

**As-is.** The Application is provided "AS IS" and "AS AVAILABLE", without
warranty of any kind, express or implied, including implied warranties of
merchantability, fitness for a particular purpose, and non-infringement. The
developer does not warrant that the Application is free of defects or that it
will meet your requirements.

**Distribution and signing.** Builds are produced by an automated public
pipeline from tagged source. You are responsible for obtaining the Application
from the official distribution channel; the Company is not responsible for
modified, repackaged or third-party-hosted copies.

**Limitation of liability.** To the maximum extent permitted by law, the
developer shall not be liable for any indirect, incidental, special, punitive
or consequential damages, nor for lost revenue, lost or corrupted data, loss
of physical assets, or legal expenses, arising from use of or inability to use
the Application. Where liability cannot be excluded, total aggregate liability
is limited to the amount you paid for the licence in the twelve months
preceding the claim.

**Capacity.** You must be of legal age to form a binding contract in your
jurisdiction.

**Successors and heirs.** The Application is intended in part for estate
records. Anyone you grant access to — an executor, heir or advisor — is bound
by these Terms when using the Application. The developer has no role in your
succession arrangements, holds no keys, and cannot grant access to anyone.

**Changes.** These Terms may be updated for future releases. The version
accompanying the build you have installed governs your use of that build.

**Governing law.** These Terms are governed by the laws of the State of
Georgia, USA, without regard to conflict of law principles.

**Severability.** If any provision is held unenforceable, the remainder stays
in force.

---

*Watch Register, published by WayeCollect Software LLC. Source: github.com/bwaye3/WayCollect ·
Commercial licensing: bradwaye@gmail.com*
