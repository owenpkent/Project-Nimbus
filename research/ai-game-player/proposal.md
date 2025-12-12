# Project Nimbus AI Game Player Expansion Proposal

**Date:** December 12, 2024  
**Version:** 1.0  
**Author:** Project Nimbus Team

---

## Executive Summary

This proposal outlines the expansion of Project Nimbus from a virtual controller interface into an **AI-powered game-playing platform**. The system would leverage neural networks and reinforcement learning to autonomously play video games, with human feedback (via gameplay video uploads) to guide learning. The end goal: **AI that plays games for you**.

---

## 1. Vision & Concept

### Current State
Project Nimbus is a virtual controller that translates mouse/keyboard input into gamepad signals via vJoy. It already has:
- Joystick/slider input processing with sensitivity curves
- Button state management (toggle/momentary modes)
- Profile system for different game configurations
- Real-time input processing pipeline

### Proposed Expansion
Transform Nimbus into an AI training and execution platform that:
1. **Observes** game state via screen capture
2. **Learns** from human gameplay videos (imitation learning / RLHF)
3. **Decides** actions using trained neural networks
4. **Executes** actions through the existing vJoy pipeline
5. **Improves** via reinforcement learning with human feedback

---

## 2. Technical Architecture

### 2.1 Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROJECT NIMBUS AI                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   VISION     │───▶│   DECISION   │───▶│   ACTION     │      │
│  │   MODULE     │    │   ENGINE     │    │   EXECUTOR   │      │
│  │              │    │              │    │              │      │
│  │ Screen Cap   │    │ Neural Net   │    │ vJoy Output  │      │
│  │ Frame Proc   │    │ Policy Net   │    │ Controller   │      │
│  │ State Detect │    │ Value Net    │    │ Timing       │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ▲                   ▲                                   │
│         │                   │                                   │
│  ┌──────┴───────────────────┴──────┐                           │
│  │        TRAINING PIPELINE         │                           │
│  │                                  │                           │
│  │  • Video Upload & Processing     │                           │
│  │  • Human Feedback Interface      │                           │
│  │  • Reward Modeling               │                           │
│  │  • Policy Optimization           │                           │
│  └──────────────────────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Vision Module

| Component | Technology | Purpose |
|-----------|------------|---------|
| Screen Capture | mss, dxcam, or OBS virtual cam | 60+ FPS game capture |
| Frame Processing | OpenCV, Pillow | Resize, normalize, preprocess |
| State Detection | CNN encoder | Extract game state features |
| OCR (optional) | Tesseract, EasyOCR | Read health, ammo, scores |

### 2.3 Decision Engine (Neural Network)

**Architecture Options:**

1. **CNN + LSTM** (Simple, proven)
   - CNN extracts spatial features from frames
   - LSTM handles temporal sequences
   - ~5-20M parameters
   - Good for: Turn-based, slower-paced games

2. **Vision Transformer (ViT)** (Modern, powerful)
   - Self-attention over image patches
   - Better long-range dependencies
   - ~50-100M parameters
   - Good for: Complex scenes, strategy games

3. **Impala/R2D2 Style** (RL optimized)
   - Distributed actor-learner architecture
   - Handles partial observability
   - ~10-50M parameters
   - Good for: Fast-paced action games like "I Am Your Beast"

**Recommended for v1:** CNN encoder + MLP policy head (~10M params)

### 2.4 Learning Approaches

#### A. Imitation Learning (Behavioral Cloning)
- Upload gameplay videos
- Extract (frame, action) pairs
- Train network to mimic human actions
- **Pros:** Fast to train, leverages human expertise
- **Cons:** Can't exceed human performance, distribution shift

#### B. RLHF (Reinforcement Learning from Human Feedback)
- Human rates AI gameplay clips (good/bad)
- Train reward model from preferences
- Optimize policy against reward model
- **Pros:** Can exceed human performance, handles edge cases
- **Cons:** Requires ongoing human feedback, more complex

#### C. Hybrid Approach (Recommended)
1. **Phase 1:** Behavioral cloning from uploaded videos (bootstrap)
2. **Phase 2:** Self-play with RLHF refinement
3. **Phase 3:** Pure RL with learned reward model

---

## 3. Implementation for "I Am Your Beast"

### Game-Specific Considerations
"I Am Your Beast" is a fast-paced FPS with:
- Quick reflexes required
- Environmental awareness
- Enemy tracking
- Resource management

### Proposed Pipeline

```python
# Simplified architecture pseudocode
class NimbusAI:
    def __init__(self):
        self.vision = VisionEncoder()      # CNN -> 512-dim features
        self.memory = LSTM(512, 256)        # Temporal context
        self.policy = PolicyHead(256, 18)   # 18 action dims
        
    def act(self, frame):
        features = self.vision(frame)
        context = self.memory(features)
        actions = self.policy(context)
        return actions  # [look_x, look_y, move_x, move_y, jump, shoot, ...]
```

### Action Space
| Action | Type | Range |
|--------|------|-------|
| Look X | Continuous | -1.0 to 1.0 |
| Look Y | Continuous | -1.0 to 1.0 |
| Move X | Continuous | -1.0 to 1.0 |
| Move Y | Continuous | -1.0 to 1.0 |
| Jump | Binary | 0 or 1 |
| Shoot | Binary | 0 or 1 |
| Reload | Binary | 0 or 1 |
| Interact | Binary | 0 or 1 |

---

## 4. Resource Requirements

### 4.1 Hardware Requirements

#### Local Training (Minimum)
| Component | Specification | Est. Cost |
|-----------|--------------|-----------|
| GPU | RTX 3080 (10GB VRAM) | $500-700 |
| RAM | 32GB DDR4 | $80-120 |
| Storage | 1TB NVMe SSD | $80-100 |
| CPU | Ryzen 7 / i7 (8+ cores) | Already owned |
| **Total** | | **$660-920** |

#### Local Training (Recommended)
| Component | Specification | Est. Cost |
|-----------|--------------|-----------|
| GPU | RTX 4090 (24GB VRAM) | $1,600-2,000 |
| RAM | 64GB DDR5 | $150-200 |
| Storage | 2TB NVMe SSD | $150-180 |
| CPU | Ryzen 9 / i9 (12+ cores) | $400-500 |
| **Total** | | **$2,300-2,880** |

#### Local Inference Only
| Component | Specification | Est. Cost |
|-----------|--------------|-----------|
| GPU | RTX 3060 (12GB VRAM) | $250-350 |
| RAM | 16GB | Already owned |
| **Total** | | **$250-350** |

### 4.2 Cloud Training Costs

#### Option A: Consumer Cloud (Vast.ai, RunPod)
| GPU | Hourly Rate | 100 hrs Training |
|-----|-------------|------------------|
| RTX 3090 | $0.20-0.40/hr | $20-40 |
| RTX 4090 | $0.40-0.80/hr | $40-80 |
| A100 40GB | $1.00-1.50/hr | $100-150 |

#### Option B: Enterprise Cloud (AWS, GCP, Azure)
| Instance | Hourly Rate | 100 hrs Training |
|----------|-------------|------------------|
| AWS p3.2xlarge (V100) | $3.06/hr | $306 |
| AWS p4d.24xlarge (A100x8) | $32.77/hr | $3,277 |
| GCP a2-highgpu-1g (A100) | $3.67/hr | $367 |

#### Option C: Specialized ML Platforms
| Platform | Pricing | Notes |
|----------|---------|-------|
| Lambda Labs | $1.10/hr (A100) | Good availability |
| Paperspace | $2.30/hr (A100) | Easy setup |
| Google Colab Pro+ | $50/month | Limited GPU hours |

### 4.3 Storage Requirements

| Data Type | Size Estimate |
|-----------|---------------|
| 1 hour gameplay video (1080p) | ~5-10 GB |
| Extracted frames (10 FPS, compressed) | ~500 MB |
| Trained model checkpoint | ~100-500 MB |
| Training dataset (10 hrs gameplay) | ~5-10 GB |
| Experience replay buffer | ~10-50 GB |

---

## 5. Cost Scenarios

### Scenario A: Budget Local Setup
**Goal:** Train and run basic models locally

| Item | Cost |
|------|------|
| RTX 3080 (used) | $500 |
| RAM upgrade to 32GB | $100 |
| SSD storage | $80 |
| Electricity (100 hrs @ $0.12/kWh) | ~$50 |
| **Total** | **~$730** |

**Pros:** One-time cost, full control, privacy  
**Cons:** Slower training, limited model size

### Scenario B: Hybrid (Local Inference + Cloud Training)
**Goal:** Train in cloud, deploy locally

| Item | Cost |
|------|------|
| RTX 3060 for inference | $300 |
| Vast.ai training (200 hrs RTX 4090) | $160 |
| Storage (cloud) | $20 |
| **Total Initial** | **~$480** |
| **Ongoing** | **~$50-100/month** |

**Pros:** Best of both worlds, fast training  
**Cons:** Ongoing costs, data upload time

### Scenario C: Full Cloud
**Goal:** Everything in cloud

| Item | Monthly Cost |
|------|--------------|
| Cloud GPU instance | $100-300 |
| Storage | $20-50 |
| Bandwidth | $10-30 |
| **Total** | **~$130-380/month** |

**Pros:** No hardware investment, scalable  
**Cons:** Recurring costs, latency for real-time play

### Scenario D: Serious ML Setup
**Goal:** Production-quality training

| Item | Cost |
|------|------|
| RTX 4090 | $1,800 |
| 64GB RAM | $180 |
| 2TB NVMe | $160 |
| UPS backup | $150 |
| **Total** | **~$2,290** |

**Pros:** Fast iteration, large models, long-term value  
**Cons:** High upfront cost

---

## 6. Local vs Cloud Decision Matrix

| Factor | Local | Cloud | Winner |
|--------|-------|-------|--------|
| **Upfront Cost** | $500-2,500 | $0 | Cloud |
| **Ongoing Cost** | Electricity only | $100-400/mo | Local |
| **Training Speed** | Moderate | Fast (scalable) | Cloud |
| **Inference Latency** | <5ms | 50-200ms | Local |
| **Privacy** | Full control | Data on servers | Local |
| **Flexibility** | Fixed hardware | Any GPU | Cloud |
| **Real-time Gaming** | ✅ Excellent | ⚠️ Latency issues | Local |
| **Long-term (1 year)** | $500-2,500 | $1,200-4,800 | Local |

### Recommendation
**Hybrid approach:** Train in cloud (Vast.ai/RunPod for cost efficiency), deploy locally on modest GPU for real-time gameplay.

---

## 7. Software Stack

### Core Dependencies
```
# ML Framework
torch>=2.0
torchvision
stable-baselines3        # RL algorithms
gymnasium                # Environment interface

# Vision
opencv-python
mss                      # Fast screen capture
pillow

# Video Processing
ffmpeg-python
av                       # PyAV for video decoding

# Existing Nimbus
pyvjoy                   # Controller output
PyQt6                    # GUI

# Training
wandb                    # Experiment tracking
tensorboard
accelerate               # Multi-GPU training
```

### Optional Enhancements
```
# For advanced models
transformers             # Vision transformers
timm                     # Image model zoo

# For RLHF
trl                      # Transformer RL
human-feedback           # Preference learning

# For OCR
easyocr
pytesseract
```

---

## 8. Development Phases

### Phase 1: Foundation (2-4 weeks)
- [ ] Screen capture integration
- [ ] Frame preprocessing pipeline
- [ ] Basic CNN encoder
- [ ] Action space definition
- [ ] vJoy output integration
- **Deliverable:** AI that outputs random but valid actions

### Phase 2: Imitation Learning (4-6 weeks)
- [ ] Video upload interface
- [ ] Gameplay annotation tool
- [ ] Frame-action pair extraction
- [ ] Behavioral cloning training
- [ ] Basic gameplay capability
- **Deliverable:** AI that mimics uploaded gameplay

### Phase 3: Reinforcement Learning (6-8 weeks)
- [ ] Reward detection (score, health, deaths)
- [ ] PPO/SAC implementation
- [ ] Self-play training loop
- [ ] Performance benchmarking
- **Deliverable:** AI that improves beyond demonstrations

### Phase 4: RLHF Integration (4-6 weeks)
- [ ] Human feedback interface
- [ ] Preference dataset collection
- [ ] Reward model training
- [ ] RLHF fine-tuning
- **Deliverable:** AI that learns from human preferences

### Phase 5: Polish & Optimization (2-4 weeks)
- [ ] Inference optimization
- [ ] Multi-game profiles
- [ ] User-friendly training UI
- [ ] Documentation
- **Deliverable:** Production-ready system

**Total Timeline:** 4-6 months

---

## 9. Challenges & Mitigations

| Challenge | Risk | Mitigation |
|-----------|------|------------|
| **Game anti-cheat** | High | Use games without anti-cheat, or single-player only |
| **Input latency** | Medium | Optimize pipeline, predict ahead |
| **Visual variation** | Medium | Data augmentation, robust encoders |
| **Reward sparsity** | High | Dense reward shaping, curiosity-driven exploration |
| **Overfitting to demos** | Medium | Regularization, diverse training data |
| **Real-time inference** | Low | Model quantization, TensorRT |

---

## 10. Legal & Ethical Considerations

### Terms of Service
- Many games prohibit automation in multiplayer
- Single-player and offline games are generally safe
- Some games explicitly allow mods/automation

### Recommendations
1. **Target single-player games** initially
2. **Avoid competitive multiplayer** entirely
3. **Check each game's ToS** before deployment
4. **Consider this a research/educational project**

### "I Am Your Beast" Suitability
✅ Single-player FPS  
✅ No anti-cheat  
✅ Offline capable  
✅ Ideal candidate for AI training

---

## 11. Accessibility & AI Copilot Mode

### The Opportunity

Beyond autonomous gameplay, this system has significant **accessibility implications**. An AI copilot could help gamers with disabilities enjoy games that would otherwise be difficult or impossible to play.

> *"AI has the potential to advance accessibility in video games in ways that traditional methods and technology cannot."*  
> — Microsoft Gaming Accessibility Guidelines

### Research Foundation

**Microsoft's Gaming AI Accessibility Research** identifies key opportunities:
- **Personalization:** AI adapts to individual abilities and preferences
- **Predictive assistance:** AI anticipates player intent from partial inputs
- **Real-time support:** AI provides guidance when players get stuck
- **Input augmentation:** AI fills gaps in player control capabilities

**GT Sophy's "Race Together" Mode** demonstrates this in practice — players can race alongside AI that matches their skill level, creating an inclusive experience for all abilities.

### Copilot Mode Concept

Instead of fully autonomous play, offer **graduated assistance levels**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI ASSISTANCE SPECTRUM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FULL MANUAL ◄─────────────────────────────────► FULL AUTO     │
│       │                    │                         │          │
│       ▼                    ▼                         ▼          │
│  ┌─────────┐        ┌───────────┐           ┌────────────┐     │
│  │ Player  │        │  Copilot  │           │    Auto    │     │
│  │ Control │        │   Mode    │           │   Player   │     │
│  │         │        │           │           │            │     │
│  │ 0% AI   │        │ 10-90% AI │           │  100% AI   │     │
│  └─────────┘        └───────────┘           └────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Copilot Assistance Modes

| Mode | AI Role | Player Role | Use Case |
|------|---------|-------------|----------|
| **Aim Assist** | Smooths/corrects aiming | Movement + shooting | Motor disabilities, tremors |
| **Navigation** | Handles movement | Combat + decisions | Cognitive load reduction |
| **Reflex Boost** | Handles time-critical actions | Strategy + exploration | Slower reaction times |
| **Full Copilot** | Handles difficult sections | Easy sections + story | Varying ability levels |
| **Spectator+** | Plays game | Provides high-level direction | Severe motor disabilities |

### Accessibility-Specific Features

#### 1. Adaptive Difficulty via AI
```python
class AdaptiveCopilot:
    def __init__(self):
        self.assistance_level = 0.5  # 0 = manual, 1 = full auto
        self.player_performance = PerformanceTracker()
    
    def adjust_assistance(self):
        # Increase help if player struggling
        if self.player_performance.deaths_per_minute > threshold:
            self.assistance_level = min(1.0, self.assistance_level + 0.1)
        # Decrease if player succeeding
        elif self.player_performance.success_rate > 0.8:
            self.assistance_level = max(0.0, self.assistance_level - 0.05)
    
    def blend_actions(self, player_input, ai_suggestion):
        # Weighted blend of player and AI actions
        return (1 - self.assistance_level) * player_input + \
               self.assistance_level * ai_suggestion
```

#### 2. Input Augmentation
- **Tremor filtering:** AI smooths erratic inputs
- **Timing assistance:** AI helps with precise timing windows
- **Combo completion:** Player initiates, AI completes complex sequences
- **Predictive input:** AI anticipates intent from partial gestures

#### 3. Cognitive Assistance
- **Objective highlighting:** AI identifies current goals
- **Path suggestions:** Visual overlay showing recommended routes
- **Threat warnings:** Audio/visual cues for dangers
- **Decision support:** AI suggests options during complex choices

### Implementation for Accessibility

#### Phase A: Basic Copilot (Add to Phase 2)
- [ ] Blended control system (player + AI weighted)
- [ ] Adjustable assistance slider (0-100%)
- [ ] Per-action-type assistance toggles

#### Phase B: Adaptive System (Add to Phase 3)
- [ ] Performance monitoring
- [ ] Automatic difficulty adjustment
- [ ] Player fatigue detection

#### Phase C: Full Accessibility Suite (Add to Phase 4)
- [ ] Input augmentation filters
- [ ] Cognitive assistance overlays
- [ ] Voice control integration
- [ ] Switch/adaptive controller support

### Target User Groups

| Group | Challenge | AI Solution |
|-------|-----------|-------------|
| **Motor disabilities** | Precise/fast inputs | Aim assist, timing help |
| **Cognitive disabilities** | Complex decisions | Navigation, objectives |
| **Visual impairments** | Screen reading | Audio cues, AI guidance |
| **Fatigue conditions** | Sustained play | Take-over during difficult sections |
| **Age-related decline** | Reaction time | Reflex boost mode |
| **Casual players** | Skill gap | Adaptive difficulty |

### Ethical Considerations

1. **Player agency:** Always give players control over assistance level
2. **Transparency:** Clearly indicate when AI is helping
3. **Achievement integrity:** Consider separate leaderboards/achievements
4. **No gatekeeping:** Don't require AI to progress (optional only)
5. **Privacy:** Process locally when possible, don't share disability data

### Research Directions

This accessibility angle opens several research opportunities:

1. **Personalized AI profiles** — Train AI to match individual player styles
2. **Minimal intervention** — AI that helps only when truly needed
3. **Skill transfer** — Can AI assistance help players improve over time?
4. **Cross-game adaptation** — Transfer accessibility settings between games
5. **Community models** — Share trained copilot models for specific games

### References

- Microsoft Gaming Accessibility Guidelines: [Accessibility of Gaming AI](https://learn.microsoft.com/en-us/gaming/accessibility/accessibility-of-gaming-ai)
- Xbox Adaptive Controller ecosystem
- AbleGamers Foundation research
- SpecialEffect charity work
- GT Sophy "Race Together" deployment

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| Frame processing latency | <16ms (60 FPS) |
| Action inference latency | <10ms |
| Training convergence | <100 hours GPU time |
| Human-level performance | Within 50 hours training |
| Superhuman performance | Within 200 hours training |

---

## 12. Budget Summary

### Minimum Viable Product
| Category | Cost |
|----------|------|
| Hardware (RTX 3060) | $300 |
| Cloud training (50 hrs) | $50 |
| Development time | Your time |
| **Total** | **~$350** |

### Recommended Setup
| Category | Cost |
|----------|------|
| Hardware (RTX 3080/4070) | $600 |
| Cloud training (100 hrs) | $100 |
| Storage & misc | $50 |
| **Total** | **~$750** |

### Full Production
| Category | Cost |
|----------|------|
| Hardware (RTX 4090) | $1,800 |
| Cloud training (200 hrs) | $200 |
| Infrastructure | $200 |
| **Total** | **~$2,200** |

---

## 13. Next Steps

1. **Decide on scope:** MVP or full system?
2. **Choose hardware strategy:** Local, cloud, or hybrid?
3. **Select target game:** Start with "I Am Your Beast" or simpler?
4. **Begin Phase 1:** Screen capture and basic pipeline
5. **Collect training data:** Record gameplay videos

---

## Appendix A: Similar Projects & Research

| Project | Approach | Results |
|---------|----------|---------|
| OpenAI Five (Dota 2) | RL + self-play | Beat world champions |
| DeepMind AlphaStar | IL + RL | Grandmaster level SC2 |
| **GT Sophy (Sony AI)** | Deep RL + racing sim | Beat world champion GT drivers |
| NVIDIA GameGAN | Video prediction | Generated playable games |
| OpenAI Gym Retro | RL benchmark | Many Atari/NES games solved |

### GT Sophy: Key Reference
Sony AI's **Gran Turismo Sophy** is particularly relevant to this project:
- **Scale:** Trained on 1,000+ PlayStation 4 consoles simultaneously
- **Platform:** DART (Distributed, Asynchronous Rollouts and Training) web-based system
- **Results:** Outperformed world champion Gran Turismo drivers
- **Publication:** Nature (2022) - "Outracing champion Gran Turismo drivers with deep reinforcement learning"
- **Deployment:** Now available to all GT7 players as "Race Together" mode
- **Key insight:** Mastered complex skills like wall-riding, sharp corner overtakes, and fair racing etiquette

GT Sophy demonstrates that consumer hardware (PS4s) can be leveraged for large-scale game AI training, and that such AI can be deployed to enhance player experiences.

### Key Papers
- "Playing Atari with Deep Reinforcement Learning" (Mnih et al., 2013)
- "Human-level control through deep RL" (Nature, 2015)
- "Learning from Human Preferences" (Christiano et al., 2017)
- "Decision Transformer" (Chen et al., 2021)
- **"Outracing champion Gran Turismo drivers with deep RL"** (Wurman et al., Nature 2022)

---

## Appendix B: Quick Start Architecture

For immediate prototyping, here's a minimal setup:

```python
# minimal_ai_player.py
import torch
import torch.nn as nn
import mss
import numpy as np
import pyvjoy

class SimpleGameAI(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 32, 8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, 4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, stride=1),
            nn.ReLU(),
            nn.Flatten(),
        )
        self.fc = nn.Sequential(
            nn.Linear(64 * 7 * 7, 512),
            nn.ReLU(),
            nn.Linear(512, 8),  # 8 action dimensions
        )
    
    def forward(self, x):
        return self.fc(self.conv(x))

class GamePlayer:
    def __init__(self):
        self.model = SimpleGameAI()
        self.sct = mss.mss()
        self.joy = pyvjoy.VJoyDevice(1)
        
    def capture_frame(self):
        img = self.sct.grab(self.sct.monitors[1])
        frame = np.array(img)[:, :, :3]
        frame = cv2.resize(frame, (84, 84))
        return torch.tensor(frame).permute(2, 0, 1).float() / 255.0
    
    def play_step(self):
        frame = self.capture_frame()
        with torch.no_grad():
            actions = self.model(frame.unsqueeze(0))
        self.execute_actions(actions[0])
```

---

*This proposal is a living document. Updates will be made as the project evolves.*
