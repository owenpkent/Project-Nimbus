# Research & Technical Documentation

This folder contains research, design decisions, and roadmap documentation for Project Nimbus.

Project Nimbus is a virtual controller application that allows users to control games via mouse input (with potential future touchscreen support).

## Quick Links by Status

### ✅ Completed

| Document | Description |
|----------|-------------|
| [Game Focus Mode](completed/game-focus-mode.md) | Focus restoration solution for gaming - **IMPLEMENTED** |
| [UI Automation Security Overview](completed/ui-automation-security-overview.md) | Summary of Windows UI Automation security model, `uiAccess`, and related resources |

### 🔴 In Progress / Open Problems

| Document | Description |
|----------|-------------|
| [Mouse Capture Problem](in-progress/mouse-capture-problem.md) | Games that capture the mouse prevent access to Nimbus UI |

### 🗺️ Future Roadmap

| Document | Description |
|----------|-------------|
| [uiAccess & Signing Strategy](roadmap/uiaccess-signing-strategy.md) | Comprehensive plan for Windows uiAccess, code signing, and releases |
| [uiAccess Implementation Checklist](roadmap/uiaccess-signing-checklist.md) | Phased TODO list for uiAccess implementation |
| [AI Game Player Proposal](ai-game-player/proposal.md) | Full RL architecture, hardware costs, training pipeline, Copilot/Spectator+ mode |

### 🔗 Related: Distribution & Feature Concepts

| Document | Description |
|----------|-------------|
| [Spectator+ Concept](../docs/distribution/SPECTATOR_PLUS.md) | Accessibility-first framing of the AI game player; integration with current Nimbus architecture |
| [Voice Command Integration](../docs/distribution/VOICE_COMMAND.md) | Speech recognition engine comparison, DeepGram/Whisper/Vosk analysis, GitConnect foundation |

---

## For New Contributors

**Start here:**

1. **Understand the core problem**: Project Nimbus is a touchscreen virtual controller. When users touch the UI, the game loses focus and may pause or ignore input.

2. **What's solved**: Game Focus Mode automatically restores focus to the game after each interaction. See [completed/game-focus-mode.md](completed/game-focus-mode.md).

3. **What's not solved**: Games that capture/lock the mouse cursor prevent users from clicking Nimbus at all. This is the main accessibility barrier. See [in-progress/mouse-capture-problem.md](in-progress/mouse-capture-problem.md).

4. **Future direction**: For proper assistive technology behavior, Nimbus needs uiAccess privileges and code signing. See [roadmap/](roadmap/).

---

## Current Setup Context

```
┌─────────────────┐    Bluetooth    ┌─────────────────┐    Synergy    ┌─────────────────┐
│   Wheelchair    │ ─────────────── │     Laptop      │ ────────────► │   Gaming PC     │
│   Controller    │   (1 device     │  (mouse input)  │   (KVM over   │  (runs games)   │
│                 │    limit)       │                 │    network)   │                 │
└─────────────────┘                 └─────────────────┘               └─────────────────┘
```

- Wheelchair Bluetooth connects to laptop only (hardware limitation)
- Laptop runs Project Nimbus, controlled via mouse (touchscreen support planned)
- Gaming PC runs actual games
- Synergy bridges keyboard/mouse from laptop to gaming PC
