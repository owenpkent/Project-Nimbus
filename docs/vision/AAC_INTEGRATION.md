# Augmentative & Alternative Communication (AAC) Integration

## The Idea

Project Nimbus is currently framed as a virtual game controller. But its core capability — a **fully customizable, touch/switch/gaze/voice-driven control surface that outputs arbitrary input signals** — is exactly what AAC devices do. The same architecture that lets a user with limited mobility control a game could let them control a communication app, trigger pre-programmed phrases, navigate a speech-generating device, or operate any software that accepts keyboard/mouse/controller input.

> *"AAC is just a control surface for language. Nimbus is already a control surface."*

---

## What Is AAC?

**Augmentative and Alternative Communication** refers to all methods of communication used by people who cannot rely on spoken speech — or for whom speech is unreliable, effortful, or unavailable. This includes:

- **Low-tech:** Picture boards, letter boards, PECS (Picture Exchange Communication System)
- **Mid-tech:** Recorded-message devices (BigMack, Step-by-Step)
- **High-tech:** Speech-generating devices (SGDs) like Tobii Dynavox, PRC-Saltillo, Snap Core First, TouchChat, Proloquo2Go

AAC users include people with:
- ALS / MND (progressive motor neuron disease)
- Cerebral palsy
- Autism (non-speaking or minimally speaking)
- Acquired brain injury / stroke
- Rett syndrome
- Down syndrome
- Parkinson's disease

**Scale:** An estimated 1.3–2 million people in the US use AAC. Globally, tens of millions. The AAC device market is ~$400M/yr and growing.

---

## The Gap Nimbus Could Fill

### The Problem with Existing AAC Software

Commercial AAC apps (Proloquo2Go, TouchChat, Snap Core First) are:
- **Expensive:** $200–$400 for the app alone; dedicated SGD hardware costs $5,000–$15,000
- **Closed:** Not customizable beyond their built-in vocabulary systems
- **Gaming-incompatible:** Cannot be used while gaming; separate device required
- **Not designed for power users:** Advanced users (e.g., ALS patients who are tech-savvy) hit ceilings quickly

### What Nimbus Could Offer

| Capability | Current Nimbus | AAC Extension |
|-----------|---------------|---------------|
| Custom button layout | ✅ | ✅ Map buttons to phrases/words |
| Touch input | ✅ | ✅ Touch to speak |
| Switch access | ✅ (via vJoy) | ✅ Single/dual switch scanning |
| Eye gaze | ❌ (not yet) | 🎯 High-value AAC input method |
| Voice input | 🔄 (Pro tier) | ✅ Voice-to-confirm, not voice-to-speak |
| Macros | 🔄 (Pro tier) | ✅ Phrase macros — one button = full sentence |
| Profile system | ✅ | ✅ Context profiles (home, medical, gaming) |
| vJoy/ViGEm output | ✅ | ➕ Add TTS output alongside controller output |

---

## Two Integration Approaches

### Approach A: Nimbus as AAC Input Controller (Simpler)

Nimbus acts as the **input layer** for an existing AAC app. The user configures Nimbus buttons to send keystrokes or mouse clicks that trigger actions in their AAC software (e.g., Snap Core First, Grid 3, Tobii Dynavox).

```
User touches Nimbus button
    ↓
Nimbus sends keystroke (e.g., F1, Ctrl+1) via vJoy/keyboard emulation
    ↓
AAC app receives keystroke → speaks phrase
```

**What this requires:**
- Keyboard output mode (already partially possible via ViGEm + key mapping)
- No changes to AAC apps needed — they already accept keyboard shortcuts
- Profile per AAC app / communication context

**Who this helps immediately:** AAC users who already have software but struggle with the physical interface. Nimbus becomes a custom access method for their existing AAC system.

### Approach B: Nimbus as a Lightweight AAC Surface (More Ambitious)

Nimbus gains a **TTS (text-to-speech) output mode** alongside its controller output. Buttons can be mapped to:
- Spoken phrases (via Windows SAPI or a cloud TTS engine)
- Dynamic vocabulary pages (like AAC "pages" — tap a category, then a word)
- Predictive phrase completion

```
User touches "I need" button
    ↓
Nimbus speaks "I need" via TTS
    ↓
Page transitions to follow-up options: "water", "help", "a break", "to go home"
    ↓
User touches "water"
    ↓
Nimbus speaks "I need water"
```

**What this requires:**
- TTS output module (`pyttsx3` or Windows SAPI — both free, offline)
- Page navigation system (already partially analogous to profile switching)
- Vocabulary storage (JSON, same pattern as existing profiles)
- No internet required — fully offline capable

**Who this helps:** Users who can't afford commercial AAC software, users who want a gaming + AAC hybrid device, users who want more customization than commercial apps allow.

---

## The Gaming + AAC Hybrid Use Case

This is the uniquely compelling angle. Many AAC users are also gamers — or want to be. Current AAC devices and gaming setups are **completely separate**, requiring the user to switch between devices. Nimbus could be both simultaneously:

```
Profile: "Gaming — Halo"
  Left half of screen: joystick + buttons → vJoy game input
  Right half of screen: AAC quick phrases → TTS output
  ("Good game", "Nice shot", "BRB", "GG")
```

This is something no commercial AAC device or gaming controller currently does. It's a genuine gap in the market and a powerful story for funders.

---

## Switch Access

Switch access is a critical AAC input method — many users have only 1–2 reliable physical movements (a head switch, a sip-and-puff, a foot pedal). Nimbus already routes through vJoy, which can accept switch inputs. The extension needed:

- **Scanning mode** — Nimbus highlights buttons in sequence; user activates their switch to select
- **Single-switch scanning** — one switch steps through options; dwelling or second press selects
- **Two-switch scanning** — one switch moves, one selects
- **Auto-scan** — timed automatic progression through options

This is standard AAC functionality and would make Nimbus compatible with the broadest range of physical abilities.

---

## Eye Gaze

Eye gaze is the highest-value input method for users with very limited motor function (late-stage ALS, locked-in syndrome, high-level SCI). Tobii and Irisbond make eye tracking hardware that exposes APIs.

- **Tobii SDK** — Windows, free for developers
- **Irisbond** — open API
- **Windows Eye Control** — built into Windows 10/11, outputs as mouse movement

Since Nimbus already works with touch/mouse input, **Windows Eye Control already works with Nimbus today** — the user's gaze moves the mouse cursor, and Nimbus buttons are just large touch targets. No code changes needed for basic eye gaze support.

A dedicated eye gaze mode would add:
- Dwell-to-activate (hover for N ms = press)
- Larger hit targets optimized for gaze accuracy
- Gaze-aware UI that highlights where the user is looking

---

## Relevant Organizations and Partners

| Organization | Type | Relevance |
|-------------|------|-----------|
| **ASHA (American Speech-Language-Hearing Association)** | Professional org | SLPs prescribe AAC; key adoption channel |
| **ISAAC (International Society for AAC)** | Academic/professional | Research, conferences, credibility |
| **Tobii Dynavox** | AAC manufacturer | Potential integration partner |
| **PRC-Saltillo** | AAC manufacturer | Potential integration partner |
| **Communication Matters** (UK) | Nonprofit | SpecialEffect connection |
| **Aphasia Access** | Nonprofit | Stroke/acquired brain injury AAC |
| **Autism Society of America** | Nonprofit | Large AAC user population |
| **ALS Association** | Nonprofit | Urgent AAC need; tech-forward community |

---

## Funding Angle

AAC opens entirely different funding streams than gaming:

- **Medicaid/Medicare** — AAC devices are covered as durable medical equipment; software may qualify
- **RERC on AAC** (Rehabilitation Engineering Research Center) — federally funded AAC research
- **NIH NICHD** — communication disorders research
- **Patient advocacy foundations** — ALS Association, MDA, United Cerebral Palsy
- **USDA Distance Learning and Telemedicine** — rural AAC access

The AAC framing also strengthens the case for **501(c)(3) nonprofit status** — a free AAC tool for people who can't afford $300 apps is a clear charitable mission.

---

## Minimum Viable AAC Feature Set

To be genuinely useful for AAC without over-engineering:

1. **Phrase buttons** — any button can be mapped to a spoken phrase (TTS)
2. **Page navigation** — buttons can link to other "pages" of buttons (vocabulary depth)
3. **Offline TTS** — `pyttsx3` wrapping Windows SAPI; no internet required
4. **Large-target mode** — UI option for fewer, larger buttons optimized for low-precision input
5. **Scanning mode** — single-switch auto-scan through buttons

This is achievable without restructuring the existing architecture. The profile system already handles button layout; TTS output is additive.

---

## Next Steps

1. **Prototype phrase button** — Add TTS output option to any button in the custom layout builder
2. **Test with Windows Eye Control** — Verify current Nimbus works as an eye gaze target today
3. **Talk to an SLP** — Speech-language pathologists are the gatekeepers for AAC adoption; get one involved early
4. **Research ASHA conference** — Presenting at ASHA would reach thousands of SLPs
5. **Draft AAC-specific profile template** — A starter layout for AAC use cases

---

## Related Documents

- [Modular Control Surface](MODULAR_CONTROL_SURFACE.md) — AAC is one instance of the broader "control surface for any application" vision
- [Research Platform](RESEARCH_PLATFORM.md) — AAC use generates its own research data
- [Voice Command Integration](../distribution/VOICE_COMMAND.md) — voice input complements AAC output
- [Release Strategy](../distribution/RELEASE_STRATEGY.md) — AAC opens new funding streams
