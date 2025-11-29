# Project Nimbus – TODO

## UI & UX
- [x] **Flight Sim layout aesthetics**
  - [x] Responsive button sizing that scales with window height
  - [x] Better visual balance at smaller window sizes

- [ ] **Smaller, labeled numbered buttons**
  - [ ] Reduce button size for numbered buttons (1-9, etc.)
  - [ ] Add clear labels to each button

- [x] **Rudder control improvements**
  - [x] Make rudder control wider for better usability
  - [x] Add option to disable center return (sticky mode) - Rudder Lock button implemented

- [ ] **Profile system**
  - [ ] Implement profile switching (e.g., Microsoft Flight Simulator 24, General Gaming/Xbox, Driving Games)
  - [ ] Allow users to create, save, and load custom profiles
  - [ ] Store profile configurations persistently

- [ ] **Macro system (inspired by Celtic Magic Game Control Mixer)**
  - [ ] Design macro recording and playback system
  - [ ] Allow binding macros to buttons/key combinations
  - [ ] Support sequence recording and conditional execution
  - [ ] Reference: See `inspiration/gcm_joystick_modes.png` for design inspiration

## Release & Distribution
- [ ] **Create Windows installer (MSI/EXE)**
  - [ ] Choose packaging tool (e.g. PyInstaller + NSIS / Inno Setup / MSI)
  - [ ] Define entry point for Qt launcher (e.g. `python run.py` → Qt UI)
  - [ ] Bundle required runtime dependencies (Python, DLLs, vJoy requirements, etc.)
  - [ ] Configure installer shortcuts (Desktop, Start Menu) and icons
  - [ ] Add uninstall support and cleanup of config/log files as appropriate
  - [ ] Test installer on clean Windows VM

- [ ] **vJoy Detection & Installation**
  - [ ] Add vJoy detection on application startup
  - [ ] Display warning/error if vJoy is not installed
  - [ ] Bundle vJoy installer with Project Nimbus installer
  - [ ] Implement automatic vJoy installation during setup (with user consent)
  - [ ] Verify vJoy device configuration after installation
  - [ ] Provide clear instructions if manual vJoy setup is required

- [ ] **Portable build (no installer)**
  - [ ] Produce a zipped portable build for advanced users
  - [ ] Document how to launch (Qt vs legacy Pygame, command-line flags)
  - [ ] Include vJoy detection and installation instructions for portable users
