# uiAccess & Code Signing Implementation Checklist

> **Status:** 🗺️ Future Roadmap

This is the actionable checklist for implementing uiAccess and code signing. See [uiaccess-signing-strategy.md](uiaccess-signing-strategy.md) for the full strategy document.

---

## Phase 1: Foundation

### Dependency Management
- [ ] Create `requirements.txt` with exact pinned versions (`==`)
- [ ] Generate lock file with transitive dependencies (`pip freeze` or `pip-compile`)
- [ ] Audit current dependencies — remove any unused packages
- [ ] Add `pip-audit` to CI workflow
- [ ] Document dependency update policy in CONTRIBUTING.md

### PyInstaller Configuration
- [ ] Create uiAccess manifest XML file
- [ ] Update PyInstaller spec to embed manifest
- [ ] Test build produces executable with correct manifest (inspect with `mt.exe` or sigcheck)
- [ ] Document build process in README or separate build doc

### Self-Signed Testing Setup
- [ ] Write script/instructions to generate self-signed code signing certificate
- [ ] Document how to add cert to Trusted Root + Trusted Publishers
- [ ] Test signing with self-signed cert
- [ ] Verify uiAccess works when installed to Program Files
- [ ] Verify uiAccess is ignored when run from Desktop (expected behavior)

### Runtime Detection
- [ ] Add startup logging for uiAccess status
- [ ] Detect: running from trusted location?
- [ ] Detect: executable is signed?
- [ ] Consider: Add uiAccess status to Settings/About dialog

---

## Phase 2: OV Certificate Integration

### Certificate Acquisition
- [ ] Research OV certificate providers (DigiCert, Sectigo, GlobalSign)
- [ ] Acquire OV code signing certificate for ATDev
- [ ] Store certificate securely (encrypted, limited access)
- [ ] Document certificate expiration date and renewal process

### CI/CD Signing
- [ ] Add OV certificate to CI secrets (encrypted)
- [ ] Create signing workflow (triggered on tags or manual)
- [ ] Include timestamping in signing command
- [ ] Output SHA256 hash of signed artifact
- [ ] Test: signed build has valid signature
- [ ] Test: uiAccess works with OV-signed build

### Installer
- [ ] Choose installer tool (Inno Setup, NSIS, or WiX)
- [ ] Create basic installer that installs to `C:\Program Files\ATDev\Nimbus\`
- [ ] Add Start Menu shortcut
- [ ] Sign the installer executable
- [ ] Test on clean Windows 10 VM
- [ ] Test on clean Windows 11 VM

### Internal Testing Distribution
- [ ] Establish beta distribution channel (GitHub pre-releases?)
- [ ] Document installation instructions for testers
- [ ] Create feedback mechanism for uiAccess issues

---

## Phase 3: EV Certificate & Production Release

### Certificate Acquisition
- [ ] Research EV certificate providers
- [ ] Acquire EV code signing certificate + hardware token
- [ ] Verify token works with signing tools
- [ ] Establish physical security for token (locked storage)
- [ ] Document token PIN policy (strong, not written down)

### Signing Ceremony Process
- [ ] Designate release manager(s) with token access
- [ ] Create signing ceremony checklist
- [ ] Create signing log template (what, when, who, commit hash)
- [ ] Test full ceremony with a test build

### Release Pipeline
- [ ] Document release branch/tag strategy
- [ ] Create pre-sign verification checklist
- [ ] Create post-sign verification checklist
- [ ] Establish human approval gate before signing
- [ ] Test full pipeline end-to-end

### SmartScreen Validation
- [ ] Test EV-signed installer on fresh Windows (no warnings expected)
- [ ] Document expected behavior for users

---

## Phase 4: Ongoing Operations

### Dependency Maintenance
- [ ] Schedule monthly dependency review
- [ ] Set up Dependabot or similar for vulnerability alerts
- [ ] Define policy: how long to delay updates after release
- [ ] Define severity thresholds (critical = block release, etc.)

### Certificate Renewal
- [ ] Calendar reminder 60 days before OV expiration
- [ ] Calendar reminder 60 days before EV expiration
- [ ] Document renewal process

### Multi-Product Scaling
- [ ] Extract signing scripts into reusable form
- [ ] Create parameterized CI workflow for any ATDev product
- [ ] Document how to onboard new product to signing infrastructure

---

## Validation Test Cases

### uiAccess Tests (run before each release)
- [ ] **Test 1**: Send input to elevated Task Manager → should work
- [ ] **Test 2**: SetForegroundWindow to background app → should be reliable
- [ ] **Test 3**: Run signed exe from Desktop → uiAccess should NOT be active
- [ ] **Test 4**: Run signed exe from Program Files → uiAccess should be active

### Signature Tests
- [ ] Right-click exe → Properties → Digital Signatures → valid
- [ ] Certificate chain is complete
- [ ] Timestamp is present
- [ ] `signtool verify /pa /v nimbus.exe` passes

### Functional Regression
- [ ] Application launches
- [ ] Virtual joystick works
- [ ] All buttons work (momentary + toggle)
- [ ] Sensitivity curves apply
- [ ] Config saves/loads
- [ ] Game Focus Mode works

---

## Related Documents

- [Full Strategy Document](uiaccess-signing-strategy.md)
- [Game Focus Mode](../completed/game-focus-mode.md) — Current workaround (implemented)
