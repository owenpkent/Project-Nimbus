# Business Model — Project Nimbus

## Overview

This document explores sustainable business models for Project Nimbus, grounded in real market data from comparable software products. The core tension: **the people who need this most are often least able to pay for it**, while the software has genuine commercial value. The recommended approach resolves this with a **freemium + subscription** model that keeps the core free forever while monetizing advanced features used by power users and organizations.

---

## Market Research

### The Addressable Market

| Segment | Size | Source |
|---------|------|--------|
| Global gamers | ~3.2 billion | Statista 2024 |
| Gamers with disabilities | ~640 million (est. 20%) | AbleGamers / accessibility.com |
| US gamers with disabilities | ~46 million | AbleGamers |
| Global assistive technology market | $26.8B (2024) → $41B (2033) | IMARC Group |
| AT market CAGR | 4.3–4.8% | Multiple analysts |
| Subscription gaming market | $10.9B (2024) → $17.5B (2029) | GlobeNewswire |

**Key insight:** 20% of the gaming population has a disability. This is not a niche — it's 1 in 5 players. The challenge is that this population is price-sensitive and underserved, making freemium + institutional sales the right model.

### What Comparable Software Charges

#### Controller Remapping / Input Software

| Product | Model | Price | Notes |
|---------|-------|-------|-------|
| **reWASD** | Subscription | $29/yr (1 device), $39/yr (2), $49/yr (3) | Recently switched from one-time; community backlash |
| **reWASD** (legacy) | One-time | $6–$20 | Old model, still referenced fondly |
| **Xpadder** | One-time | $9.99 | Simple, long-running |
| **JoyToKey** | Shareware | Free / ~$7 donation | Minimal, keyboard-only mapping |
| **AntiMicroX** | Free / Open source | $0 | No monetization |
| **DS4Windows** | Free / Open source | $0 | No monetization |
| **Controller Companion** | One-time (Steam) | $2.99 | Steam-distributed |

#### Voice Control Software

| Product | Model | Price | Notes |
|---------|-------|-------|-------|
| **VoiceAttack** | One-time | $10 | Perpetual license, no subscription |
| **Dragon Professional** | One-time | $500–$700 | Enterprise dictation, not gaming-focused |
| **Talon Voice** | Free + Patreon | $0 / ~$15/mo Patreon | Hands-free coding/gaming; community-funded |
| **HCS VoicePacks** | One-time + subscription | $15–$40 packs | Voice packs for Elite Dangerous, Star Citizen |
| **DeepGram** (API) | Usage-based | $0.0043/min | Infrastructure cost, not end-user product |

#### Accessibility / Adaptive Gaming Tools

| Product | Model | Price | Notes |
|---------|-------|-------|-------|
| **Xbox Adaptive Controller** | Hardware one-time | $99.99 | Microsoft hardware |
| **Xbox Adaptive Joystick** | Hardware one-time | $29.99 | Launched early 2025 |
| **Logitech Adaptive Gaming Kit** | Hardware one-time | $99.99 | Button/switch accessories |
| **SpecialEffect custom setups** | Free (charity) | $0 | Funded by donations |
| **AbleGamers consultations** | Free (nonprofit) | $0 | Funded by donations/grants |

### What Users Are Already Spending

Based on market data and community research:

- **Casual accessibility users:** Willing to pay $0–$10 one-time; resistant to subscriptions
- **Power users / sim enthusiasts:** $10–$30/yr subscriptions acceptable (reWASD precedent)
- **Organizations (hospitals, rehab centers, VA):** $50–$500/yr per seat; prefer annual invoicing
- **Corporate sponsors:** $5,000–$50,000/yr for brand association
- **Grant funding:** $10,000–$500,000 per grant cycle

**Key market lesson from reWASD:** Their switch to subscriptions caused significant community backlash. Their $29/yr base plan is considered "too expensive" by many users. **$5–$10/mo or $30–$50/yr is the ceiling for individual users** in this space.

---

## Recommended Model: Freemium + Pro Subscription

### Core Principle

> **The disability community gets everything they need for free. Power users and organizations pay for advanced features.**

This is not charity — it's smart positioning. Free users become advocates, drive word-of-mouth, and create the user base that makes the product attractive to sponsors and institutional buyers.

---

## Tier Structure

### Tier 0: Free (Core — Always Free)

Everything needed for accessibility use:

| Feature | Included |
|---------|----------|
| All controller layouts (Flight Sim, Xbox, Adaptive, Custom) | ✅ |
| vJoy + ViGEm integration | ✅ |
| Profile system (unlimited profiles) | ✅ |
| Sensitivity curves, deadzones | ✅ |
| Custom layout builder | ✅ |
| Basic button mapping | ✅ |
| Game Focus Mode | ✅ |
| Community support | ✅ |

**Rationale:** This is the accessibility mission. No one with a disability should hit a paywall for basic controller access.

---

### Tier 1: Nimbus Pro — $4.99/mo or $39/yr

Advanced features for power users:

| Feature | Description |
|---------|-------------|
| **Voice Commands** | Built-in voice control (Faster-Whisper offline engine) |
| **Macro System** | Record and replay input sequences; time-based triggers |
| **Advanced Profiles** | Unlimited cloud sync + backup of profiles |
| **Per-Game Auto-Switch** | Automatically load profile when a game launches |
| **Priority Support** | Email support with 48hr response |
| **Early Access** | Beta features before public release |

**Price rationale:**
- Below reWASD's $29/yr base (more features, better value)
- VoiceAttack charges $10 one-time for voice alone — bundling it with macros at $39/yr is competitive
- $4.99/mo is below the psychological "coffee" threshold

---

### Tier 2: Nimbus AI — $9.99/mo or $79/yr

AI-powered features (Spectator+ and beyond):

| Feature | Description |
|---------|-------------|
| Everything in Pro | ✅ |
| **Spectator+ Mode** | AI-assisted play — you direct, AI executes |
| **AI Macro Generation** | Describe what you want in plain language; AI builds the macro |
| **DeepGram Cloud Voice** | Higher-accuracy cloud voice recognition (uses managed API key) |
| **Adaptive Assistance Slider** | 0–100% AI control blend per game |
| **Community Model Library** | Download pre-trained game agents from community |

**Price rationale:**
- AI features have real infrastructure costs (DeepGram API, compute)
- $9.99/mo is the standard "mid-tier" SaaS price point (Spotify, etc.)
- Comparable to HCS VoicePacks subscriptions for Elite Dangerous

---

### Tier 3: Nimbus Institutional — $199/yr per seat (min. 5 seats)

For hospitals, rehab centers, VA facilities, schools:

| Feature | Description |
|---------|-------------|
| Everything in AI tier | ✅ |
| **Admin Dashboard** | Manage profiles across multiple patients/users |
| **Centralized Profile Library** | Push profiles to users remotely |
| **Usage Analytics** | Track which features help which users |
| **Dedicated Support** | Named support contact, 24hr response |
| **Custom Onboarding** | Setup call + training for staff |
| **Invoicing** | Annual invoice (no credit card required) |

**Price rationale:**
- Hospitals pay $500–$2,000/yr per seat for specialized software
- $199/yr is deliberately accessible for smaller clinics and nonprofits
- Volume discounts available for large deployments

---

## Revenue Scenarios

### Scenario A: Grassroots (Year 1)

Conservative assumptions: small but engaged community.

| Segment | Users | Conversion | Revenue |
|---------|-------|-----------|---------|
| Free users | 5,000 | — | $0 |
| Pro subscribers | 200 (4%) | $39/yr | $7,800 |
| AI subscribers | 50 (1%) | $79/yr | $3,950 |
| Institutional seats | 20 seats | $199/yr | $3,980 |
| GitHub Sponsors | 30 | $10/mo avg | $3,600 |
| **Total ARR** | | | **~$19,330** |

*Enough to cover part-time development hours.*

---

### Scenario B: Moderate Growth (Year 2–3)

After press coverage, AbleGamers partnership, one corporate sponsor.

| Segment | Users | Conversion | Revenue |
|---------|-------|-----------|---------|
| Free users | 25,000 | — | $0 |
| Pro subscribers | 750 (3%) | $39/yr | $29,250 |
| AI subscribers | 200 (0.8%) | $79/yr | $15,800 |
| Institutional seats | 100 seats | $199/yr | $19,900 |
| Corporate sponsor (1x Silver) | — | — | $10,000 |
| GitHub Sponsors | 100 | $10/mo avg | $12,000 |
| **Total ARR** | | | **~$86,950** |

*Enough for one full-time developer salary in many markets.*

---

### Scenario C: Established (Year 3–5)

After multiple sponsors, grant funding, institutional adoption.

| Segment | Users | Conversion | Revenue |
|---------|-------|-----------|---------|
| Free users | 100,000 | — | $0 |
| Pro subscribers | 2,000 (2%) | $39/yr | $78,000 |
| AI subscribers | 500 (0.5%) | $79/yr | $39,500 |
| Institutional seats | 500 seats | $199/yr | $99,500 |
| Corporate sponsors (2x Gold) | — | — | $50,000 |
| Grant funding | — | — | $50,000 |
| GitHub Sponsors | 300 | $10/mo avg | $36,000 |
| **Total ARR** | | | **~$353,000** |

*Small team of 2–3 people. Sustainable long-term.*

---

## Feature Gating Strategy

### What Should Never Be Gated

The following must remain free to preserve the accessibility mission and avoid community backlash:

- All hardware integration (vJoy, ViGEm)
- All built-in profiles and layouts
- Custom layout builder
- Sensitivity and deadzone configuration
- Game Focus Mode
- Basic button mapping

### What Makes Sense to Gate

| Feature | Why It's Gateable |
|---------|------------------|
| **Voice commands** | Real infrastructure cost (model download, compute); VoiceAttack charges $10 for this alone |
| **Macros** | Power-user feature; not needed for basic accessibility |
| **Cloud profile sync** | Storage cost; local profiles always free |
| **AI/Spectator+** | Significant compute cost; clearly "advanced" |
| **Per-game auto-switch** | Convenience feature, not accessibility-critical |
| **Institutional dashboard** | B2B feature with real support cost |

### What Should NOT Be Gated (Even If Tempting)

| Feature | Why Keep Free |
|---------|--------------|
| **Offline voice (basic)** | If a user's disability requires voice, gating it is a barrier |
| **Profile switching** | Core accessibility feature |
| **Any layout type** | Adaptive Platform users need all layouts |

**Resolution for voice:** Offer a **limited free voice tier** (e.g., 50 commands/day offline with Vosk constrained grammar) and **unlimited voice** in Pro. This gives accessibility users a working solution while incentivizing upgrade.

---

## Implementation: Technical Requirements

### Licensing / Auth

- **License server** — Simple JWT-based license validation (can self-host or use Keygen.sh ~$29/mo)
- **Offline grace period** — 7-day offline use without re-validation (critical for users without reliable internet)
- **No feature removal** — If subscription lapses, Pro features disable gracefully; no data loss

### Payment Infrastructure

| Option | Fee | Notes |
|--------|-----|-------|
| **Stripe** | 2.9% + $0.30 | Industry standard; supports subscriptions, invoicing |
| **Paddle** | 5% | Handles VAT/tax globally; good for international |
| **GitHub Sponsors** | 0% (GitHub covers) | For open-source community funding |
| **Gumroad** | 10% | Simple but expensive |

**Recommendation:** Stripe for Pro/AI/Institutional; GitHub Sponsors for community donations.

### Distribution

| Channel | Tier | Notes |
|---------|------|-------|
| **GitHub Releases** | Free tier | Direct download, no account required |
| **Project website** | All tiers | License purchase + download |
| **Steam** | Free tier (future) | Massive discovery potential; Steam handles payment |
| **Microsoft Store** | Free tier (future) | Accessibility visibility; Windows-native |

**Steam note:** Steam takes 30% but provides enormous discovery. A free Steam listing with in-app Pro upgrade is worth exploring. Steam supports DLC-style unlocks that could serve as the Pro license.

---

## Competitive Positioning

| | Project Nimbus Free | Nimbus Pro | reWASD | VoiceAttack | AntiMicroX |
|--|--|--|--|--|--|
| **Price** | $0 | $39/yr | $29/yr | $10 one-time | $0 |
| **Accessibility focus** | ✅ Primary | ✅ | ⚠️ Secondary | ❌ | ⚠️ |
| **Voice control** | Limited | ✅ | ❌ | ✅ | ❌ |
| **Custom layouts** | ✅ | ✅ | ⚠️ | ❌ | ❌ |
| **AI features** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **AI features (AI tier)** | — | — | ❌ | ❌ | ❌ |
| **Open source** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **vJoy + ViGEm** | ✅ | ✅ | ✅ | ❌ | ❌ |

**Unique position:** No competitor combines accessibility-first design + open source + voice + AI. This is a defensible niche.

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| **Community backlash to subscriptions** | Medium | Keep core free; communicate clearly; grandfather early users |
| **reWASD backlash precedent** | Medium | Never gate accessibility features; be transparent about what's free |
| **Low conversion rate** | Medium | Focus on institutional sales + sponsorships as primary revenue |
| **AI compute costs exceed revenue** | Low | Cap AI tier usage; use local models where possible |
| **Competitor copies features** | Low | Open source + community trust is the moat |
| **Disability community distrust** | Low | Developer with disability + nonprofit partnerships = credibility |

---

## Recommended Launch Sequence

### Phase 1: Free Only (Now → 6 months)
- Build user base, gather feedback
- Set up GitHub Sponsors
- Establish nonprofit partnerships (AbleGamers, SpecialEffect)
- Track usage metrics

### Phase 2: Pro Launch (6–12 months)
- Launch voice commands + macros as Pro features
- Introduce $39/yr Pro tier
- Grandfather early adopters (free Pro for 1 year)
- Apply for first grants

### Phase 3: AI Tier + Institutional (12–24 months)
- Launch Spectator+ as AI tier feature
- Approach hospitals and rehab centers for institutional licenses
- Pursue corporate sponsorships with usage data in hand

### Phase 4: Platform Expansion (24+ months)
- Steam listing (free tier)
- Microsoft Store listing
- Consider 501(c)(3) nonprofit status for grant eligibility

---

## Summary Recommendation

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| **Core model** | Freemium | Accessibility mission; community trust |
| **Pro price** | $39/yr | Below reWASD; above "free" threshold |
| **AI price** | $79/yr | Reflects real compute costs |
| **Institutional** | $199/yr/seat | Accessible for small clinics |
| **Payment** | Stripe | Industry standard |
| **Voice gating** | Limited free / unlimited Pro | Balances mission and sustainability |
| **Open source** | Keep MIT | Trust, adoption, sponsor appeal |
| **Primary revenue** | Institutional + sponsorships | More reliable than individual subscriptions |

---

## Related Documents

- [Release Strategy](RELEASE_STRATEGY.md) — open source philosophy and funding overview
- [Sponsorship Outreach](SPONSORSHIP_OUTREACH.md) — corporate sponsor templates
- [Voice Command Integration](VOICE_COMMAND.md) — technical implementation of voice features
- [Spectator+ Concept](SPECTATOR_PLUS.md) — AI tier feature details
- [AI Game Player Proposal](../../research/ai-game-player/proposal.md) — full technical proposal
