# Code Signing Guide for Project Nimbus

This guide covers signing Windows executables with an Extended Validation (EV) code signing certificate.

## Overview

EV code signing certificates provide the highest level of trust for Windows applications:
- **Immediate SmartScreen reputation** - No warning dialogs for new releases
- **Hardware-based key storage** - Private key stored on USB token (e.g., SafeNet, YubiKey)
- **Timestamping** - Signatures remain valid even after certificate expires

## Prerequisites

1. **EV Code Signing Certificate** - Obtained from a Certificate Authority (DigiCert, Sectigo, GlobalSign, etc.)
2. **Hardware Token** - USB token containing your private key (provided by CA)
3. **Token Drivers** - SafeNet Authentication Client or equivalent
4. **Windows SDK** - For `signtool.exe`

## Setup

### 1. Install Windows SDK

Download and install the Windows SDK to get `signtool.exe`:
- https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/

After installation, `signtool.exe` is typically located at:
```
C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\signtool.exe
```

### 2. Install Token Drivers

Install the driver software for your hardware token:
- **SafeNet tokens**: SafeNet Authentication Client
- **YubiKey**: YubiKey Smart Card Minidriver

### 3. Verify Certificate

Insert your token and verify the certificate is recognized:
```powershell
certutil -csp "eToken Base Cryptographic Provider" -key
```

Or list certificates:
```powershell
certutil -store -user My
```

## Signing Process

### Manual Signing

Sign a single executable:
```powershell
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a "dist\Project-Nimbus.exe"
```

Parameters:
- `/tr` - RFC 3161 timestamp server URL
- `/td sha256` - Timestamp digest algorithm
- `/fd sha256` - File digest algorithm  
- `/a` - Auto-select the best signing certificate

### Signing with Specific Certificate

If you have multiple certificates, specify by SHA1 thumbprint:
```powershell
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /sha1 YOUR_CERT_THUMBPRINT "dist\Project-Nimbus.exe"
```

### Verify Signature

Confirm the executable is properly signed:
```powershell
signtool verify /pa /v "dist\Project-Nimbus.exe"
```

## Automated Build & Sign

### sign_exe.bat

Create this script in `build_tools/` for automated signing:

```batch
@echo off
REM Code signing script for Project Nimbus
REM Requires EV certificate on hardware token

set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
set TIMESTAMP_URL=http://timestamp.digicert.com
set EXE_PATH=dist\Project-Nimbus.exe

echo Signing %EXE_PATH%...

%SIGNTOOL% sign /tr %TIMESTAMP_URL% /td sha256 /fd sha256 /a "%EXE_PATH%"

if errorlevel 1 (
    echo ERROR: Signing failed!
    echo Make sure your hardware token is connected and unlocked.
    exit /b 1
)

echo Verifying signature...
%SIGNTOOL% verify /pa "%EXE_PATH%"

if errorlevel 1 (
    echo ERROR: Signature verification failed!
    exit /b 1
)

echo.
echo SUCCESS: %EXE_PATH% is signed and verified.
```

### Complete Build & Sign Workflow

1. Build the executable:
   ```powershell
   cd build_tools
   .\build_exe.bat
   ```

2. Sign the executable:
   ```powershell
   .\sign_exe.bat
   ```

3. Verify and distribute `dist\Project-Nimbus.exe`

## Timestamp Servers

Use a reliable timestamp server to ensure signatures remain valid:

| Provider   | URL                                    |
|------------|----------------------------------------|
| DigiCert   | http://timestamp.digicert.com          |
| Sectigo    | http://timestamp.sectigo.com           |
| GlobalSign | http://timestamp.globalsign.com/tsa/r6advanced1 |

## Troubleshooting

### "No certificates were found"
- Ensure hardware token is connected
- Check token PIN/password
- Verify certificate is not expired: `certutil -store -user My`

### "The specified timestamp server could not be reached"
- Check internet connection
- Try a different timestamp server
- Verify firewall isn't blocking outbound HTTPS

### SmartScreen Still Shows Warning
- EV certificates provide **immediate** reputation (no warning)
- If warnings persist, verify the signature: `signtool verify /pa /v file.exe`
- Check that timestamp was applied successfully

### Token PIN Dialog Not Appearing
- Some tokens require middleware (SafeNet Authentication Client)
- Try running command prompt as Administrator
- Check Windows Credential Manager for cached PINs

## Security Best Practices

1. **Never share token PIN** - Treat it like a password
2. **Lock token when not signing** - Remove USB when done
3. **Use dedicated signing machine** - Minimize attack surface
4. **Audit signatures** - Keep logs of what was signed and when
5. **Backup certificate info** - Store certificate thumbprint and CA contact securely

## CI/CD Considerations

For automated pipelines, EV signing is challenging because:
- Hardware token must be physically connected
- PIN entry may be required interactively

Options:
1. **Manual signing step** - Build in CI, sign locally before release
2. **Cloud HSM** - Some CAs offer cloud-based signing (Azure SignTool, AWS CloudHSM)
3. **Self-hosted runner** - Dedicated machine with token connected

## Release Checklist

- [ ] Version updated in `src/__init__.py`
- [ ] Version updated in `build_tools/version_info.txt`
- [ ] Build executable: `build_exe.bat`
- [ ] Sign executable: `sign_exe.bat`
- [ ] Verify signature: `signtool verify /pa dist\Project-Nimbus.exe`
- [ ] Test on clean Windows machine
- [ ] Create GitHub release with signed executable
- [ ] Tag release in git: `git tag v1.0.0`

## References

- [Microsoft SignTool Documentation](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [DigiCert EV Code Signing Guide](https://www.digicert.com/kb/code-signing/)
- [Windows SmartScreen](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-smartscreen/)
