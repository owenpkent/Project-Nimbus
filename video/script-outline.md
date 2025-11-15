# Project Nimbus – YouTube Script Outline

This outline pairs with `video/shotlist.md`.

---

## 1. Hook (5–10 seconds)

**Lines (rough):**
- "What if you needed a joystick… but couldn’t use your hands?"
- "Project Nimbus turns simple mouse input into a full virtual joystick for drones, games, and more."

Goal: Immediately show the problem + visual tease of Nimbus.

---

## 2. Intro (10–20 seconds)

**Lines:**
- "Hey, I’m [Name], and this is Project Nimbus."
- "It’s an open-source virtual controller that sends joystick commands through vJoy, using a mouse-first interface." 
- Optional: "I built it with accessibility in mind, so people who can’t use traditional controllers still get full joystick control."

---

## 3. Feature Tour (45–90 seconds)

**Narration beats:**
- "The main interface gives you dual virtual joysticks, a dedicated throttle, and a rudder slider."
- "Everything is smooth and low-latency, so it feels like a real joystick." 
- "You also get 10 buttons, including ARM and Return-to-Home, each configurable as toggle or momentary."

As you say these, follow the shot list: show full UI, then joysticks, then throttle/rudder, then buttons.

---

## 4. Accessibility & Use Cases (30–60 seconds)

**Narration beats:**
- "Nimbus is especially useful if a physical joystick just isn’t an option—whether that’s because of mobility limitations or your hardware setup." 
- "Because it talks to vJoy, you can use it with ground control software like Mission Planner, games that support joysticks, or even your own research and prototypes." 

Optional line:
- "If you’re working on assistive tech, this can be one building block in a larger system." 

---

## 5. Under the Hood – Architecture (45–90 seconds)

**Narration beats:**
- "Under the hood, Nimbus is built with Qt Quick and Python." 
- "The QML UI talks to a Python bridge object called `ControllerBridge`." 
- "That bridge uses a `ControllerConfig` class to handle settings, curves, and scaling…" 
- "…and a `VJoyInterface` class to send axis and button updates to the vJoy driver in real time." 

Optional deeper line for devs:
- "The config system stores everything in a JSON file, so you can tweak sensitivity curves, deadzones, safety limits, and more." 

---

## 6. Installation & Launch (20–40 seconds)

**Narration beats:**
- "For end users, there’s a standalone Windows executable—just install vJoy, run the EXE, and you’re in." 
- "If you want to hack on the code, clone the repo, install the Python dependencies, and run `python run.py` to start the Qt Quick UI." 

Mention briefly:
- "All of the build steps are documented, so you can also roll your own executable if you’d like." 

---

## 7. In-Use Hero Demo (30–60 seconds)

**Narration beats:**
- "Here’s Nimbus in action. On the left, you can see the UI. On the right, you can see how the target app responds." 
- "Moving the sticks and sliders in Nimbus directly drives vJoy axes under the hood." 
- "There’s optional smoothing so the controls glide back to center instead of snapping." 

If you show safety/failsafe:
- "There’s also a focus on safety—like centering axes if something goes wrong." 

---

## 8. Closing & Call to Action (10–20 seconds)

**Lines:**
- "If you know someone who needs an accessible joystick alternative, please share this video with them." 
- "You’ll find links to Project Nimbus, the docs, and the architecture overview in the description." 
- "If you want to help, contributions on GitHub are very welcome." 
- Optional: "In a follow-up video, I’ll show how to build the Windows installer step by step." 

End card text:
- "Project Nimbus – Virtual Joystick" 
- "GitHub link" 
- "Subscribe for more builds & deep dives"
