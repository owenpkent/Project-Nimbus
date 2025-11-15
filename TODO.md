# Project Nimbus – TODO

## Release & Distribution
- [ ] **Create Windows installer (MSI/EXE)**
  - [ ] Choose packaging tool (e.g. PyInstaller + NSIS / Inno Setup / MSI)
  - [ ] Define entry point for Qt launcher (e.g. `python run.py` → Qt UI)
  - [ ] Bundle required runtime dependencies (Python, DLLs, vJoy requirements, etc.)
  - [ ] Configure installer shortcuts (Desktop, Start Menu) and icons
  - [ ] Add uninstall support and cleanup of config/log files as appropriate
  - [ ] Test installer on clean Windows VM

- [ ] **Portable build (no installer)**
  - [ ] Produce a zipped portable build for advanced users
  - [ ] Document how to launch (Qt vs legacy Pygame, command-line flags)

- [ ] **Versioning & Releases**
  - [ ] Decide on versioning scheme (e.g. Semantic Versioning)
  - [ ] Add version constant in code and surface it in the UI/About dialog
  - [ ] Set up GitHub release process (tags, changelog, attached binaries)

## UI & UX
- [ ] **Qt UI polish**
  - [ ] Review current Qt layouts for scaling and DPI-awareness
  - [ ] Ensure all controls are keyboard/mouse accessible
  - [ ] Add basic theming (light/dark mode if desired)

- [ ] **Configuration UX**
  - [ ] Provide a clear configuration panel for controller mappings, vJoy settings, etc.
  - [ ] Add validation and helpful error messages for invalid configurations
  - [ ] Ensure configuration changes can be saved and reloaded reliably

- [ ] **Help & Onboarding**
  - [ ] Add an in-app "Help" or "Getting Started" section
  - [ ] Provide quick links to README, FAQ, and issue tracker

## Core Functionality
- [ ] **vJoy integration**
  - [ ] Confirm vJoy detection and error handling are robust
  - [ ] Add diagnostics panel to show current vJoy device state

- [ ] **Input mapping**
  - [ ] Review joystick/button/slider mapping logic
  - [ ] Add presets and the ability to export/import mappings

- [ ] **Legacy Pygame mode**
  - [ ] Confirm `--pygame` legacy mode still works as expected
  - [ ] Decide long-term support status (keep, deprecate, or remove)

## Quality & Testing
- [ ] **Automated tests**
  - [ ] Add unit tests for core logic (config handling, mapping, vJoy interface)
  - [ ] Add smoke tests for Qt startup and basic flows

- [ ] **Manual testing checklist**
  - [ ] Test on multiple Windows versions (10, 11, different DPI settings)
  - [ ] Test with and without vJoy installed
  - [ ] Test first-run experience (no config file present)

- [ ] **CI / CD**
  - [ ] Set up CI to run tests on push/PR
  - [ ] Optionally automate build of installer/portable artifacts for tagged releases

## Documentation
- [ ] **README updates**
  - [ ] Clearly describe Qt vs Pygame modes and how to launch each
  - [ ] Add installation instructions including vJoy requirements
  - [ ] Document known limitations and troubleshooting tips

- [ ] **Developer docs**
  - [ ] Add a short "Architecture" section (Qt shell, core logic, config system)
  - [ ] Document how to build from source and how to create the installer

## Housekeeping
- [ ] **Code cleanup**
  - [ ] Remove dead code and stale branches related to pre-Qt architecture if obsolete
  - [ ] Normalize logging (levels, format, log file location)

- [ ] **Issue tracking & roadmap**
  - [ ] Turn this TODO into GitHub issues or a project board
  - [ ] Prioritize tasks for the next release milestone
