# uiAccess, Code Signing, and Secure Release Strategy

> **Status:** 🗺️ Future Roadmap

## Executive Summary

This document outlines the architectural and operational strategy for:
1. Enabling uiAccess privileges in Project Nimbus for reliable assistive technology behavior
2. Implementing code signing with a path from OV (testing) to EV (production)
3. Establishing a secure release workflow with supply chain protections
4. Scaling these practices across multiple ATDev products

The goal is Windows On-Screen Keyboard parity: Nimbus should reliably send input to elevated windows, overlay above secure desktops when appropriate, and behave as a trusted assistive technology.

---

## Part 1: Understanding uiAccess

### What uiAccess Provides

uiAccess is a Windows security feature designed specifically for assistive technologies. When enabled, an application gains:

| Capability | Without uiAccess | With uiAccess |
|------------|------------------|---------------|
| Send input to elevated windows | ❌ Blocked by UIPI | ✅ Allowed |
| Interact with UAC prompts | ❌ Cannot | ✅ Can send input |
| Set foreground window reliably | ❌ Windows restrictions apply | ✅ Bypasses restrictions |
| Overlay above other windows | ⚠️ Limited | ✅ Full topmost capability |
| Run from any directory | ✅ Yes | ❌ Must be in trusted location |

### Windows Requirements for uiAccess

Windows enforces three requirements for uiAccess to be honored:

1. **Manifest Declaration**: The executable must contain a manifest with `uiAccess="true"`
2. **Code Signature**: The executable must be signed with a valid code signing certificate
3. **Trusted Location**: The executable must run from `%ProgramFiles%` or `%SystemRoot%`

If any requirement is missing, Windows silently ignores `uiAccess="true"` and runs the application as a normal user-mode process.

### Why This Matters for Nimbus

Our current Game Focus Mode uses `AttachThreadInput` + `SetForegroundWindow` tricks to restore focus after interactions. This works for most games but fails when:

- The target application is elevated (admin)
- The game uses certain anti-cheat systems
- Windows decides not to honor `SetForegroundWindow`

With uiAccess, these workarounds become unnecessary. Nimbus can send input directly without focus manipulation, similar to how the Windows On-Screen Keyboard works.

---

## Part 2: Development and Testing Strategy

### Proposed Development Tiers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT TIERS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Tier 1: Local Development (No Signing)                                    │
│  ├── Run from source or PyInstaller build                                  │
│  ├── uiAccess="false" in manifest                                          │
│  ├── Works anywhere on filesystem                                          │
│  └── Used for: UI work, vJoy integration, feature development              │
│                                                                             │
│  Tier 2: Internal Testing (Self-Signed or OV)                              │
│  ├── PyInstaller build with uiAccess="true" manifest                       │
│  ├── Signed with test certificate or OV cert                               │
│  ├── Installed to Program Files                                            │
│  └── Used for: Testing uiAccess behavior, elevated window interaction      │
│                                                                             │
│  Tier 3: Production Release (EV Signed)                                    │
│  ├── Full release build with uiAccess="true"                               │
│  ├── Signed with EV certificate                                            │
│  ├── Distributed via installer                                             │
│  └── Used for: End user distribution                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Behavioral Testing Matrix

Developers should validate uiAccess behavior against this matrix:

| Test Scenario | Expected Without uiAccess | Expected With uiAccess |
|---------------|---------------------------|------------------------|
| Send input to Notepad (normal) | ✅ Works | ✅ Works |
| Send input to Task Manager (elevated) | ❌ Blocked by UIPI | ✅ Works |
| Use joystick while UAC prompt is visible | ❌ Cannot interact | ✅ Input reaches prompt |
| SetForegroundWindow to any app | ⚠️ May be ignored | ✅ Reliable |
| Overlay above elevated windows | ❌ Z-order clamped | ✅ True topmost |
| Run from Desktop folder | ✅ Works | ❌ uiAccess silently ignored |
| Run from Program Files | ✅ Works | ✅ uiAccess active |

---

## Part 3: Code Signing Architecture

### Certificate Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CERTIFICATE STRATEGY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Organization: ATDev (or your legal entity name)                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OV Code Signing Certificate                                         │   │
│  │  ├── Purpose: Internal testing, CI/CD automation                     │   │
│  │  ├── Storage: Software keystore (exportable with passphrase)         │   │
│  │  ├── SmartScreen: Builds reputation slowly                           │   │
│  │  ├── Cost: ~$200-400/year                                            │   │
│  │  └── Products: All ATDev products (Nimbus, future tools)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EV Code Signing Certificate                                         │   │
│  │  ├── Purpose: Production releases                                    │   │
│  │  ├── Storage: Hardware token (USB HSM)                               │   │
│  │  ├── SmartScreen: Immediate reputation (no warnings)                 │   │
│  │  ├── Cost: ~$300-600/year + hardware token                           │   │
│  │  └── Products: All ATDev products (shared identity)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### OV vs EV: When to Use Each

| Aspect | OV Certificate | EV Certificate |
|--------|---------------|----------------|
| **Use For** | Dev builds, CI testing, beta releases | Production releases |
| **SmartScreen** | Warning until reputation builds | Immediate trust |
| **Storage** | Software (can be automated) | Hardware token required |
| **CI/CD Friendly** | Yes, fully automatable | Limited (token PIN required) |
| **uiAccess** | Works (Windows accepts OV) | Works |
| **User Trust** | Lower (may see warnings) | Higher (no warnings) |

---

## Part 4: Secure Release Workflow

### Separation of Build and Signing

The core security principle: **The build environment should never have access to the signing key.**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUILD AND SIGN SEPARATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────┐      ┌──────────────────────┐                    │
│  │   BUILD ENVIRONMENT   │      │   SIGN ENVIRONMENT   │                    │
│  │                       │      │                       │                    │
│  │  • CI/CD runner       │      │  • Dedicated machine  │                    │
│  │  • No signing keys    │      │  • Air-gapped or      │                    │
│  │  • Produces unsigned  │─────►│    restricted network │                    │
│  │    artifacts          │      │  • Has EV token       │                    │
│  │  • Computes hashes    │      │  • Manual operation   │                    │
│  │                       │      │                       │                    │
│  └──────────────────────┘      └──────────────────────┘                    │
│                                                                             │
│  Why: If build environment is compromised, attacker cannot sign malware.   │
│  Signing requires physical access to token + PIN.                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Release Pipeline Stages

1. **Source Verification** — Ensure release branch is clean, tests pass, dependencies audited
2. **Build** — Fresh environment, pinned dependencies, PyInstaller with manifest
3. **Pre-Sign Verification** — Verify hash matches, human approval gate
4. **Signing** — EV token + PIN, include timestamp
5. **Post-Sign Verification** — Verify signature, certificate chain, timestamp, uiAccess
6. **Release** — Upload to GitHub Releases, publish hashes

---

## Part 5: Rollout Phases

### Phase 1: Foundation (Now → OV Certificate)

- Set up dependency pinning and vulnerability scanning
- Create PyInstaller build with uiAccess manifest
- Test with self-signed certificate on dev machine

### Phase 2: OV Integration

- Integrate OV signing into CI
- Produce signed internal test builds
- Validate uiAccess works with OV signature
- Build installer framework

### Phase 3: EV Production

- Acquire EV certificate
- Establish signing ceremony process
- Produce first EV-signed production build
- Verify SmartScreen behavior

### Phase 4: Mature Operations

- Regular dependency audits
- Automated vulnerability monitoring
- Streamlined release process

---

## Appendix: Manifest Configuration

The uiAccess manifest should contain:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="true"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
```

**Key Points:**
- `level="asInvoker"`: Nimbus does not require admin rights itself
- `uiAccess="true"`: Request assistive technology privileges
- This manifest must be embedded in the executable (PyInstaller supports this)

---

## Related Documents

- [Implementation Checklist](uiaccess-signing-checklist.md) — Phased TODO list
- [Game Focus Mode](../completed/game-focus-mode.md) — Current workaround (implemented)
