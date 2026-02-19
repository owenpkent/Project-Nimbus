# Spectator+ — AI-Assisted Play (Concept Overview)

> **Note:** A detailed technical proposal for the full AI game player system already exists at  
> [`research/ai-game-player/proposal.md`](../../research/ai-game-player/proposal.md)  
> That document covers the full RL architecture, hardware costs, training pipeline, software stack, and development phases. This document focuses specifically on the **Spectator+ user experience concept**, its accessibility framing, and the practical questions around hardware and integration with the current Nimbus architecture.

---

## What Is Spectator+?

Spectator+ is the **accessibility-first face** of the AI game player system. Rather than framing it as "AI that plays games for you," Spectator+ frames it as:

> *"You direct. The AI executes."*

The user remains the player — they provide **intent** (strategic direction, high-level goals, moment-to-moment decisions). The AI handles **execution** (precise joystick movements, timing, reflexes). This is meaningful for users who:

- Have the cognitive engagement to play but not the fine motor precision
- Experience fatigue that makes sustained precise input impossible
- Use switch access, eye gaze, or voice as their primary input — fast enough for direction, not for twitch gameplay
- Want to participate in games that were previously inaccessible

This is already described in the proposal as **"Copilot Mode"** (Section 11), with a full assistance spectrum from 0% AI to 100% AI. Spectator+ is the high end of that spectrum — the user is directing, not executing.

---

## The Interaction Model

```
User speaks or clicks:  "Go forward"  /  "Attack the enemy on the left"  /  "Retreat"
                                    ↓
              Spectator+ interprets intent in context of current game state
                                    ↓
              AI generates joystick/button sequence via Project Nimbus → vJoy/ViGEm
                                    ↓
                              Game responds
```

The user's input channel can be **anything Nimbus already supports** — or voice (see [VOICE_COMMAND.md](VOICE_COMMAND.md)):
- Mouse click on a command palette
- Voice command ("attack", "dodge left", "go to objective")
- Switch/button press mapped to a command
- Eye gaze dwell on a command

---

## How It Differs from Full Automation

| | Full Auto (Bot) | Spectator+ | Manual Play |
|---|---|---|---|
| **Who decides strategy** | AI | User | User |
| **Who executes inputs** | AI | AI | User |
| **User engagement** | Passive | Active (directing) | Active (executing) |
| **Accessibility value** | Low (user excluded) | High (user included) | Depends on ability |
| **ToS risk** | High (multiplayer) | Medium | None |

The key distinction: the user is **present and directing** at all times. This is closer to a game accessibility feature than a bot.

---

## Hardware Requirements

The existing proposal (`research/ai-game-player/proposal.md`, Section 4) covers full training hardware. For **Spectator+ inference only** (running a pre-trained model in real time), requirements are significantly lower:

### Inference-Only Hardware (Running Spectator+)

| Tier | GPU | RAM | What It Enables |
|------|-----|-----|-----------------|
| **Minimum** | None (CPU only) | 8GB | VLM-based command mapping, ~500ms response |
| **Recommended** | GTX 1060 / RX 580 (6GB VRAM) | 16GB | Faster-Whisper + lightweight vision model, ~150–200ms |
| **Optimal** | RTX 3060 (12GB VRAM) | 16GB | Full vision model + voice, ~80–120ms |
| **Best** | RTX 4070+ (12GB+ VRAM) | 32GB | Large VLM, real-time screen understanding, ~50ms |

### Why These Numbers

The two compute-heavy components are:

1. **Screen understanding** — Reading the game state to contextualize the user's command
   - Lightweight: CLIP-based scene classifier (~50ms on CPU, ~10ms on GPU)
   - Full: Vision-Language Model like LLaVA or Moondream (~200–800ms on CPU, ~50–150ms on GPU)

2. **Voice recognition** (if used) — See [VOICE_COMMAND.md](VOICE_COMMAND.md) for full breakdown
   - Faster-Whisper tiny: ~80–150ms on CPU
   - DeepGram cloud: ~100–300ms (internet required)

The **action execution** itself (writing to vJoy/ViGEm via the existing Nimbus bridge) adds < 2ms — that part is already solved.

### Training Hardware (If Training Your Own Model)

See `research/ai-game-player/proposal.md` Section 4 for full cost breakdown. Summary:

| Scenario | Hardware | Cost |
|----------|----------|------|
| MVP (cloud training) | RTX 3060 local + Vast.ai | ~$350–480 |
| Recommended | RTX 3080/4070 | ~$750 |
| Production | RTX 4090 | ~$2,200 |

For Spectator+ specifically, **pre-trained models can be used** (no training required for the first version), which eliminates training hardware costs entirely.

---

## Two Implementation Approaches

### Approach A: Command Palette + Pre-trained RL Agent (Faster to Ship)

Use a pre-trained game-specific agent (e.g., from OpenAI Gym, or trained via the pipeline in the proposal) and expose a **command palette** in the Nimbus UI. The user clicks/speaks a command; the agent executes it.

- No screen understanding required
- Commands are game-specific and pre-mapped
- Lower latency (no vision inference)
- Requires a trained model per game

### Approach B: Vision-Language Model + Natural Language Commands (More Flexible)

Use a VLM (e.g., Moondream, LLaVA, or GPT-4o Vision via API) to understand the current game screen, then map the user's natural language command to a specific action sequence.

- Game-agnostic (works with any game)
- Understands context ("the enemy on the left" requires knowing where enemies are)
- Higher latency (~200–800ms depending on model and hardware)
- No per-game training needed

**Recommended path:** Start with Approach A for a specific game (e.g., "I Am Your Beast" as outlined in the proposal), then layer in Approach B for context-awareness.

---

## Integration with Current Nimbus Architecture

The existing architecture is well-positioned for this. The key integration points:

### What Already Exists

- **`src/bridge.py` (`ControllerBridge`)** — All vJoy/ViGEm axis and button writes are already centralized here. The AI agent just calls the same `@Slot` methods the QML UI calls.
- **`src/vjoy_interface.py`** — 8-axis, 128-button vJoy output already working
- **`src/vigem_interface.py`** — Xbox 360 emulation for XInput games
- **Profile system** — Per-game axis mappings already stored in JSON profiles

### What Needs to Be Added

```
src/
├── spectator/
│   ├── agent_interface.py      # Abstract base: act(game_state) → actions
│   ├── command_palette.py      # Maps user commands → agent goals
│   ├── screen_capture.py       # mss/dxcam frame capture
│   └── vision_encoder.py       # Optional: game state from pixels
```

The agent calls `bridge.setAxis()` and `bridge.pressButton()` — the same methods QML calls. No changes to the core pipeline.

### QML UI Changes

- **Spectator+ panel** — Command palette overlay (voice or click)
- **Assistance slider** — 0–100% AI control blend (from proposal Section 11)
- **Status indicator** — "AI Active", "Listening", "Executing"

---

## Accessibility Framing for Funders and Partners

This is the angle that resonates with AbleGamers, Microsoft Inclusive Tech Lab, Shirley Ryan AbilityLab, and similar organizations:

> *"Spectator+ is not a cheat tool. It's a ramp. Just as a wheelchair ramp doesn't give non-disabled people an unfair advantage — it gives disabled people equal access — Spectator+ gives players with motor disabilities access to games that require physical precision they cannot provide."*

Key points for grant applications and sponsor pitches:
- **Single-player only** (no competitive fairness concerns)
- **User remains the decision-maker** (not passive)
- **Graduated assistance** (user controls how much help they get)
- **Builds on existing research** (GT Sophy, OpenAI Five, Microsoft Gaming AI Accessibility)
- **Open source** (benefits the whole community)

See [`RELEASE_STRATEGY.md`](RELEASE_STRATEGY.md) and [`SPONSORSHIP_OUTREACH.md`](SPONSORSHIP_OUTREACH.md) for the full funding strategy.

---

## Next Steps

1. **Read the full proposal** — `research/ai-game-player/proposal.md` has the complete technical plan
2. **Decide on target game** — "I Am Your Beast" is already identified as ideal (single-player, no anti-cheat)
3. **Choose approach** — Command palette (faster) vs. VLM (more flexible)
4. **Prototype screen capture** — `mss` or `dxcam` integration with the existing bridge
5. **Voice integration** — See [VOICE_COMMAND.md](VOICE_COMMAND.md) for the command input layer

---

## Related Documents

| Document | Location |
|----------|----------|
| Full AI game player proposal | `research/ai-game-player/proposal.md` |
| Voice command integration | `docs/distribution/VOICE_COMMAND.md` |
| Release & funding strategy | `docs/distribution/RELEASE_STRATEGY.md` |
| Sponsorship outreach templates | `docs/distribution/SPONSORSHIP_OUTREACH.md` |
