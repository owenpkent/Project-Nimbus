# Project Nimbus – YouTube Showcase Shot List

## 1. Hook (5–10 seconds)

- **Shot 1 – Problem cold open**
  - Screen: Mission Planner or a game that "Requires joystick".
  - Action: Cursor hovering over a greyed-out joystick option.
  - VO/Text: "What if you can’t use a physical joystick?"

- **Shot 2 – Instant solution teaser**
  - Screen: Close-up of Project Nimbus UI (both joysticks, throttle, rudder, buttons).
  - Action: Quick, smooth joystick movement with the mouse.
  - VO/Text: "This mouse-driven virtual controller solves that."

---

## 2. Quick Intro (10–20 seconds)

- **Shot 3 – Intro**
  - Camera: Talking head OR title card if you prefer no facecam.
  - Action: Brief explanation of what Nimbus is.
  - Script idea: "This is Project Nimbus, a virtual joystick that turns mouse input into vJoy signals for drones, games, or accessibility setups."

---

## 3. What It Does – Feature Tour (45–90 seconds)

- **Shot 4 – Full UI overview**
  - Screen: Main Qt/QML interface.
  - Action: Slow pan/zoom to show dual joysticks, throttle, rudder, and buttons.
  - VO: High-level feature overview.

- **Shot 5 – Dual joystick demo**
  - Screen: Center on joystick area.
  - Action: Move left and right sticks with the mouse; show smooth movement and return.
  - Overlay: Labels "Left Stick", "Right Stick" and maybe axis values.

- **Shot 6 – Throttle & rudder**
  - Screen: Focus on throttle and rudder sliders.
  - Action: Demonstrate throttle staying where placed, rudder auto-centering.
  - VO: Call out behavior differences.

- **Shot 7 – Buttons + ARM/RTH**
  - Screen: Close-up of buttons.
  - Action: Show a momentary button vs a toggle button (including ARM/RTH).
  - Overlay: "Toggle" vs "Momentary".

---

## 4. Accessibility & Use Cases (30–60 seconds)

- **Shot 8 – Accessibility framing**
  - Screen: B-roll of mouse / assistive hardware, or abstract footage.
  - Text: "Built with accessibility in mind".
  - VO: Explain why a virtual joystick matters if users can’t use physical controllers.

- **Shot 9 – Application montage**
  - Clips: Very short cuts of
    - Mission Planner / UAV control screen
    - A game using vJoy
    - A sim or other visualization
  - Text overlays: "UAV", "Gaming", "Research & Prototyping", "Assistive Tech".

---

## 5. Under the Hood – Architecture (45–90 seconds)

- **Shot 10 – Architecture overview**
  - Screen: Simple diagram or capture of `docs/architecture.md` / README architecture section.
  - Highlight: QML UI → ControllerBridge → ControllerConfig & VJoyInterface → vJoy.

- **Shot 11 – Config & curves**
  - Screen: Joystick Settings dialog.
  - Action: Move sensitivity/deadzone sliders and show the live curve preview updating.

- **Shot 12 – Axis mapping**
  - Screen: Axis Mapping dialog.
  - Action: Change mappings for left/right sticks, throttle, rudder.

- **Shot 13 – vJoy status**
  - Screen: Terminal/log snippet or any status indicator that vJoy is connected.
  - VO: Mention Python + pyvjoy and safety behavior.

---

## 6. Installation & Launch (20–40 seconds)

- **Shot 14 – Standalone executable**
  - Screen: README section "Standalone Executable" and Windows Explorer.
  - Action: Show `Project-Nimbus.exe` being double-clicked and the app appearing.

- **Shot 15 – Run from source**
  - Screen: Terminal.
  - Action: Show commands:
    - `git clone ...`
    - `pip install -r requirements.txt`
    - `python run.py`
  - Text: "Open source – hackable".

---

## 7. In-Use Hero Demo (30–60 seconds)

- **Shot 16 – Split-screen control**
  - Layout: Left – Nimbus UI; Right – target app (Mission Planner, sim, or test harness).
  - Action: Move joysticks/throttle/rudder and show immediate response on the right side.

- **Shot 17 – Smooth behavior & safety**
  - Screen: Close up on joystick returning smoothly to center, maybe mention smoothing/failsafe.
  - VO: Briefly highlight smooth returns and safety mindset.

---

## 8. Closing & Call to Action (10–20 seconds)

- **Shot 18 – Outro**
  - Camera: Talking head or title card.
  - Script idea: "If you know someone who needs an accessible joystick alternative, share this. Link to Project Nimbus and docs is in the description. Contributions are welcome." 

- **Shot 19 – End screen**
  - Screen: Logo + links.
  - Elements:
    - GitHub repo URL
    - Subscribe / like prompt
    - Teaser text: "Next video: building the Windows installer step by step."
