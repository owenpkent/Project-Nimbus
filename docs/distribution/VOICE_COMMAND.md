# Voice Command Integration

## Overview

Voice command integration would allow users to trigger controller actions (button presses, axis locks, profile switches, mode changes) using spoken words — a critical accessibility feature for users with limited hand mobility who may rely on voice as a primary input modality.

This document explores the technical landscape, compares available engines, and outlines how voice commands could be integrated into Project Nimbus's existing QML/Python architecture.

---

## Use Cases

| Use Case | Example Command | Priority |
|----------|----------------|----------|
| Button press | "Fire", "Jump", "A button" | High |
| Toggle axis lock | "Lock X", "Unlock joystick" | High |
| Profile switch | "Switch to flight sim", "Xbox mode" | High |
| Throttle control | "Throttle up", "Full throttle", "Throttle fifty" | Medium |
| Sensitivity adjust | "More sensitive", "Reduce deadzone" | Medium |
| Emergency stop | "Center", "Stop", "Failsafe" | High |
| UI navigation | "Open settings", "Save profile" | Low |

---

## The Latency Problem

Voice command latency is the critical constraint for gaming. The pipeline is:

```
Microphone → Audio Buffer → Model Inference → Command Parse → vJoy/ViGEm → Game
```

**Target latency:** < 200ms end-to-end for gaming to feel responsive
**Acceptable latency:** < 500ms for non-time-critical commands

### Latency Sources

| Stage | Typical Time | Notes |
|-------|-------------|-------|
| Audio buffer fill | 30–100ms | Depends on chunk size |
| Model inference | 20–500ms | Varies wildly by engine |
| Command parsing | < 5ms | Negligible |
| vJoy write | < 1ms | Negligible |

The model inference stage is where engines diverge dramatically.

---

## Engine Comparison

### 1. Vosk (Current Consideration)

**Pros:**
- Fully offline, no internet required
- **Constrained vocabulary / grammar mode** — only recognizes words you define
- Very fast inference on constrained grammars (~50–150ms)
- Free and open source
- Python bindings available

**Cons:**
- Accuracy suffers on unconstrained speech
- Constrained mode requires exact word matches (no fuzzy matching)
- Model quality lower than Whisper or cloud services
- Requires careful grammar design

**Verdict:** Best for constrained command sets. If you define exactly 30–50 commands, Vosk with a grammar file is fast and reliable. The accuracy problem you experienced is likely from using it in free-speech mode rather than constrained grammar mode.

**Constrained grammar example:**
```python
grammar = '["fire", "jump", "lock x", "unlock", "throttle up", "throttle down", "stop", "[unk]"]'
rec = KaldiRecognizer(model, 16000, grammar)
```

---

### 2. OpenAI Whisper (Local)

**Pros:**
- State-of-the-art accuracy, even for unusual speech patterns
- Handles accents, speech impediments, and non-standard pronunciation well
- Fully offline (after model download)
- Free and open source

**Cons:**
- **High latency** — base model: ~300–800ms; small model: ~150–400ms on CPU
- No native constrained vocabulary mode
- Requires GPU for real-time performance (see hardware section)
- Not designed for streaming/real-time use

**Whisper model sizes:**

| Model | Parameters | CPU Latency | GPU Latency | VRAM |
|-------|-----------|-------------|-------------|------|
| tiny | 39M | ~150ms | ~30ms | ~1GB |
| base | 74M | ~300ms | ~50ms | ~1GB |
| small | 244M | ~600ms | ~100ms | ~2GB |
| medium | 769M | ~2000ms | ~200ms | ~5GB |
| large | 1550M | ~5000ms+ | ~400ms | ~10GB |

**Verdict:** Excellent accuracy but too slow on CPU for real-time gaming. Viable with a dedicated GPU. `whisper.cpp` (C++ port) is significantly faster.

---

### 3. Whisper.cpp (C++ Port)

**Pros:**
- 3–5x faster than Python Whisper
- Supports real-time streaming mode
- Runs on CPU reasonably well (tiny/base models)
- Supports Apple Silicon, CUDA, OpenCL acceleration

**Cons:**
- Requires C++ build or pre-built binaries
- Python bindings via `pywhispercpp` are less mature
- Still no native constrained vocabulary

**Tiny model on modern CPU:** ~80–150ms — borderline viable for gaming

---

### 4. Faster-Whisper

**Pros:**
- 4x faster than original Whisper with same accuracy
- Uses CTranslate2 backend (optimized inference)
- Python-native, easy to install
- Supports streaming with VAD (Voice Activity Detection)
- Runs well on CPU for small/base models

**Cons:**
- Still no constrained vocabulary
- Requires post-processing to map recognized text to commands

**Tiny model on CPU:** ~60–120ms — viable for gaming commands

**Verdict: Best balance of accuracy and speed for local offline use.** Recommended starting point.

---

### 5. DeepGram (Cloud)

**Pros:**
- Extremely accurate, handles speech impediments well
- Nova-2 model: ~100–300ms round-trip (including network)
- Streaming API with real-time transcription
- Custom vocabulary/boosting for specific words
- Handles non-standard speech patterns

**Cons:**
- **Requires internet connection** — not viable for offline use
- **Costs money** — $0.0043/minute (Pay-as-you-go), free tier available
- Privacy concerns (audio sent to cloud)
- Network latency adds unpredictability
- Not suitable for users with unreliable internet

**Verdict:** Best accuracy and reasonable latency, but the internet dependency is a significant barrier for an accessibility tool. Could be offered as an optional premium mode.

---

### 6. Silero VAD + Vosk/Whisper Hybrid

**Architecture:**
1. **Silero VAD** detects when speech starts/ends (< 10ms, very lightweight)
2. Only run the recognition model on detected speech segments
3. Reduces false positives and unnecessary inference

This is the recommended architecture regardless of which recognition engine is chosen — VAD dramatically reduces latency by not processing silence.

---

### 7. Pocketsphinx

**Pros:**
- Very lightweight, fast
- Constrained grammar support

**Cons:**
- Outdated (CMU Sphinx, largely unmaintained)
- Poor accuracy compared to modern alternatives
- Not recommended for new projects

---

## Recommended Architecture

### Tier 1: Fast + Offline (Recommended Default)

```
Microphone → PyAudio stream → Silero VAD → Faster-Whisper (tiny) → Command Parser → Bridge
```

- **Latency:** ~80–150ms
- **Accuracy:** High (Whisper-quality)
- **Hardware:** Any modern CPU (no GPU required for tiny model)
- **Cost:** Free

### Tier 2: Maximum Accuracy + Offline

```
Microphone → PyAudio stream → Silero VAD → Faster-Whisper (base/small) + GPU → Command Parser → Bridge
```

- **Latency:** ~40–80ms with GPU
- **Accuracy:** Excellent
- **Hardware:** NVIDIA GPU with CUDA (GTX 1060+ or better)
- **Cost:** Free

### Tier 3: Cloud (Optional Premium)

```
Microphone → PyAudio stream → Silero VAD → DeepGram Streaming API → Command Parser → Bridge
```

- **Latency:** ~100–300ms (network dependent)
- **Accuracy:** Best available
- **Hardware:** Any (internet required)
- **Cost:** ~$0.0043/min

---

## Command Parser Design

Regardless of engine, the recognized text needs to map to controller actions. A fuzzy matching approach handles minor recognition errors:

```python
COMMAND_MAP = {
    "fire": lambda: bridge.pressButton(1),
    "jump": lambda: bridge.pressButton(2),
    "lock x": lambda: bridge.lockAxis("left", "x"),
    "unlock": lambda: bridge.unlockAll(),
    "throttle up": lambda: bridge.adjustThrottle(+0.1),
    "throttle down": lambda: bridge.adjustThrottle(-0.1),
    "full throttle": lambda: bridge.setThrottle(1.0),
    "stop": lambda: bridge.emergencyCenter(),
    "flight sim": lambda: bridge.switchProfile("flight_simulator"),
    "xbox mode": lambda: bridge.switchProfile("xbox_controller"),
}

def parse_command(text: str):
    text = text.lower().strip()
    # Exact match first
    if text in COMMAND_MAP:
        return COMMAND_MAP[text]()
    # Fuzzy match (difflib or rapidfuzz)
    best = max(COMMAND_MAP.keys(), key=lambda k: similarity(k, text))
    if similarity(best, text) > 0.8:
        return COMMAND_MAP[best]()
```

---

## Integration with Project Nimbus Architecture

### Python Side (`src/voice_interface.py`)

New module exposing voice recognition as a background thread:

```python
class VoiceInterface(QObject):
    commandRecognized = Signal(str)   # Emits recognized command text
    listeningChanged = Signal(bool)   # Emits when listening state changes
    
    def start_listening(self): ...
    def stop_listening(self): ...
    def set_engine(self, engine: str): ...  # "faster-whisper", "vosk", "deepgram"
```

### Bridge Integration (`src/bridge.py`)

```python
# New slots exposed to QML
@Slot()
def toggleVoiceListening(self): ...

@Slot(str)
def onVoiceCommand(self, command: str): ...
```

### QML Integration

- Microphone icon in status bar (green = listening, red = off)
- Visual feedback when a command is recognized
- Settings dialog for engine selection, sensitivity, command mapping

---

## Accessibility Considerations

- **Speech impediments:** Whisper handles these significantly better than Vosk
- **Quiet environments:** VAD threshold should be configurable
- **Noisy environments:** Noise suppression (e.g., `noisereduce` library) before inference
- **Custom vocabulary:** Allow users to remap commands to their preferred words
- **Confirmation feedback:** Audio or visual confirmation that a command was received
- **Hands-free toggle:** Voice command to enable/disable voice listening itself

---

## Dependencies

```
# Tier 1 (Recommended)
faster-whisper>=0.10.0
silero-vad>=4.0
pyaudio>=0.2.13
rapidfuzz>=3.0.0      # fuzzy command matching

# Optional: Vosk (constrained grammar alternative)
vosk>=0.3.45

# Optional: DeepGram (cloud)
deepgram-sdk>=3.0.0
```

---

## Hardware Requirements

| Configuration | CPU | RAM | GPU | Notes |
|---------------|-----|-----|-----|-------|
| Minimum (Vosk constrained) | Any dual-core | 4GB | None | ~100ms latency |
| Recommended (Faster-Whisper tiny) | Quad-core 3GHz+ | 8GB | None | ~100–150ms latency |
| Optimal (Faster-Whisper base + GPU) | Any | 8GB | GTX 1060 / RX 580 | ~40–80ms latency |
| Best (Faster-Whisper small + GPU) | Any | 16GB | RTX 2060+ | ~30–60ms latency |

---

## Implementation Roadmap

1. **Proof of concept** — Faster-Whisper tiny + Silero VAD, hardcoded command map
2. **UI integration** — Listening indicator, command feedback in QML
3. **Settings dialog** — Engine selection, command remapping, VAD threshold
4. **Profile integration** — Per-profile command maps
5. **Optional cloud tier** — DeepGram as opt-in setting
6. **Noise suppression** — For noisy environments

---

## Existing Foundation: GitConnect

The DeepGram streaming integration does **not** need to be built from scratch. A working implementation already exists in the companion project **GitConnect** (`C:\Users\Owen\dev\gitconnect`), which uses DeepGram Nova-3 with real-time WebSocket streaming for voice-to-code editing.

### What GitConnect Already Has

`gitconnect/web/src/hooks/useDeepgram.ts` implements:
- WebSocket connection to `wss://api.deepgram.com/v1/listen`
- **Nova-3 model** with `interim_results`, `vad_events`, `utterance_end_ms`, and `endpointing` parameters
- 250ms audio chunk streaming via `MediaRecorder`
- Real-time audio level monitoring (RMS via `AnalyserNode`)
- Managed API key proxy (Pro tier) with user-key fallback
- Clean start/stop lifecycle with stream teardown

### Adaptation Strategy for Project Nimbus

GitConnect's hook is TypeScript/React (browser). For Nimbus (Python/PySide6), the equivalent Python port would be:

```python
import asyncio
import websockets
import pyaudio
import json

DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-3&language=en-US"
    "&interim_results=true&vad_events=true"
    "&utterance_end_ms=1000&endpointing=300"
)

class DeepgramStream:
    def __init__(self, api_key: str, on_transcript):
        self.api_key = api_key
        self.on_transcript = on_transcript

    async def stream(self):
        async with websockets.connect(
            DEEPGRAM_URL,
            extra_headers={"Authorization": f"Token {self.api_key}"}
        ) as ws:
            audio = pyaudio.PyAudio()
            stream = audio.open(format=pyaudio.paInt16, channels=1,
                                rate=16000, input=True, frames_per_buffer=4000)
            async def send():
                while True:
                    chunk = stream.read(4000, exception_on_overflow=False)
                    await ws.send(chunk)
                    await asyncio.sleep(0)
            async def recv():
                async for msg in ws:
                    data = json.loads(msg)
                    transcript = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                    if transcript:
                        self.on_transcript(transcript, data.get("is_final", False))
            await asyncio.gather(send(), recv())
```

### Key Parameters from GitConnect (Proven Working)

| Parameter | Value | Effect |
|-----------|-------|--------|
| `model` | `nova-3` | Best accuracy, ~100–200ms latency |
| `utterance_end_ms` | `1000` | Fires final transcript after 1s silence |
| `endpointing` | `300` | Detects end of speech at 300ms |
| `interim_results` | `true` | Partial results for low-latency feedback |
| `vad_events` | `true` | Speech start/end events |
| `chunk interval` | `250ms` | Audio send frequency |

The `endpointing=300` + `interim_results=true` combination is what makes GitConnect feel responsive — interim results fire immediately while the final transcript confirms after 300ms silence. This same pattern should be used for Nimbus command detection: **act on interim results for time-critical commands, confirm on final**.

---

## References

- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)
- [Silero VAD](https://github.com/snakers4/silero-vad)
- [Vosk](https://alphacephei.com/vosk/)
- [DeepGram Streaming API](https://developers.deepgram.com/docs/getting-started-with-live-streaming-audio)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [pywhispercpp](https://github.com/abdeladim-s/pywhispercpp)
- [GitConnect useDeepgram.ts](../../../../gitconnect/web/src/hooks/useDeepgram.ts) — existing working implementation
