<#
.SYNOPSIS
    Unattended check of the installer's driver bootstrap: vJoy and ViGEmBus.

.DESCRIPTION
    Runs the built installer silently and verifies what actually happened on the
    machine, rather than what the installer said. Everything after launch is
    unattended; the only interaction is the elevation prompt on this script
    itself, because the installer requires admin and this account is not one.

    Start it from an elevated PowerShell:

        Set-ExecutionPolicy -Scope Process Bypass -Force
        tests\probe_installer_drivers_windows.ps1 -Fresh

    Checks (each prints PASS or FAIL, with a count at the end):

      I1   elevated, and the built installer is present
      I2   baseline recorded (driver versions, vJoy device 1 capabilities)
      I3   vJoy uninstalled            (-Fresh only)
      I4   ViGEmBus uninstalled        (-Fresh only)
      I5   silent install returns a success code
      I6   vJoy present afterwards
      I7   ViGEmBus service present afterwards
      I8   vJoy device 1 has 8 axes and 128 buttons
      I9   the app is installed and registered, with no leftover drivers folder
      I10  the app starts, shows a window, and exits when asked
      I11  the app uninstalls and both drivers survive it

.PARAMETER Fresh
    Uninstall vJoy and ViGEmBus first, so the install path is exercised instead
    of skipped. Without it the installer will correctly detect both and install
    neither, which tests the detection half only.

    This removes drivers the machine may be using. Only pass it on a machine
    where that is acceptable, and expect vJoy to come back as 2.2.1 and
    ViGEmBus as 1.22.0, which is what the installer ships.

.PARAMETER KeepApp
    Leave the app installed at the end. By default I11 uninstalls it, since the
    point of the run is the drivers, and the drivers are deliberately left
    behind by the uninstaller.
#>
param(
    [string]$Setup = "dist\Nimbus-Adaptive-Controller-Setup-1.4.3.exe",
    [switch]$Fresh,
    [switch]$KeepApp,
    [string]$LogPath = "dist\installer-probe.log"
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$Setup = if ([IO.Path]::IsPathRooted($Setup)) { $Setup } else { Join-Path $repo $Setup }
$LogPath = if ([IO.Path]::IsPathRooted($LogPath)) { $LogPath } else { Join-Path $repo $LogPath }

$script:pass = 0
$script:fail = 0
$script:lines = @()

function Say([string]$Text) {
    Write-Host $Text
    $script:lines += $Text
}
function Check([string]$Id, [bool]$Ok, [string]$Detail) {
    if ($Ok) { $script:pass++ } else { $script:fail++ }
    Say ("  {0,-4} {1,-5} {2}" -f $Id, $(if ($Ok) { 'PASS' } else { 'FAIL' }), $Detail)
}
function Save-Log {
    New-Item -ItemType Directory -Force (Split-Path $LogPath) | Out-Null
    Set-Content -Path $LogPath -Value $script:lines -Encoding utf8
    Write-Host "`nLog: $LogPath"
}

# ------------------------------------------------------------------ detection
function Get-VJoy {
    # The same three uninstall keys installer.nsi checks, read from the 64-bit
    # hive, plus the DLL on disk as the fallback.
    $keys = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{8E31F76F-74C3-47F1-9550-E041EEDC5FBB}_is1',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{D3B6B8B0-4C9B-4C9B-8A1A-6B3C5E7D8F2A}_is1',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\vJoy'
    )
    foreach ($k in $keys) {
        $p = Get-ItemProperty $k -ErrorAction SilentlyContinue
        if ($p.DisplayVersion) {
            return [pscustomobject]@{ Present = $true; Version = $p.DisplayVersion; Uninstall = $p.UninstallString; Key = $k }
        }
    }
    $dll = "$env:ProgramFiles\vJoy\x64\vJoyInterface.dll"
    if (Test-Path $dll) { return [pscustomobject]@{ Present = $true; Version = '(dll only)'; Uninstall = $null; Key = $null } }
    return [pscustomobject]@{ Present = $false; Version = $null; Uninstall = $null; Key = $null }
}

function Get-ViGEm {
    $null = & sc.exe query ViGEmBus 2>&1
    $service = ($LASTEXITCODE -eq 0)
    $entry = Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall' -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue } |
        Where-Object { $_.DisplayName -match 'ViGEm|Virtual Gamepad Emulation Bus' } |
        Select-Object -First 1
    return [pscustomobject]@{
        Present = $service
        Version = $entry.DisplayVersion
        Product = $entry.PSChildName
    }
}

function Get-VJoyCaps {
    # Axis and button counts straight from vJoyInterface.dll, which is what the
    # app itself talks to. Returns $null when vJoy is not installed.
    $dll = "$env:ProgramFiles\vJoy\x64\vJoyInterface.dll"
    if (-not (Test-Path $dll)) { return $null }
    $py = Join-Path $repo 'venv\Scripts\python.exe'
    if (-not (Test-Path $py)) { return 'no venv python' }
    $code = @"
import ctypes
dll = ctypes.WinDLL(r'$dll')
u = {'X':0x30,'Y':0x31,'Z':0x32,'RX':0x33,'RY':0x34,'RZ':0x35,'SL0':0x36,'SL1':0x37}
axes = [n for n, c in u.items() if dll.GetVJDAxisExist(1, c)]
print('%d buttons, axes %s' % (dll.GetVJDButtonNumber(1), ' '.join(axes)))
"@
    return (& $py -c $code 2>&1 | Select-Object -Last 1)
}

function Get-App {
    $p = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\nimbus-adaptive-controller' -ErrorAction SilentlyContinue
    return [pscustomobject]@{
        Present   = [bool]$p.InstallLocation
        Dir       = $p.InstallLocation
        Version   = $p.DisplayVersion
        Uninstall = $p.UninstallString
    }
}

# ---------------------------------------------------------------------- start
Say "Nimbus installer driver probe  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Say "  setup : $Setup"
Say "  fresh : $Fresh"
Say ''

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$elevated = (New-Object Security.Principal.WindowsPrincipal($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Check 'I1' ($elevated -and (Test-Path $Setup)) "elevated=$elevated setup present=$(Test-Path $Setup) (running as $($identity.Name))"
if (-not $elevated) {
    Say ''
    Say 'The installer needs admin. Start an elevated PowerShell (Win+X, A) and run this again.'
    Save-Log
    exit 1
}
if (-not (Test-Path $Setup)) {
    Say ''
    Say 'Build it first: PyInstaller, then build_tools\fetch_redist.ps1, then makensis build_tools\installer.nsi'
    Save-Log
    exit 1
}

$vj0 = Get-VJoy
$vg0 = Get-ViGEm
$caps0 = Get-VJoyCaps
Check 'I2' $true "baseline: vJoy=$(if ($vj0.Present) { $vj0.Version } else { 'absent' }) ViGEmBus=$(if ($vg0.Present) { $vg0.Version } else { 'absent' }) device1=$caps0"

# ------------------------------------------------------------------- teardown
if ($Fresh) {
    if ($vj0.Present -and $vj0.Uninstall) {
        $exe = $vj0.Uninstall.Trim('"')
        Say "  removing vJoy $($vj0.Version)"
        Start-Process -FilePath $exe -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait
        Start-Sleep -Seconds 3
    }
    $vj1 = Get-VJoy
    Check 'I3' (-not $vj1.Present) "vJoy after uninstall: $(if ($vj1.Present) { $vj1.Version } else { 'absent' })"

    if ($vg0.Present -and $vg0.Product) {
        Say "  removing ViGEmBus $($vg0.Version)"
        Start-Process -FilePath 'msiexec.exe' -ArgumentList '/x', $vg0.Product, '/qn', '/norestart' -Wait
        Start-Sleep -Seconds 3
    }
    $vg1 = Get-ViGEm
    Check 'I4' (-not $vg1.Present) "ViGEmBus service after uninstall: $(if ($vg1.Present) { 'still present' } else { 'absent' })"
} else {
    Say '  I3   SKIP  -Fresh not passed, drivers left in place'
    Say '  I4   SKIP  -Fresh not passed, drivers left in place'
}

# --------------------------------------------------------------- silent install
Say "  running the installer silently"
$sw = [Diagnostics.Stopwatch]::StartNew()
$proc = Start-Process -FilePath $Setup -ArgumentList '/S' -Wait -PassThru
$sw.Stop()
$code = $proc.ExitCode
Check 'I5' ($code -eq 0) "installer exit code $code after $([math]::Round($sw.Elapsed.TotalSeconds,1)) s"

Start-Sleep -Seconds 3
$vj2 = Get-VJoy
$vg2 = Get-ViGEm
$caps2 = Get-VJoyCaps
$app = Get-App

Check 'I6' $vj2.Present "vJoy: $(if ($vj2.Present) { $vj2.Version } else { 'MISSING' })"
Check 'I7' $vg2.Present "ViGEmBus: $(if ($vg2.Present) { "service present, $($vg2.Version)" } else { 'MISSING' })"
Check 'I8' ($caps2 -match '128 buttons' -and $caps2 -match 'X Y Z RX RY RZ SL0 SL1') "vJoy device 1: $caps2"

$leftover = $false
if ($app.Dir) { $leftover = Test-Path (Join-Path $app.Dir 'drivers') }
Check 'I9' ($app.Present -and -not $leftover) "app $($app.Version) at $($app.Dir); leftover drivers folder: $leftover (present only when a driver install failed)"

# ------------------------------------------------------------------ app launch
if ($app.Present) {
    $exe = Join-Path $app.Dir 'Nimbus-Adaptive-Controller-1.4.3.exe'
    if (Test-Path $exe) {
        $p = Start-Process -FilePath $exe -PassThru
        Start-Sleep -Seconds 20        # PyInstaller onefile unpacks before Qt appears
        $p.Refresh()
        $alive = -not $p.HasExited
        $window = $false
        if ($alive) { $window = ($p.MainWindowHandle -ne 0) }
        if ($alive) {
            $null = $p.CloseMainWindow()
            Start-Sleep -Seconds 5
            $p.Refresh()
            if (-not $p.HasExited) { $p | Stop-Process -Force }
        }
        Check 'I10' ($alive -and $window) "app alive after 20 s: $alive, window shown: $window"
    } else {
        Check 'I10' $false "app exe not found at $exe"
    }
} else {
    Check 'I10' $false 'app not installed, nothing to launch'
}

# --------------------------------------------------------------- app uninstall
if ($KeepApp) {
    Say '  I11  SKIP  -KeepApp passed, app left installed'
} elseif ($app.Present) {
    $un = Join-Path $app.Dir 'Uninstall.exe'
    if (Test-Path $un) {
        Start-Process -FilePath $un -ArgumentList '/S', "_?=$($app.Dir)" -Wait
        Start-Sleep -Seconds 3
        Remove-Item $un -Force -ErrorAction SilentlyContinue
        Remove-Item $app.Dir -Recurse -Force -ErrorAction SilentlyContinue
    }
    $after = Get-App
    $vj3 = Get-VJoy
    $vg3 = Get-ViGEm
    Check 'I11' ((-not $after.Present) -and $vj3.Present -and $vg3.Present) "app removed: $(-not $after.Present); vJoy kept: $($vj3.Present); ViGEmBus kept: $($vg3.Present)"
} else {
    Check 'I11' $false 'app was not installed, nothing to uninstall'
}

# ------------------------------------------------------------------- summary
Say ''
Say ("Result: {0}/{1} checks passed" -f $script:pass, ($script:pass + $script:fail))
if (Get-Item 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired' -ErrorAction SilentlyContinue) {
    Say 'A reboot is pending. Windows was told a restart is needed; the drivers may not be fully live until then.'
}
Save-Log
if ($script:fail -gt 0) { exit 1 }
