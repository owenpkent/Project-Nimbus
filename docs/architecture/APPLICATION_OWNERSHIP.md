# Application Ownership Restructuring

This first-stage restructuring separates ownership from the Qt input facade.
It is deliberately not an implementation of every finding from the September
2026 architecture review. Driver behavior and profile activation semantics need
separate, explicitly reviewed changes.

## Runtime Structure

```text
qt_qml_app.main
  ControllerConfig
    ProfileRepository: profile files, safe IDs, atomic replacement
  ApplicationServices: Qt lifetime owner
    TelemetryClient
    CloudClient
    UpdateChecker
  ControllerBridge: the QML context object
    ControllerOutput: backend instances and selection policy
      VJoyInterface
      ViGEmInterface
    injected ApplicationServices
    existing shaping, smoothing, and Game Mode integration
```

### Controller Output

`src/controller_output.py` owns backend construction, reuse, and selection.
Constructors are injected, so selection can be tested without Qt or driver
imports. The bridge delegates selection to this owner while retaining its
existing `_vjoy`, `_vigem`, and `_use_vigem` accessors for the Windows probes and
Game Mode implementation.

This owner does not write input, reset devices, or serialize gamepad reports.
Selection intentionally retains the previous package-availability policy,
including its connection-failure limitations. Shaping still happens in the
bridge, and no kernel/client contract or input rate is changed.

### Profile Repository

`src/profile_repository.py` owns profile listing, loading, saving, duplication
IDs, deletion, reset, timestamps, and bundled-default installation. Configuration
retains the existing public CRUD methods and delegates file operations to the
repository. Cloud merge uses the same boundary rather than writing filenames
it constructs itself.

Identifiers must represent a single valid Windows filename stem and resolve
inside the selected directory. Invalid IDs and non-object JSON documents are
rejected. Writes use a temporary file in the destination directory followed by
`os.replace`, so a serialization or replacement failure preserves the old file.
Layout Save As generates a unique safe ID and reports the actual save result.

The profile JSON schema, unknown fields, per-machine settings location, profile
overlay rules, cloud conflict policy, and bundled-profile retirement policy are
unchanged. This is not yet full widget-schema validation or a migration system.

### Application Services

`src/application_services.py` constructs cloud, telemetry, and updater instances
once, parents them explicitly, and provides idempotent shutdown. The bridge
receives this owner as a constructor argument; it never searches its QObject
parent for services.

The existing account, privacy, and update QML components access Qt properties,
slots, and signals on `controller`. Service implementation objects are no longer
separate context properties in the production entry point. Bridge construction
without services remains supported for controller-only probes.

Privacy commands now reach the live telemetry client, not just stored config.
Crash-report consent updates the timer, and the Sentry callback rejects events
after consent is revoked. Collection defaults, event fields, endpoints, and
credential handling are unchanged.

The updater's manifest signal no longer shadows `QThread.finished`. Shutdown
stops timers and waits for an in-flight update request before QObject teardown.
This wait can last until the existing HTTP timeout. Production startup also
shuts services down on QML load failure. This change does not add new menu items
for the optional account/privacy/update components.

## Verification

Run these from the repository root with the project virtual environment:

```powershell
.\venv\Scripts\python.exe -m unittest tests.test_controller_output tests.test_profile_repository tests.test_application_services tests.test_bridge_services -v
.\venv\Scripts\python.exe tests\test_stick_shaping.py
```

The new suite uses standard-library `unittest`, temporary profile directories,
fake backends and services, and offscreen Qt with the Basic control style. It
checks backend reuse, unchanged selection/input policy, file containment,
failure recovery, configuration CRUD, cloud persistence, service lifetime,
consent changes, Qt metadata, component bindings, and production QML startup.
It does not use real credentials, network requests, cursor hooks, or drivers.

Native module stubs are restored individually. Restoring the complete
`sys.modules` mapping would unload newly imported compiled dependencies such as
NumPy and make subsequent startup imports unsafe.

## Follow-Up Work

1. Define and approve neutralization policy for profile/output switches, widget
   destruction, Game Mode exit, and application shutdown. Add backend contract
   tests before changing live input behavior.
2. Give Game Mode and normal input one serialized report writer. Preserve or
   explicitly revise the current pulse values and emergency-stop behavior.
3. Extract Game Mode lifecycle coordination from the bridge once those state
   transitions have hardware-backed regression coverage.
4. Define connection-based fallback and capabilities independently of profile
   layout, then validate both Windows backends.
5. Replace profile overlays and disk/cache mixtures with a validated active
   snapshot. Add widget-schema validation and migrations without losing custom
   fields or user-created layouts.
6. Migrate per-machine settings from the executable working directory to the
   existing user-data directory, with an explicit precedence and rollback rule.
7. Move cloud and telemetry network operations off the UI thread. Authentication,
   sync, and telemetry HTTP calls remain synchronous in this stage.
8. Review cloud timestamp/conflict handling, callback delivery, and cached-profile
   refresh separately. These are not fixed by extracting file persistence.

No driver installation, real input probes, kernel stress tests, WDK checks, or
CodeQL run is claimed by this stage.