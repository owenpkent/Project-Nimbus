<#
.SYNOPSIS
    Downloads the third-party driver setups that installer.nsi bundles.

.DESCRIPTION
    Nimbus needs two drivers it does not own: vJoy (DirectInput output) and
    ViGEmBus (Xbox 360 output). The installer carries both so a user with a bad
    connection, a proxy, or no connection at all still ends up with working
    drivers, and so a moved or renamed release asset can never break an
    installer that already shipped.

    Each file is pinned by SHA-256 and checked for a valid Authenticode
    signature from the expected publisher before it is accepted. A file that
    fails either check is deleted, not kept.

    Run this before makensis. The output lands in build_tools\redist\, which is
    gitignored: these are third-party binaries, not our source.

.PARAMETER Force
    Re-download even when a verified copy is already present.
#>
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$redist = Join-Path $PSScriptRoot 'redist'

# Both projects are frozen: ViGEmBus was archived on 2023-11-02 with 1.22.0 as
# its final release, and vJoy 2.2.1.1 is the current njz3 build. Bumping either
# means a new hash here and a new version in installer.nsi.
$items = @(
    @{
        Name      = 'vJoySetup-2.2.1-signed.exe'
        Url       = 'https://github.com/njz3/vJoy/releases/download/v2.2.1.1/vJoySetup-2.2.1-signed.exe'
        Sha256    = '0C599290DA9AB17ED189DEB1DB20D8BB2688D15173FE464D485C203032EEEF8D'
        Signer    = 'On-site Dental Systems'
        Purpose   = 'vJoy 2.2.1 (Inno Setup, silent flags /VERYSILENT /SUPPRESSMSGBOXES /NORESTART)'
    },
    @{
        Name      = 'ViGEmBus_1.22.0_x64_x86_arm64.exe'
        Url       = 'https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe'
        Sha256    = '89220A7865076B342892F98865F3499FB7C4CFD673159E89D352C360FD014C6A'
        Signer    = 'Nefarius Software Solutions'
        Purpose   = 'ViGEmBus 1.22.0 (Advanced Installer bootstrapper, silent flags /exenoui /qn /norestart)'
    }
)

function Test-Redist($Item, $Path) {
    if (-not (Test-Path $Path)) { return $false }
    $hash = (Get-FileHash $Path -Algorithm SHA256).Hash
    if ($hash -ne $Item.Sha256) {
        Write-Warning "$($Item.Name): SHA-256 is $hash, expected $($Item.Sha256)"
        return $false
    }
    $sig = Get-AuthenticodeSignature $Path
    if ($sig.Status -ne 'Valid') {
        Write-Warning "$($Item.Name): Authenticode status is $($sig.Status)"
        return $false
    }
    if ($sig.SignerCertificate.Subject -notlike "*$($Item.Signer)*") {
        Write-Warning "$($Item.Name): signed by '$($sig.SignerCertificate.Subject)', expected $($Item.Signer)"
        return $false
    }
    return $true
}

New-Item -ItemType Directory -Force $redist | Out-Null
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

foreach ($item in $items) {
    $path = Join-Path $redist $item.Name
    if (-not $Force -and (Test-Redist $item $path)) {
        Write-Host "OK (cached)  $($item.Name)"
        continue
    }
    if (Test-Path $path) { Remove-Item $path -Force }

    Write-Host "Downloading   $($item.Name)"
    Write-Host "              $($item.Purpose)"
    $progress = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'   # the progress bar makes this an order of magnitude slower
    try {
        Invoke-WebRequest -Uri $item.Url -OutFile $path -UseBasicParsing
    } finally {
        $ProgressPreference = $progress
    }

    if (-not (Test-Redist $item $path)) {
        Remove-Item $path -Force -ErrorAction SilentlyContinue
        throw "$($item.Name) failed verification and was deleted. Do not build an installer around an unverified driver setup."
    }
    Write-Host "OK            $($item.Name)"
}

Write-Host ''
Write-Host "Redist ready in $redist"
Get-ChildItem $redist -File | ForEach-Object { "  {0,-36} {1,10:N0} bytes" -f $_.Name, $_.Length }
Write-Host ''
Write-Host 'Next: build the app with PyInstaller, then makensis build_tools\installer.nsi'
