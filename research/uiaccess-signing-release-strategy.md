# Project Nimbus: uiAccess, Code Signing, and Secure Release Strategy

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

## Part 2: Development and Testing Strategy for uiAccess

### The Development Challenge

uiAccess cannot be tested with unsigned builds. This creates a chicken-and-egg problem: how do developers test uiAccess behavior before you have production signing infrastructure?

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

### Self-Signed Testing for uiAccess

Before acquiring an OV certificate, developers can test uiAccess using a self-signed certificate that is manually trusted on the development machine:

**High-Level Process:**
1. Generate a self-signed code signing certificate
2. Add the certificate to the machine's Trusted Root and Trusted Publishers stores
3. Sign the Nimbus executable with this certificate
4. Install to Program Files
5. Run and verify uiAccess behavior

**Key Constraint**: This only works on machines where the self-signed certificate has been explicitly trusted. It cannot be used for distribution.

**Security Note**: The self-signed certificate should be generated uniquely per developer machine and kept in a developer-only key store. It should never be shared or used for anything other than local testing.

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

### Detecting uiAccess at Runtime

Nimbus should detect whether it is actually running with uiAccess privileges and surface this information:

**What to Detect:**
- Is the manifest present with uiAccess="true"?
- Is the executable signed?
- Is the executable running from a trusted location?
- Can we successfully send input to an elevated test target?

**How to Surface:**
- Debug logging at startup: "uiAccess: enabled" or "uiAccess: not available (reason)"
- Settings/About dialog showing uiAccess status
- Consider warning if user installed to non-Program Files location

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

### Recommended Approach

1. **Start with OV**: Acquire an OV certificate immediately. This enables:
   - Testing uiAccess in realistic conditions
   - Building CI/CD signing automation
   - Distributing to internal testers

2. **Add EV for Production**: When ready for public release, acquire EV. Use it only for:
   - Final production builds
   - Official releases to end users

3. **Share Across Products**: Both certificates should be issued to "ATDev" (or your organization). This allows signing any ATDev product without separate certificates.

### Timestamping

Always timestamp signatures using an RFC 3161 timestamp server. This ensures signatures remain valid after the certificate expires:

**Why This Matters:**
- Code signing certificates typically expire in 1-3 years
- Without timestamping, signatures become invalid when the cert expires
- With timestamping, signatures remain valid indefinitely (as long as cert was valid at signing time)

**Recommended Timestamp Servers:**
- DigiCert: `http://timestamp.digicert.com`
- Sectigo: `http://timestamp.sectigo.com`
- GlobalSign: `http://timestamp.globalsign.com/tsa/r6advanced1`

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

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RELEASE PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Stage 1: Source Verification                                               │
│  ├── Ensure release branch is clean                                         │
│  ├── All tests pass                                                         │
│  ├── Dependencies are pinned and audited                                    │
│  └── Manual review of changes since last release                            │
│                                                                             │
│  Stage 2: Build                                                             │
│  ├── Fresh environment (no cached state)                                    │
│  ├── Install exact pinned dependencies                                      │
│  ├── Run PyInstaller with uiAccess manifest                                 │
│  ├── Compute SHA256 hash of unsigned executable                             │
│  └── Output: unsigned-nimbus.exe + hash                                     │
│                                                                             │
│  Stage 3: Pre-Sign Verification                                             │
│  ├── Download unsigned artifact                                             │
│  ├── Verify hash matches build output                                       │
│  ├── Optionally: Run unsigned in VM to verify behavior                      │
│  └── Human approval gate                                                    │
│                                                                             │
│  Stage 4: Signing (Manual for EV)                                           │
│  ├── Transfer unsigned executable to signing machine                        │
│  ├── Insert EV token, enter PIN                                             │
│  ├── Sign with timestamp                                                    │
│  ├── Compute SHA256 hash of signed executable                               │
│  └── Output: nimbus.exe (signed) + hash                                     │
│                                                                             │
│  Stage 5: Post-Sign Verification                                            │
│  ├── Verify signature is valid                                              │
│  ├── Verify certificate chain                                               │
│  ├── Verify timestamp is present                                            │
│  ├── Run signed executable in test environment                              │
│  └── Verify uiAccess is working                                             │
│                                                                             │
│  Stage 6: Release                                                           │
│  ├── Upload to GitHub Releases / distribution channel                       │
│  ├── Publish hashes for user verification                                   │
│  └── Update documentation                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### EV Token Management

The EV hardware token is a critical security asset. Compromise of this token means an attacker could sign malware under your organization's identity.

**Operational Guidelines:**

| Aspect | Recommendation |
|--------|---------------|
| **Physical Storage** | Locked drawer/safe when not in use |
| **Access** | Limited to designated release manager(s) |
| **PIN Policy** | Strong PIN, not written down, not shared |
| **Usage Logging** | Log every signing operation (what, when, by whom) |
| **Backup Token** | Some CAs offer backup tokens; store separately |
| **Revocation Plan** | Know how to revoke if token is lost/stolen |

**Signing Ceremony Checklist:**
1. Verify you are signing an artifact built from the intended commit
2. Verify the hash matches CI output
3. Visually confirm the executable size/date are reasonable
4. Insert token, enter PIN
5. Sign with timestamp
6. Remove token immediately after signing
7. Log the signing operation

### Automated OV Signing in CI

For internal testing builds, OV signing can be automated since the key is software-based:

**Security Controls:**
- Store OV private key as encrypted secret in CI (e.g., GitHub Secrets)
- Limit which workflows can access the secret
- Require approval for PRs that modify signing-related code
- Log all signed artifacts
- Consider: Sign only on tagged releases, not every commit

**What to Sign:**
- Release candidates for internal testing
- Beta distributions
- Anything that needs to be tested with uiAccess

**What NOT to Sign with OV:**
- Production releases (use EV)
- Arbitrary feature branches (wasted signature, pollution)

---

## Part 5: Supply Chain Security

### The Risk Landscape

Nimbus depends on open source libraries. Any of these could be compromised:

| Attack Vector | Example | Risk Level |
|--------------|---------|------------|
| Malicious package update | Legitimate package releases malware in new version | HIGH |
| Typosquatting | `pyside6` vs `pyslde6` (typo installs malware) | MEDIUM |
| Compromised maintainer | Maintainer account hacked | MEDIUM |
| Dependency of dependency | Your dep is fine, but its dep is not | MEDIUM |
| Build-time injection | Malware only present in wheel, not source | LOW-MEDIUM |

### Dependency Management Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DEPENDENCY MANAGEMENT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Principle 1: Pin Everything                                                │
│  ├── Use requirements.txt with exact versions (==)                          │
│  ├── Pin transitive dependencies (pip-compile or pip freeze)                │
│  ├── Store lock file in version control                                     │
│  └── Never use >= or ~= in production dependencies                          │
│                                                                             │
│  Principle 2: Verify What You Pin                                           │
│  ├── Review changelogs before updating                                      │
│  ├── Check package download counts and maintainer reputation                │
│  ├── Consider hash verification (pip --require-hashes)                      │
│  └── For critical deps: review source code                                  │
│                                                                             │
│  Principle 3: Update Deliberately                                           │
│  ├── Schedule regular dependency review (monthly?)                          │
│  ├── Don't auto-merge Dependabot PRs                                        │
│  ├── Test thoroughly after any update                                       │
│  └── Consider: Delay updates by 1-2 weeks (let others find problems)        │
│                                                                             │
│  Principle 4: Minimize Dependencies                                         │
│  ├── Each dependency is attack surface                                      │
│  ├── Prefer standard library when reasonable                                │
│  └── Audit: Do we really need this package?                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Vulnerability Scanning

Integrate automated vulnerability scanning into CI:

**Tools to Consider:**
- `pip-audit`: Scans for known vulnerabilities in Python packages
- `safety`: Similar, checks against PyUp.io database
- GitHub Dependabot: Alerts on known vulnerabilities
- Snyk: More comprehensive, includes license scanning

**When to Scan:**
- On every PR (catch issues before merge)
- On every release build (gate releases on no critical vulns)
- Scheduled daily scan of main branch (catch newly disclosed vulns)

**How to Handle Findings:**
- Critical/High: Block release, fix immediately
- Medium: Fix in next release, document exception if blocking
- Low: Address in regular maintenance

### Auditing Key Dependencies

Some dependencies warrant deeper scrutiny due to their privileged position:

| Dependency | Why It Matters | Audit Level |
|------------|---------------|-------------|
| PySide6/PyQt | Full GUI, runs all UI code | Review release notes |
| pyvjoy | Direct hardware access | Review source (small codebase) |
| PyInstaller | Packages everything, runs build-time hooks | Monitor releases |
| Any native extension | Runs compiled code | Highest scrutiny |

### Build Reproducibility

Aspire toward reproducible builds where the same source produces bit-identical output:

**Why:**
- Proves the released binary came from the claimed source
- Multiple parties can verify the build
- Detects build-time injection attacks

**Practical Steps:**
- Pin Python version in CI
- Pin all dependencies with hashes
- Use consistent build environment (Docker or locked runner)
- Document build instructions so others can reproduce

**Note:** Perfect reproducibility is difficult with PyInstaller. Aim for "close enough" - same dependencies, same behavior, even if not bit-identical.

---

## Part 6: Installer and Distribution

### Trusted Location Requirement

uiAccess requires running from `%ProgramFiles%` or `%SystemRoot%`. This has distribution implications:

**Option A: Installer (Recommended)**
- Use an installer (MSI, NSIS, Inno Setup) that:
  - Installs to `C:\Program Files\ATDev\Nimbus\`
  - Creates Start Menu shortcuts
  - Optionally creates Desktop shortcut
- Installer itself should be signed
- User gets familiar "Install to Program Files" experience

**Option B: Portable with Caveat**
- Distribute as ZIP
- README instructs user to extract to Program Files
- Requires admin rights to write to Program Files
- Less user-friendly, but simpler to build

**Recommendation:** Start with Option B for testing, move to Option A for production.

### What to Sign

| Artifact | Sign? | Certificate |
|----------|-------|-------------|
| nimbus.exe | Yes | EV (production) or OV (testing) |
| Installer (setup.exe / .msi) | Yes | Same as above |
| DLLs bundled by PyInstaller | No (covered by main signature) | - |
| Python runtime in bundle | No (covered by main signature) | - |

**Note:** PyInstaller bundles Python and dependencies into the exe or alongside it. The main executable signature covers the integrity of what it loads.

---

## Part 7: Multi-Product Considerations

### Shared Signing Identity

When you acquire OV/EV certificates, they're issued to your organization (ATDev), not to a specific product. This means:

| Product | Can Sign With ATDev Cert? |
|---------|---------------------------|
| Project Nimbus | ✅ Yes |
| Future Product A | ✅ Yes (same cert) |
| Future Product B | ✅ Yes (same cert) |

**Benefit:** One certificate investment covers all current and future ATDev products.

**Responsibility:** Every product signed with this certificate carries your organization's reputation. Ensure every product meets your quality and security standards.

### Shared Infrastructure

Consider building shared release infrastructure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SHARED RELEASE INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Reusable Components                                                 │   │
│  │  ├── Signing scripts (accept any unsigned artifact)                  │   │
│  │  ├── Verification scripts (check signature validity)                 │   │
│  │  ├── CI/CD signing workflows (parameterized by product)              │   │
│  │  ├── Installer templates (brandable per product)                     │   │
│  │  └── Signing ceremony checklist (shared documentation)               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Benefits:                                                                  │
│  • New products inherit security practices                                  │
│  • Consistent user experience across products                               │
│  • Single place to improve signing process                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 8: Testing and Validation

### uiAccess Validation Tests

Before each release, validate uiAccess is working:

**Test 1: Elevated Window Interaction**
1. Launch Task Manager as admin (right-click > Run as administrator)
2. Launch signed Nimbus from Program Files
3. Attempt to use virtual joystick while Task Manager is focused
4. Expected: Input is not blocked by UIPI

**Test 2: SetForegroundWindow Reliability**
1. Open multiple windows
2. Use Nimbus to send input to background windows
3. Verify focus switching is reliable (no "flash taskbar instead of focus" behavior)

**Test 3: Installation Location Enforcement**
1. Copy signed Nimbus to Desktop
2. Run from Desktop
3. Verify uiAccess is NOT active (should behave like unsigned)
4. This confirms Windows is correctly enforcing trusted location requirement

**Test 4: Signature Verification**
1. Right-click nimbus.exe > Properties > Digital Signatures
2. Verify signature is present and valid
3. Verify certificate chain is complete
4. Verify timestamp is present

### Regression Testing

Maintain a test checklist for each release:

```
□ Application launches without crash
□ Virtual joystick sends correct XInput values
□ All buttons work (momentary and toggle modes)
□ Sensitivity curves apply correctly
□ Configuration saves and loads
□ Menu system is functional
□ Game Focus Mode works with test game
□ (Signed build) uiAccess is active
□ (Signed build) Can interact with elevated window
□ Installer works on clean Windows 10
□ Installer works on clean Windows 11
□ No SmartScreen warning (EV only)
```

---

## Part 9: Rollout Phases

### Phase 1: Foundation (Now → OV Certificate)

**Goals:**
- Set up dependency pinning and vulnerability scanning
- Create PyInstaller build with uiAccess manifest
- Test with self-signed certificate on dev machine
- Document uiAccess behavior for developers

**Deliverables:**
- `requirements.txt` with pinned versions
- CI workflow with pip-audit
- PyInstaller spec file with manifest
- Self-signed testing procedure documentation

### Phase 2: OV Integration (After OV Certificate Acquired)

**Goals:**
- Integrate OV signing into CI
- Produce signed internal test builds
- Validate uiAccess works with OV signature
- Build installer framework

**Deliverables:**
- CI workflow that signs with OV
- Signed beta releases for internal testing
- Basic installer (Inno Setup or similar)
- uiAccess validation test suite

### Phase 3: EV Production (Before Public Release)

**Goals:**
- Acquire EV certificate
- Establish signing ceremony process
- Produce first EV-signed production build
- Verify SmartScreen behavior

**Deliverables:**
- EV token operational procedures
- Signing ceremony checklist
- First production release
- Public-facing installer

### Phase 4: Mature Operations (Ongoing)

**Goals:**
- Regular dependency audits
- Automated vulnerability monitoring
- Streamlined release process
- Extend to additional ATDev products

**Deliverables:**
- Monthly dependency review process
- Alerting on new vulnerabilities
- Release runbook
- Shared signing infrastructure for multi-product

---

## Appendix A: Tool Recommendations

These are suggestions to explore, not prescriptions:

| Purpose | Options to Consider |
|---------|---------------------|
| **Code Signing** | SignTool (Windows SDK), osslsigncode |
| **Build Automation** | GitHub Actions, Azure DevOps |
| **Installer Creation** | Inno Setup, NSIS, WiX Toolset |
| **Dependency Pinning** | pip-tools (pip-compile), pip freeze |
| **Vulnerability Scanning** | pip-audit, safety, Snyk |
| **Certificate Authority** | DigiCert, Sectigo, GlobalSign |

---

## Appendix B: Manifest Configuration

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

## Appendix C: Risk Summary

| Risk | Mitigation | Residual Risk |
|------|-----------|---------------|
| Accidental signing of malware | Separation of build/sign, verification steps, human gate | Low |
| EV token theft/loss | Physical security, PIN protection, revocation plan | Low |
| Compromised dependency | Pinning, scanning, delayed updates, audit | Medium |
| Typosquatting attack | Careful review of dependency names | Low |
| Build environment compromise | Fresh builds, no signing keys in build env | Low |
| SmartScreen warning (OV) | EV for production; OV reputation builds over time | Medium (OV only) |

---

## Appendix D: Glossary

| Term | Definition |
|------|------------|
| **uiAccess** | Windows feature allowing assistive tech to interact with elevated windows |
| **UIPI** | User Interface Privilege Isolation - Windows security boundary |
| **OV Certificate** | Organization Validated code signing certificate (software key) |
| **EV Certificate** | Extended Validation code signing certificate (hardware token) |
| **SmartScreen** | Windows feature that warns users about unsigned/unknown software |
| **Timestamping** | Embedding a trusted timestamp in the signature |
| **HSM** | Hardware Security Module (the USB token for EV signing) |

---

## Summary

This strategy provides a path from unsigned development builds to production-ready EV-signed releases with uiAccess support. The key principles are:

1. **Layer your signing**: Self-signed for dev testing → OV for internal/beta → EV for production
2. **Separate build and sign**: Build environment never has signing keys
3. **Verify before signing**: Human gate with hash verification
4. **Pin dependencies**: Exact versions, reviewed updates, vulnerability scanning
5. **Test uiAccess specifically**: Dedicated test cases for elevated window interaction
6. **Document and log**: Signing ceremonies, release checklists, audit trails

The engineering team should shape these principles into specific implementations based on available tooling, team size, and release cadence.
