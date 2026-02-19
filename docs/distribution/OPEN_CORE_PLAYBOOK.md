# Open Core Playbook — Project Nimbus

## What Is Open Core?

**Open Core** is the standard industry model for software that is both open source and commercially sustainable. The term was coined by Andrew Lampitt and is used by some of the most successful software companies in the world:

| Company | Open Core | Paid Layer |
|---------|-----------|------------|
| **GitLab** | GitLab CE (MIT) | GitLab EE (proprietary features) |
| **Metabase** | OSS edition (AGPL) | Enterprise Edition (proprietary license) |
| **Sentry** | Self-hosted (BSL) | Sentry.io (managed cloud) |
| **Elasticsearch** | Core (Apache 2.0) | X-Pack features (proprietary) |
| **MySQL** | GPL | Oracle Enterprise (proprietary) |
| **VS Code** | Open source core | Microsoft binary + proprietary extensions |
| **IntelliJ** | Community Edition (Apache) | Ultimate Edition (proprietary) |

**The pattern:** A fully functional open source version exists that anyone can use, modify, and self-host. A paid version adds features that power users, organizations, or cloud customers pay for. The open source version is not crippled — it's genuinely useful on its own.

---

## Is This Standard Practice?

Yes. It is the dominant model for developer tools and infrastructure software. The key insight from the industry:

> *"Open source is the distribution strategy. The business model is what you build on top of it."*
> — common framing in the OSS business community

The model works because:
1. Open source drives adoption at zero marketing cost
2. Users who love it become paying customers or advocates
3. Organizations that depend on it pay for support, features, or convenience
4. The community contributes improvements back, reducing development cost

---

## The Two-Repo Question

You asked about having two repos: one public (open source) and one private (admin/monetization). This is a real pattern, but the industry has largely learned that **it creates significant pain**. Here's the honest breakdown:

### Option A: Two Separate Repos (Your Initial Idea)

```
github.com/owenpkent/project-nimbus          ← Public, MIT, open source
github.com/owenpkent/project-nimbus-admin    ← Private, Pro/AI features + billing
```

**How it works:**
- Public repo contains the core application
- Private repo contains Pro/AI feature modules + license server + billing code
- At build time, private modules are merged/injected into the distributable
- Users who build from source get the free version; users who download the binary get the full app with license gating

**Real-world precedent:** This is how Metabase started. They ran it for a while, then abandoned it.

**Why Metabase abandoned two repos (their own words):**
> *"We had originally developed the Enterprise Edition in a private GitHub repository... Pretty soon, we ran into some problems. Since the OSS and EE code lived in separate repositories, we were constantly dealing with merge conflicts."*

**Pros:**
- Clean separation — no one can see your billing/license code
- Simpler contributor license agreement story (OSS contributors only touch the public repo)

**Cons:**
- **Merge conflicts constantly** — every change to core has to be synced to the private repo
- **Two CI/CD pipelines** to maintain
- **Two issue trackers** — users file bugs in the wrong place
- **Harder to develop** — you're always context-switching between repos
- **Doesn't actually protect much** — the feature gating logic is in the binary anyway

---

### Option B: One Repo, License-Gated Features (Industry Standard)

```
github.com/owenpkent/project-nimbus          ← Public, everything visible
├── src/                                      ← Core (MIT)
├── src/pro/                                  ← Pro features (source visible, license-gated)
└── src/ai/                                   ← AI features (source visible, license-gated)
```

**How it works:**
- All code lives in one repo
- Pro/AI feature directories have a different license header (e.g., Nimbus Commercial License)
- The code is visible but not freely usable without a license key
- At runtime, features check for a valid license before activating

**Real-world precedent:** GitLab, Metabase (after they merged), Sentry, Elasticsearch.

**Pros:**
- One codebase, one CI/CD pipeline, one issue tracker
- No merge conflicts
- Easier to develop — everything in one place
- Community can see what Pro features exist (builds trust, drives upgrades)
- Contributors can still contribute to core

**Cons:**
- Pro feature source code is visible (competitors can read it)
- Requires clear license headers and contributor agreements

**Verdict: This is the right model for Project Nimbus.** The "secret sauce" isn't the feature code — it's your accessibility expertise, your community, and your relationships. Hiding the code doesn't protect that.

---

### Option C: One Repo + Separate Private Billing/Admin Repo

```
github.com/owenpkent/project-nimbus          ← Public (open core)
github.com/owenpkent/nimbus-platform         ← Private (license server, billing, admin dashboard)
```

**How it works:**
- The application code (including Pro/AI features) lives in the public repo
- The *infrastructure* — license server, Stripe integration, admin dashboard, customer database — lives in a private repo
- Users who self-host get the app; the license server validates their key against your private backend

**This is actually the right split.** The distinction is:
- **Application code** → public repo (open core)
- **Business infrastructure** → private repo (not open source, not part of the app)

**Pros:**
- Clean: the app is open, the business backend is private
- No merge conflict problem (they're genuinely separate concerns)
- Billing/customer data stays private (as it should)
- License server can't be trivially forked

**Cons:**
- Requires running a license validation service
- Users need internet to activate (mitigated by offline grace period)

---

## Recommended Architecture for Project Nimbus

### Repo 1: `project-nimbus` (Public)

```
github.com/owenpkent/project-nimbus
├── LICENSE-MIT              ← Core license
├── LICENSE-COMMERCIAL       ← Pro/AI feature license
├── src/
│   ├── bridge.py            ← MIT
│   ├── vjoy_interface.py    ← MIT
│   ├── vigem_interface.py   ← MIT
│   ├── config.py            ← MIT
│   ├── pro/                 ← Nimbus Commercial License
│   │   ├── voice_interface.py
│   │   ├── macro_engine.py
│   │   └── profile_sync.py
│   └── ai/                  ← Nimbus Commercial License
│       ├── spectator.py
│       ├── screen_capture.py
│       └── agent_interface.py
├── qml/                     ← MIT
├── profiles/                ← MIT
└── src/license_check.py     ← MIT (validates key, enables pro/ai modules)
```

**License structure:**
- `src/` (core) → MIT — anyone can use, fork, modify, redistribute
- `src/pro/` → Nimbus Commercial License — source visible, requires paid license to run
- `src/ai/` → Nimbus Commercial License — same

### Repo 2: `nimbus-platform` (Private)

```
github.com/owenpkent/nimbus-platform   ← PRIVATE, never public
├── license-server/          ← FastAPI service: issue/validate license keys
│   ├── main.py
│   ├── models.py
│   └── stripe_webhooks.py
├── admin-dashboard/         ← Internal: manage customers, seats, usage
├── billing/                 ← Stripe integration, subscription management
├── customer-db/             ← Customer records (never in public repo)
└── deploy/                  ← Hosting config (Railway, Fly.io, etc.)
```

This repo **never ships to users**. It's pure business infrastructure. No merge conflict risk with the app repo.

---

## License Strategy

### The Core License: MIT (unchanged)

The `src/` core keeps MIT. This is non-negotiable for community trust and sponsor appeal.

### The Pro/AI License: Nimbus Commercial License (custom)

A simple custom license for `src/pro/` and `src/ai/` that says:

```
Nimbus Commercial License v1.0

Copyright (c) 2025 Owen Kent

Source code in this directory is made available for inspection and
contribution under the following terms:

1. You may read, study, and contribute to this code.
2. You may NOT use this code in production without a valid Nimbus Pro
   or Nimbus AI license key obtained from projectnimbus.io.
3. You may NOT redistribute this code or use it in other products.
4. Contributions to this directory require signing the Nimbus CLA.

For licensing inquiries: licensing@projectnimbus.io
```

**Why not AGPL or BSL?**
- AGPL is complex and scares corporate users
- BSL (Business Source License, used by HashiCorp/Sentry) is good but has a 4-year conversion clause that may not fit
- A simple custom license is clearer for a small project

### Contributor License Agreement (CLA)

For contributions to `src/pro/` and `src/ai/`, contributors must sign a CLA granting you the right to use their contribution commercially. This is standard practice (used by Google, Microsoft, HashiCorp).

For contributions to `src/` (MIT core), no CLA needed — MIT handles it.

**Simple CLA tool:** [CLA Assistant](https://cla-assistant.io/) — free, GitHub-integrated, automated.

---

## What "Build It Yourself" Gets You

A user who clones the public repo and builds from source gets:

| Feature | Self-Built (Free) | Licensed Binary |
|---------|------------------|-----------------|
| All core layouts | ✅ | ✅ |
| vJoy + ViGEm | ✅ | ✅ |
| Custom layout builder | ✅ | ✅ |
| Profile system | ✅ | ✅ |
| Voice commands | ❌ (code present, key required) | ✅ Pro |
| Macros | ❌ (code present, key required) | ✅ Pro |
| Spectator+ | ❌ (code present, key required) | ✅ AI |
| Cloud profile sync | ❌ | ✅ Pro |

The Pro/AI code is visible in the repo — a technically sophisticated user could remove the license check. This is acceptable. The people who will do that are not your customers. Your customers are:
- Users who want a working installer (not a build environment)
- Organizations that need support and invoicing
- People who want to support the project

This is the same calculus that GitLab, Sentry, and every other open core company has made.

---

## The Self-Hosted Angle

You mentioned "self-hosted stuff you don't have to pay for." This is a real model — **Sentry** is the canonical example:

- `getsentry/sentry` on GitHub — fully open source, self-hostable
- `sentry.io` — managed cloud, paid
- The self-hosted version is fully functional; the cloud version is convenient

For Project Nimbus, this translates to:

| Version | Who | Cost | What They Get |
|---------|-----|------|---------------|
| **Self-built from source** | Developers, tinkerers | $0 | Core only (Pro features gated) |
| **Free installer** | End users | $0 | Core, no build required |
| **Pro license** | Power users | $39/yr | Voice, macros, sync |
| **AI license** | Advanced users | $79/yr | Spectator+, AI features |
| **Institutional** | Hospitals, VA | $199/seat/yr | All features + support |

The "self-hosted" model doesn't quite apply to a desktop app the same way it does to a web service — there's no server to host. But the spirit is the same: **the open source version is genuinely useful, not a demo.**

---

## Practical Setup Steps

### Step 1: Restructure the Repo

Move Pro/AI feature code into `src/pro/` and `src/ai/` subdirectories. Add license headers to those files.

### Step 2: Add License Check Module

```python
# src/license_check.py (MIT licensed)

import os
import requests
from pathlib import Path

LICENSE_SERVER = "https://api.projectnimbus.io/v1/validate"
CACHE_FILE = Path.home() / ".projectnimbus" / "license.cache"
OFFLINE_GRACE_DAYS = 7

def check_license(tier: str = "pro") -> bool:
    """Returns True if a valid license for the given tier is active."""
    key = _load_key()
    if not key:
        return False
    # Try online validation first
    try:
        resp = requests.post(LICENSE_SERVER, json={"key": key, "tier": tier}, timeout=3)
        if resp.ok and resp.json().get("valid"):
            _update_cache(key, tier)
            return True
    except Exception:
        pass
    # Fall back to offline cache (grace period)
    return _check_cache(key, tier)

def _load_key() -> str | None:
    return os.environ.get("NIMBUS_LICENSE_KEY") or _read_stored_key()
```

### Step 3: Gate Pro Features in Bridge

```python
# src/bridge.py
from .license_check import check_license

@Slot()
def toggleVoiceListening(self):
    if not check_license("pro"):
        self.showUpgradeDialog("voice")
        return
    # ... existing voice logic
```

### Step 4: Create the Private Platform Repo

Set up `nimbus-platform` (private) with:
- FastAPI license server (simple: store keys in SQLite or Postgres)
- Stripe webhook handler (create key on subscription activation, invalidate on cancellation)
- Deploy to Railway or Fly.io (~$5–10/mo)

### Step 5: Set Up CLA Assistant

Go to [cla-assistant.io](https://cla-assistant.io), connect your GitHub, point it at a `CLA.md` file in the public repo. Contributors to `src/pro/` and `src/ai/` will be prompted automatically.

---

## Common Pitfalls to Avoid

| Pitfall | What Happens | How to Avoid |
|---------|-------------|--------------|
| **Gating too much** | Community feels cheated; backlash | Keep core genuinely useful |
| **Two app repos** | Merge conflict hell (Metabase learned this) | One app repo, separate platform repo |
| **No offline grace period** | Users lose access when internet drops | 7-day cache in license check |
| **Aggressive license enforcement** | Community distrust | Don't sue hobbyists; focus on commercial use |
| **Forgetting CLA** | Can't legally use community contributions commercially | Set up CLA Assistant early |
| **Hiding the Pro code** | Doesn't protect you; hurts trust | Source-visible is fine; key-gated is enough |

---

## Documentation: What Lives Where

This is a question that comes up immediately: you want to track business planning in GitHub, but you don't want end users reading your revenue projections, sponsorship email templates, or internal strategy.

### The Rule of Thumb

> **If an end user would find it useful → public repo.**
> **If an end user would find it confusing or it reveals business internals → private repo (`nimbus-platform`).**

### Document Routing Table

| Document | Repo | Reason |
|----------|------|--------|
| `docs/development/` (architecture, integration guide, LLM notes) | **Public** | Helps contributors and AI assistants |
| `docs/accessibility/` | **Public** | Builds community trust, helps grant applications |
| `research/ai-game-player/proposal.md` | **Public** | Demonstrates technical depth to partners |
| `docs/distribution/VOICE_COMMAND.md` | **Public** | Feature roadmap; builds excitement, helps sponsors see vision |
| `docs/distribution/SPECTATOR_PLUS.md` | **Public** | Same — accessibility feature concept is public-facing |
| `docs/distribution/BUSINESS_MODEL.md` | **Private** (`nimbus-platform/docs/`) | Revenue projections, conversion rates, pricing strategy |
| `docs/distribution/OPEN_CORE_PLAYBOOK.md` | **Private** (`nimbus-platform/docs/`) | Internal architecture of the monetization system |
| `docs/distribution/RELEASE_STRATEGY.md` | **Private** (`nimbus-platform/docs/`) | Funding models, grant targets, internal roadmap |
| `docs/distribution/SPONSORSHIP_OUTREACH.md` | **Private** (`nimbus-platform/docs/`) | Email templates, pitch decks, partner contacts |

> **Note:** The four private docs currently live in `docs/distribution/` in this public repo. They should be migrated to `nimbus-platform/docs/` when that private repo is created. Until then, they are here for reference and are not yet committed to a public remote.

### Tracking Business Planning in GitHub (Privately)

Once `nimbus-platform` exists as a private GitHub repo, use its native GitHub features for business planning:

#### GitHub Issues — for discrete tasks
```
[nimbus-platform] Issues
├── "Draft AbleGamers sponsorship email"
├── "Set up Stripe account"
├── "Apply for Microsoft Accessibility grant Q3"
└── "Research 501(c)(3) nonprofit filing"
```
Label them: `outreach`, `legal`, `funding`, `infrastructure`

#### GitHub Projects (Kanban) — for pipeline tracking
```
Sponsorship Pipeline board:
  Backlog → Contacted → In Conversation → Proposal Sent → Closed
```
Drag sponsor cards across columns. Attach emails, notes, and dollar amounts as issue comments.

#### GitHub Milestones — for release phases
```
Milestone: "Pro Launch" (target: Q3 2025)
  - [ ] Stripe integration
  - [ ] License server deployed
  - [ ] Voice feature gated
  - [ ] Landing page live

Milestone: "First Institutional Customer"
  - [ ] Admin dashboard MVP
  - [ ] Invoicing flow
  - [ ] Onboarding doc
```

#### GitHub Wiki (private repo) — for living strategy docs
The wiki is separate from the repo file tree — good for documents that change frequently (pricing, contact lists, meeting notes) without cluttering git history.

#### GitHub Discussions (private) — for thinking out loud
Use Discussions for longer-form strategy threads where you want to write out your thinking, revisit it later, and keep a record. Better than a notes app because it's searchable and version-aware.

### What This Looks Like in Practice

```
github.com/owenpkent/project-nimbus          ← Public
├── docs/
│   ├── development/         ← Public: technical docs
│   ├── accessibility/       ← Public: mission docs
│   └── distribution/
│       ├── VOICE_COMMAND.md     ← Public: feature roadmap
│       └── SPECTATOR_PLUS.md   ← Public: feature roadmap
└── research/                ← Public: technical proposals

github.com/owenpkent/nimbus-platform         ← Private
├── docs/
│   ├── BUSINESS_MODEL.md        ← Private: revenue strategy
│   ├── OPEN_CORE_PLAYBOOK.md    ← Private: monetization architecture
│   ├── RELEASE_STRATEGY.md      ← Private: funding roadmap
│   └── SPONSORSHIP_OUTREACH.md  ← Private: partner templates
├── license-server/              ← Private: billing infrastructure
└── admin-dashboard/             ← Private: customer management
```

---

## Real-World Validation

This exact model — one public repo with license-gated subdirectories + a separate private platform repo — is used by:

- **GitLab:** `gitlab-org/gitlab` (public, CE + EE code in one repo) + private infrastructure repos
- **Sentry:** `getsentry/sentry` (public) + private billing/ops repos
- **Metabase:** Merged their two repos into one after learning the hard way
- **Posthog:** `PostHog/posthog` (public, MIT + EE) + private cloud infrastructure

You'd be in very good company.

---

## Summary

| Question | Answer |
|----------|--------|
| **Is this standard practice?** | Yes — it's called Open Core, used by GitLab, Sentry, Metabase, etc. |
| **Two repos for the app?** | No — one app repo. Metabase tried two and merged them. |
| **Private repo for what?** | License server, billing, admin dashboard — business infrastructure only |
| **Can people build it free?** | Yes — core is MIT, Pro features are source-visible but key-gated |
| **Does hiding code protect you?** | No — your moat is community trust, not secret code |
| **What license for Pro features?** | Simple custom Nimbus Commercial License in `src/pro/` and `src/ai/` |

---

## Related Documents

- [Business Model](BUSINESS_MODEL.md) — tier pricing and revenue scenarios
- [Release Strategy](RELEASE_STRATEGY.md) — open source philosophy and funding
- [Voice Command Integration](VOICE_COMMAND.md) — Pro tier voice feature
- [Spectator+ Concept](SPECTATOR_PLUS.md) — AI tier feature
