; Nimbus Adaptive Controller NSIS Installer Script
; Windows Installer Best Practices (modeled after GitConnect Pro)
; Features: wizard UI, admin/user choice, running app check, previous version detection, shortcut options

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"

; ---- General ----
!define PRODUCT_NAME "Nimbus Adaptive Controller"
!define PRODUCT_FILENAME "Nimbus-Adaptive-Controller"
!define PRODUCT_EXE "${PRODUCT_FILENAME}-1.4.3.exe"
!define PRODUCT_PUBLISHER "Owen Kent"
!define PRODUCT_VERSION "1.4.3"
!define PRODUCT_GUID "nimbus-adaptive-controller"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_GUID}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\dist\${PRODUCT_FILENAME}-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_UNINST_KEY}" "InstallLocation"
RequestExecutionLevel admin  ; Required for Program Files install
SetCompressor /SOLID lzma
BrandingText "${PRODUCT_NAME} v${PRODUCT_VERSION}"

; Variables for shortcut options
Var CreateDesktopShortcut
Var CreateStartMenuShortcut
Var InstallVJoy
Var VJoyInstalled
Var InstallViGEm
Var ViGEmInstalled
Var KeepProfiles

; ---- MUI Settings ----
!define MUI_ICON "Nimbus-Adaptive-Controller.ico"
!define MUI_UNICON "Nimbus-Adaptive-Controller.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${PRODUCT_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${PRODUCT_NAME} v${PRODUCT_VERSION} on your computer.$\r$\n$\r$\n${PRODUCT_NAME} is a free, open-source modular virtual controller designed for accessibility.$\r$\n$\r$\nRequired virtual controller drivers will be offered on the next page if not already installed.$\r$\n$\r$\nClick Next to continue."

; vJoy detection registry keys — Headsoft original and njz3 fork both covered
!define VJOY_KEY_HEADSOFT "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{8E31F76F-74C3-47F1-9550-E041EEDC5FBB}_is1"
!define VJOY_KEY_FORK    "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{D3B6B8B0-4C9B-4C9B-8A1A-6B3C5E7D8F2A}_is1"
!define VJOY_KEY_PLAIN   "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\vJoy"

; Finish page — MUI2 requires MUI_FINISHPAGE_RUN to be defined (even as a dummy)
; to show the checkbox; the actual launch is overridden by RUN_FUNCTION.
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApplication
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${PRODUCT_NAME}"

; ---- Custom Page for Shortcuts ----
Var Dialog
Var DesktopCheckbox
Var StartMenuCheckbox

Function ShortcutOptionsPage
    !insertmacro MUI_HEADER_TEXT "Shortcut Options" "Choose which shortcuts to create."
    
    nsDialogs::Create 1018
    Pop $Dialog
    ${If} $Dialog == error
        Abort
    ${EndIf}
    
    ${NSD_CreateLabel} 0 0 100% 20u "Select which shortcuts you would like to create:"
    Pop $0
    
    ${NSD_CreateCheckbox} 20u 30u 100% 12u "Create Desktop shortcut"
    Pop $DesktopCheckbox
    ${NSD_Check} $DesktopCheckbox  ; Checked by default
    
    ${NSD_CreateCheckbox} 20u 50u 100% 12u "Create Start Menu shortcut"
    Pop $StartMenuCheckbox
    ${NSD_Check} $StartMenuCheckbox  ; Checked by default
    
    nsDialogs::Show
FunctionEnd

Function ShortcutOptionsLeave
    ${NSD_GetState} $DesktopCheckbox $CreateDesktopShortcut
    ${NSD_GetState} $StartMenuCheckbox $CreateStartMenuShortcut
FunctionEnd

; ---- Custom Page for Driver Installation (vJoy + ViGEmBus) ----
Var VJoyDialog
Var VJoyCheckbox
Var VJoyStatusLabel
Var ViGEmCheckbox
Var ViGEmStatusLabel

Function VJoyOptionsPage
    !insertmacro MUI_HEADER_TEXT "Virtual Controller Drivers" "vJoy and ViGEmBus are required for controller emulation."
    
    nsDialogs::Create 1018
    Pop $VJoyDialog
    ${If} $VJoyDialog == error
        Abort
    ${EndIf}
    
    ; Title
    ${NSD_CreateLabel} 0 0 100% 14u "These drivers let ${PRODUCT_NAME} create virtual game controllers:"
    Pop $0
    
    ; ---- vJoy Section ----
    ${NSD_CreateGroupBox} 0 18u 100% 40u "vJoy (DirectInput controller)"
    Pop $0
    
    ; Check all known vJoy registry locations
    ; MUST use SetRegView 64 — vJoy is a 64-bit install and registers in the
    ; native hive; NSIS 32-bit would otherwise silently read WOW6432Node and miss it.
    StrCpy $VJoyInstalled 0
    SetRegView 64
    ReadRegStr $0 HKLM "${VJOY_KEY_HEADSOFT}" "DisplayVersion"
    ${If} $0 != ""
        StrCpy $VJoyInstalled 1
    ${EndIf}
    ${If} $VJoyInstalled == 0
        ReadRegStr $0 HKCU "${VJOY_KEY_HEADSOFT}" "DisplayVersion"
        ${If} $0 != ""
            StrCpy $VJoyInstalled 1
        ${EndIf}
    ${EndIf}
    ${If} $VJoyInstalled == 0
        ReadRegStr $0 HKLM "${VJOY_KEY_FORK}" "DisplayVersion"
        ${If} $0 != ""
            StrCpy $VJoyInstalled 1
        ${EndIf}
    ${EndIf}
    ${If} $VJoyInstalled == 0
        ReadRegStr $0 HKLM "${VJOY_KEY_PLAIN}" "DisplayVersion"
        ${If} $0 != ""
            StrCpy $VJoyInstalled 1
        ${EndIf}
    ${EndIf}
    SetRegView lastused
    ; Fallback: check if vJoyInterface.dll exists on disk
    ${If} $VJoyInstalled == 0
        IfFileExists "$PROGRAMFILES\vJoy\x64\vJoyInterface.dll" 0 +2
            StrCpy $VJoyInstalled 1
    ${EndIf}
    ${If} $VJoyInstalled == 0
        IfFileExists "$PROGRAMFILES64\vJoy\x64\vJoyInterface.dll" 0 +2
            StrCpy $VJoyInstalled 1
    ${EndIf}
    
    ${If} $VJoyInstalled == 1
        StrCpy $InstallVJoy 0
        ${If} $0 != ""
            ${NSD_CreateLabel} 10u 32u 90% 12u "Installed (v$0)"
        ${Else}
            ${NSD_CreateLabel} 10u 32u 90% 12u "Already installed"
        ${EndIf}
        Pop $VJoyStatusLabel
    ${Else}
        StrCpy $InstallVJoy 1
        ${NSD_CreateCheckbox} 10u 32u 90% 12u "Install vJoy driver (recommended)"
        Pop $VJoyCheckbox
        ${NSD_Check} $VJoyCheckbox
        ${NSD_CreateLabel} 10u 48u 90% 12u "Required for flight sim and legacy game profiles"
        Pop $VJoyStatusLabel
    ${EndIf}
    
    ; ---- ViGEmBus Section ----
    ${NSD_CreateGroupBox} 0 64u 100% 40u "ViGEmBus (Xbox 360 controller emulation)"
    Pop $0
    
    ; Check if ViGEmBus is installed via service query
    nsExec::ExecToStack 'sc query ViGEmBus'
    Pop $0
    Pop $1
    ${If} $0 == 0
        StrCpy $ViGEmInstalled 1
        StrCpy $InstallViGEm 0
        ${NSD_CreateLabel} 10u 78u 90% 12u "Installed and running"
        Pop $ViGEmStatusLabel
    ${Else}
        StrCpy $ViGEmInstalled 0
        StrCpy $InstallViGEm 1
        ${NSD_CreateCheckbox} 10u 78u 90% 12u "Install ViGEmBus driver (recommended)"
        Pop $ViGEmCheckbox
        ${NSD_Check} $ViGEmCheckbox
        ${NSD_CreateLabel} 10u 92u 90% 12u "Required for Game Mode and Xbox controller profiles"
        Pop $ViGEmStatusLabel
    ${EndIf}
    
    ; Info text
    ${NSD_CreateLabel} 0 110u 100% 20u "Both drivers are safe, open-source, and used by DS4Windows, Steam, etc.$\r$\nAn internet connection is required to download them."
    Pop $0
    
    nsDialogs::Show
FunctionEnd

Function VJoyOptionsLeave
    ${If} $VJoyInstalled == 0
        ${NSD_GetState} $VJoyCheckbox $InstallVJoy
    ${EndIf}
    ${If} $ViGEmInstalled == 0
        ${NSD_GetState} $ViGEmCheckbox $InstallViGEm
    ${EndIf}
FunctionEnd

; ---- Custom Page: Keep User Profiles (shown only when upgrading) ----
Var ProfileDialog
Var KeepProfilesRadioYes
Var KeepProfilesRadioNo
Var ProfilesExist

Function ProfilesPage
    ; Only show this page if user data exists in %APPDATA%
    IfFileExists "$APPDATA\ProjectNimbus\*.*" 0 skipPage
    StrCpy $ProfilesExist 1
    
    !insertmacro MUI_HEADER_TEXT "Saved Profiles & Settings" "Your saved controller profiles were found."
    
    nsDialogs::Create 1018
    Pop $ProfileDialog
    ${If} $ProfileDialog == error
        Abort
    ${EndIf}
    
    ${NSD_CreateLabel} 0 0 100% 30u "${PRODUCT_NAME} found existing saved profiles and settings at:$\r$\n$APPDATA\ProjectNimbus"
    Pop $0
    
    ${NSD_CreateLabel} 0 38u 100% 12u "What would you like to do with your saved profiles?"
    Pop $0
    
    ${NSD_CreateRadioButton} 20u 58u 100% 12u "Keep my profiles and settings (recommended)"
    Pop $KeepProfilesRadioYes
    ${NSD_Check} $KeepProfilesRadioYes
    
    ${NSD_CreateRadioButton} 20u 76u 100% 12u "Remove profiles and start fresh"
    Pop $KeepProfilesRadioNo
    
    ${NSD_CreateLabel} 0 100u 100% 30u "Keeping profiles lets you continue right where you left off.$\r$\nYour customizations will survive future upgrades too."
    Pop $0
    
    nsDialogs::Show
    Goto endPage
    skipPage:
        StrCpy $ProfilesExist 0
        StrCpy $KeepProfiles 1  ; default: keep (nothing to delete anyway)
    endPage:
FunctionEnd

Function ProfilesPageLeave
    ${If} $ProfilesExist == 1
        ${NSD_GetState} $KeepProfilesRadioYes $KeepProfiles
    ${EndIf}
FunctionEnd

; ---- Pages ----
!insertmacro MUI_PAGE_WELCOME
Page custom VJoyOptionsPage VJoyOptionsLeave
!insertmacro MUI_PAGE_DIRECTORY
Page custom ShortcutOptionsPage ShortcutOptionsLeave
Page custom ProfilesPage ProfilesPageLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; Finish-page launch function — must be defined AFTER MUI_PAGE_FINISH macro
Function LaunchApplication
    ; System::Call ShellExecuteW launches at normal user privilege,
    ; not inheriting the installer's elevated admin token.
    System::Call 'shell32::ShellExecuteW(i $HWNDPARENT, w "open", w "$INSTDIR\${PRODUCT_EXE}", w "", w "$INSTDIR", i 1)'
FunctionEnd

; ---- Init: check if already running ----
Function .onInit
    ; Bring installer to front (important after UAC elevation)
    BringToFront
    
    ; Initialize shortcut options to checked (1 = checked in NSIS)
    StrCpy $CreateDesktopShortcut 1
    StrCpy $CreateStartMenuShortcut 1
    
    ; Check if Nimbus Adaptive Controller is currently running
    nsExec::ExecToStack 'cmd /c tasklist /FI "IMAGENAME eq ${PRODUCT_EXE}" /NH | findstr /I "Nimbus-Adaptive"'
    Pop $0
    ${If} $0 == 0
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "${PRODUCT_NAME} is currently running.$\r$\n$\r$\nClick OK to close it and continue, or Cancel to abort." IDOK closeApp IDCANCEL abortInstall
        abortInstall:
            Abort
        closeApp:
            nsExec::ExecToLog 'taskkill /F /IM "${PRODUCT_EXE}"'
            Sleep 1500
    ${EndIf}

    ; Check for previous installation in HKCU (per-user install)
    ReadRegStr $0 HKCU "${PRODUCT_UNINST_KEY}" "UninstallString"
    ReadRegStr $2 HKCU "${PRODUCT_UNINST_KEY}" "InstallLocation"
    ${If} $0 != ""
    ${AndIf} $2 != ""
        ReadRegStr $1 HKCU "${PRODUCT_UNINST_KEY}" "DisplayVersion"
        MessageBox MB_YESNO|MB_ICONQUESTION "A previous version of ${PRODUCT_NAME} (v$1) was found at:$\r$\n$2$\r$\n$\r$\nWould you like to remove it before installing the new version?$\r$\n(Recommended: Yes)" IDYES removeUserPrev IDNO skipUserPrev
        removeUserPrev:
            ExecWait '"$0" /S'
            Sleep 2000
        skipUserPrev:
    ${EndIf}

    ; Check for previous installation in HKLM (per-machine install)
    ReadRegStr $0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
    ReadRegStr $2 HKLM "${PRODUCT_UNINST_KEY}" "InstallLocation"
    ${If} $0 != ""
    ${AndIf} $2 != ""
        ReadRegStr $1 HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion"
        MessageBox MB_YESNO|MB_ICONQUESTION "A system-wide installation of ${PRODUCT_NAME} (v$1) was found at:$\r$\n$2$\r$\n$\r$\nWould you like to remove it before installing the new version?$\r$\n(Recommended: Yes)" IDYES removeMachinePrev IDNO skipMachinePrev
        removeMachinePrev:
            ExecWait '"$0" /S'
            Sleep 2000
        skipMachinePrev:
    ${EndIf}
FunctionEnd

; ---- Install Section ----
Section "Install"
    SetOutPath "$INSTDIR"

    ; Install main executable
    File "..\dist\${PRODUCT_EXE}"  ; PyInstaller output: Project-Nimbus-1.3.1.exe

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry entries for Add/Remove Programs (HKCU for per-user)
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_EXE}"
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoRepair" 1

    ; Estimate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "EstimatedSize" $0

    ; Register nimbus:// custom URL scheme for OAuth callback
    WriteRegStr HKCR "nimbus" "" "URL:Nimbus Adaptive Controller"
    WriteRegStr HKCR "nimbus" "URL Protocol" ""
    WriteRegStr HKCR "nimbus\DefaultIcon" "" "$INSTDIR\${PRODUCT_EXE},0"
    WriteRegStr HKCR "nimbus\shell\open\command" "" '"$INSTDIR\${PRODUCT_EXE}" "%1"'

    ; Create shortcuts based on user selection
    ; NOTE: icon argument omitted — NSIS silently drops shortcuts when icon path contains spaces
    ${If} $CreateStartMenuShortcut == 1
        CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
        CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}"
        CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk" "$INSTDIR\Uninstall.exe"
    ${EndIf}
    
    ${If} $CreateDesktopShortcut == 1
        CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}"
    ${EndIf}
    
    ; ---- vJoy Driver Installation ----
    ${If} $InstallVJoy == 1
        DetailPrint "Downloading vJoy driver..."
        SetOutPath "$TEMP"
        
        ; Download vJoy installer from GitHub releases
        ; Using njz3's maintained fork
        NSISdl::download /TIMEOUT=60000 "https://github.com/njz3/vJoy/releases/download/v2.2.1.1/vJoySetup.exe" "$TEMP\vJoySetup.exe"
        Pop $0
        ${If} $0 == "success"
            DetailPrint "Installing vJoy driver (this may take a moment)..."
            ; Run vJoy installer silently
            nsExec::ExecToLog '"$TEMP\vJoySetup.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
            Pop $0
            ${If} $0 == 0
                DetailPrint "vJoy driver installed successfully"
                
                ; Configure vJoy device 1 with 8 axes and 128 buttons
                ; vJoyConfig.exe is installed by vJoy to Program Files
                nsExec::ExecToLog '"$PROGRAMFILES\vJoy\x64\vJoyConfig.exe" 1 -f -a x y z rx ry rz sl0 sl1 -b 128'
                DetailPrint "vJoy device configured"
            ${Else}
                DetailPrint "vJoy installation may require a restart"
                MessageBox MB_OK|MB_ICONINFORMATION "vJoy driver installation complete.$\r$\n$\r$\nYou may need to restart your computer for the driver to work properly."
            ${EndIf}
            
            ; Clean up
            Delete "$TEMP\vJoySetup.exe"
        ${Else}
            DetailPrint "Failed to download vJoy: $0"
            MessageBox MB_OK|MB_ICONEXCLAMATION "Could not download vJoy driver.$\r$\n$\r$\nPlease install it manually from:$\r$\nhttps://github.com/njz3/vJoy/releases$\r$\n$\r$\n${PRODUCT_NAME} will not function without vJoy."
        ${EndIf}
    ${EndIf}
    
    ; ---- ViGEmBus Driver Installation ----
    ${If} $InstallViGEm == 1
        DetailPrint "Downloading ViGEmBus driver..."
        SetOutPath "$TEMP"
        
        ; Download ViGEmBus setup from GitHub releases (nefarius)
        NSISdl::download /TIMEOUT=60000 "https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_Setup_1.22.0.exe" "$TEMP\ViGEmBus_Setup.exe"
        Pop $0
        ${If} $0 == "success"
            DetailPrint "Installing ViGEmBus driver (this may take a moment)..."
            ; Run ViGEmBus installer silently
            nsExec::ExecToLog '"$TEMP\ViGEmBus_Setup.exe" /quiet /norestart'
            Pop $0
            ${If} $0 == 0
                DetailPrint "ViGEmBus driver installed successfully"
            ${Else}
                ; Try alternate silent flags
                nsExec::ExecToLog '"$TEMP\ViGEmBus_Setup.exe" --silent'
                Pop $0
                ${If} $0 == 0
                    DetailPrint "ViGEmBus driver installed successfully"
                ${Else}
                    DetailPrint "ViGEmBus installation may require manual steps"
                    MessageBox MB_OK|MB_ICONINFORMATION "ViGEmBus driver installation complete.$\r$\n$\r$\nIf Game Mode doesn't detect the controller, try:$\r$\n1. Restart your computer$\r$\n2. Or run ViGEmBus_Setup.exe manually from:$\r$\nhttps://github.com/nefarius/ViGEmBus/releases"
                ${EndIf}
            ${EndIf}
            
            ; Clean up
            Delete "$TEMP\ViGEmBus_Setup.exe"
        ${Else}
            DetailPrint "Failed to download ViGEmBus: $0"
            MessageBox MB_OK|MB_ICONEXCLAMATION "Could not download ViGEmBus driver.$\r$\n$\r$\nPlease install it manually from:$\r$\nhttps://github.com/nefarius/ViGEmBus/releases$\r$\n$\r$\nGame Mode (virtual Xbox controller) requires this driver."
        ${EndIf}
    ${EndIf}
SectionEnd

; ---- Uninstall Section ----
Section "Uninstall"
    ; Remove application files from install directory
    Delete "$INSTDIR\${PRODUCT_EXE}"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\controller_config.json"
    RMDir /r "$INSTDIR\profiles"
    RMDir "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

    ; Remove registry entries
    DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"

    ; Remove nimbus:// custom URL scheme
    DeleteRegKey HKCR "nimbus"

    ; Remove user data only if user chose to (KeepProfiles == 0 means "remove")
    ${If} $KeepProfiles == 0
        RMDir /r "$APPDATA\ProjectNimbus"
    ${EndIf}
SectionEnd
