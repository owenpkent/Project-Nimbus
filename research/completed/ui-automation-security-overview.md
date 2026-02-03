# UI Automation Security Considerations (UIAccess)

This note summarizes Microsoft’s guidance on the security model around Windows UI Automation for assistive technologies, with emphasis on `uiAccess` and integrity level (IL) boundaries.

Source:
- https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-securityoverview

---

## What UI Automation enables (and why it’s security-sensitive)

Assistive technology (AT) apps (screen readers, on-screen keyboards, overlays, switch-control UIs, etc.) typically need to:

- Read UI state from other apps (names, values, control structure).
- Programmatically “drive” other apps (invoke controls, set values, send input).

That inherently crosses process boundaries.

Windows treats cross-process UI interaction as a security boundary because it can be used to:

- Spy on privileged UI.
- Simulate user input into protected dialogs (credential prompts, UAC consent, etc.).

---

## Integrity levels, UIPI, and protected UI

Windows uses integrity levels (IL) + User Interface Privilege Isolation (UIPI) to reduce “shatter attacks” where a lower-privileged process sends messages/input to a higher-privileged one.

Key implications:

- A normal desktop app typically runs at **medium IL**.
- Many security-relevant UI surfaces run higher to block cross-process interaction:
  - **UAC consent UI** uses a higher IL to prevent simulated clicks/keystrokes by malware.
  - The **logon screen** is similarly protected.

If your AT app needs to interact with these protected UI surfaces, it must be treated as trusted by Windows.

---

## `uiAccess`: what it is

`uiAccess` is a special application manifest flag intended specifically for trusted assistive technologies.

Enabling it is part of what allows an AT app to:

- Interact with UI in higher-IL processes (subject to the rules below).
- Be “always available” by being able to appear topmost in z-order (important for AT overlays).

`uiAccess` alone does **not** let a process bypass every privilege boundary; it is a controlled mechanism with strict requirements.

---

## Access behavior by scenario (from the Microsoft doc)

The doc describes these constraints:

- If an app **does not** have `uiAccess`:
  - It starts at **medium IL** and cannot access elevated (“medium+” / “high”) process UI.

- If an app **has** `uiAccess` but is launched by a **non-admin** user:
  - It starts at **“medium+” IL** but still cannot access **high IL** UI (e.g., apps started via “Run as administrator”).

- If an app **has** `uiAccess` and is launched by an **admin** user:
  - It starts at **high IL** and can access elevated UI (because it matches the target’s IL).

Important limitation:

- None of these scenarios provide access to UI running under **system IL**.
- Accessing system-IL UI is only possible if the process is launched under SYSTEM on the **UAC secure desktop**; setting `uiAccess` has no effect in that context.

---

## Requirements for `uiAccess` to be honored

To use `uiAccess`, Microsoft’s guidance is:

- Your app must actually be an assistive technology:
  - It needs to display/interact with/reflect info from other apps for an accessibility scenario and/or needs to run topmost for that scenario.

- Your app must be **digitally signed**.

- Your app must be installed in a **trusted/secure location** that requires a UAC prompt for modification (for example, `Program Files`).

- Your app must include a manifest with `uiAccess="true"`.

If any of these are missing, Windows may silently treat the app like a normal medium-IL app.

Microsoft also notes:

- `uiAccess` should **not** be used by non-AT apps, nor by AT apps for UI unrelated to their accessibility scenario.
- `uiAccess` is **not available** for UWP apps.

---

## Manifest snippet

From the Microsoft page (example only):

```xml
<trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
  <security>
    <requestedPrivileges>
      <requestedExecutionLevel level="highestAvailable" uiAccess="true" />
    </requestedPrivileges>
  </security>
</trustInfo>
```

Notes:

- `uiAccess` defaults to `false`.
- If `uiAccess` is omitted (or there is no manifest), the app cannot gain access to protected UI.

---

## Why this is relevant to Project Nimbus

Project Nimbus’s core accessibility problem is enabling reliable interaction with games and the Windows desktop without requiring keyboard shortcuts (Alt+Tab) or assistance.

`uiAccess` is relevant because it can:

- Reduce focus/foreground restrictions and improve topmost overlay behavior.
- Allow interaction with elevated UI surfaces (within the allowed IL rules).

However, it also adds release/ops requirements:

- Code signing.
- Installation into Program Files (or another secure location).
- A build pipeline that embeds the manifest correctly.

See also:

- `research/roadmap/uiaccess-signing-strategy.md`
- `research/roadmap/uiaccess-signing-checklist.md`

---

## Additional Windows UI Automation / accessibility resources

### Core UI Automation docs

- **UI Automation (Win32) landing page**
  - https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32

- **UI Automation Fundamentals**
  - https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiautocore-overview

- **UI Automation Overview (Win32)**
  - https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview

- **UI Automation (.NET Framework) Overview**
  - https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/ui-automation-overview

### Inspection and debugging tools (high leverage for AT + automation)

- **Inspect (Inspect.exe) — Windows SDK UIA inspection tool**
  - https://learn.microsoft.com/en-us/windows/win32/winauto/inspect-objects

- **Accessibility Insights for Windows (UIA-based auditing + inspection)**
  - https://accessibilityinsights.io/docs/windows/overview/

### Legacy/interop context

- **Legacy accessibility and automation tech (MSAA ↔ UIA)**
  - https://learn.microsoft.com/en-us/windows/win32/accessibility/accessibility-legacy

- **MSAA vs UI Automation compared**
  - https://learn.microsoft.com/en-us/windows/win32/winauto/microsoft-active-accessibility-and-ui-automation-compared

### Security / deployment adjacent

- **UAC policy: only elevate UIAccess apps installed in secure locations**
  - https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/user-account-control-only-elevate-uiaccess-applications-that-are-installed-in-secure-locations

