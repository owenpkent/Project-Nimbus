; Project Nimbus NSIS Installer Script
; Windows Installer Best Practices (modeled after GitConnect Pro)
; Features: wizard UI, admin/user choice, running app check, previous version detection, shortcut options

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"

; ---- General ----
!define PRODUCT_NAME "Project Nimbus"
!define PRODUCT_EXE "Project-Nimbus-1.3.1.exe"
!define PRODUCT_PUBLISHER "Owen Kent"
!define PRODUCT_VERSION "1.3.1"
!define PRODUCT_GUID "project-nimbus-virtual-controller"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_GUID}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\dist\Project-Nimbus-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\${PRODUCT_NAME}"
InstallDirRegKey HKCU "${PRODUCT_UNINST_KEY}" "InstallLocation"
RequestExecutionLevel admin  ; Request admin but can install per-user too
SetCompressor /SOLID lzma
BrandingText "${PRODUCT_NAME} v${PRODUCT_VERSION}"

; Variables for shortcut options
Var CreateDesktopShortcut
Var CreateStartMenuShortcut
Var InstallVJoy
Var VJoyInstalled

; ---- MUI Settings ----
!define MUI_ICON "Project-Nimbus.ico"
!define MUI_UNICON "Project-Nimbus.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${PRODUCT_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${PRODUCT_NAME} v${PRODUCT_VERSION} on your computer.$\r$\n$\r$\n${PRODUCT_NAME} is a virtual controller interface for accessibility.$\r$\n$\r$\nThe vJoy driver will be installed automatically if needed.$\r$\n$\r$\nClick Next to continue."

; vJoy detection registry key
!define VJOY_UNINST_KEY "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{8E31F76F-74C3-47F1-9550-E041EEDC5FBB}_is1"
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
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

; ---- Custom Page for vJoy Installation ----
Var VJoyDialog
Var VJoyCheckbox
Var VJoyStatusLabel

Function VJoyOptionsPage
    !insertmacro MUI_HEADER_TEXT "Virtual Controller Driver" "vJoy is required for controller emulation."
    
    nsDialogs::Create 1018
    Pop $VJoyDialog
    ${If} $VJoyDialog == error
        Abort
    ${EndIf}
    
    ; Check if vJoy is already installed
    ReadRegStr $0 HKLM "${VJOY_UNINST_KEY}" "DisplayVersion"
    ${If} $0 != ""
        StrCpy $VJoyInstalled 1
        ${NSD_CreateLabel} 0 0 100% 30u "vJoy driver v$0 is already installed.$\r$\n$\r$\nNo action needed - your system is ready!"
        Pop $VJoyStatusLabel
        StrCpy $InstallVJoy 0
    ${Else}
        StrCpy $VJoyInstalled 0
        ${NSD_CreateLabel} 0 0 100% 40u "vJoy driver is required for ${PRODUCT_NAME} to create virtual controllers.$\r$\n$\r$\nThe installer will download and install vJoy automatically.$\r$\nThis requires an internet connection."
        Pop $VJoyStatusLabel
        
        ${NSD_CreateCheckbox} 20u 50u 100% 12u "Install vJoy driver (recommended)"
        Pop $VJoyCheckbox
        ${NSD_Check} $VJoyCheckbox  ; Checked by default
        StrCpy $InstallVJoy 1
    ${EndIf}
    
    nsDialogs::Show
FunctionEnd

Function VJoyOptionsLeave
    ${If} $VJoyInstalled == 0
        ${NSD_GetState} $VJoyCheckbox $InstallVJoy
    ${EndIf}
FunctionEnd

; ---- Pages ----
!insertmacro MUI_PAGE_WELCOME
Page custom VJoyOptionsPage VJoyOptionsLeave
!insertmacro MUI_PAGE_DIRECTORY
Page custom ShortcutOptionsPage ShortcutOptionsLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ---- Init: check if already running ----
Function .onInit
    ; Bring installer to front (important after UAC elevation)
    BringToFront
    
    ; Initialize shortcut options to checked (1 = checked in NSIS)
    StrCpy $CreateDesktopShortcut 1
    StrCpy $CreateStartMenuShortcut 1
    
    ; Check if Project Nimbus is currently running
    nsExec::ExecToStack 'cmd /c tasklist /FI "IMAGENAME eq ${PRODUCT_EXE}" /NH | findstr /I "Project-Nimbus"'
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
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_EXE}"
    WriteRegDWORD HKCU "${PRODUCT_UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKCU "${PRODUCT_UNINST_KEY}" "NoRepair" 1

    ; Estimate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKCU "${PRODUCT_UNINST_KEY}" "EstimatedSize" $0

    ; Create shortcuts based on user selection
    ${If} $CreateStartMenuShortcut == 1
        CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
        CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0
        CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk" "$INSTDIR\Uninstall.exe"
    ${EndIf}
    
    ${If} $CreateDesktopShortcut == 1
        CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0
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
    DeleteRegKey HKCU "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"

    ; Optionally remove user data (profiles, settings) from %APPDATA%
    MessageBox MB_YESNO|MB_ICONQUESTION "Would you like to remove your saved profiles and settings?$\r$\n$\r$\nThey are stored in:$\r$\n$APPDATA\ProjectNimbus$\r$\n$\r$\nSelect 'No' to keep them for future installations." IDYES removeUserData IDNO keepUserData
    removeUserData:
        RMDir /r "$APPDATA\ProjectNimbus"
    keepUserData:
SectionEnd
