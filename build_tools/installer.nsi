; Project Nimbus NSIS Installer Script
; Creates a Windows installer with shortcuts, uninstall, and previous-version detection
; Modeled after GitConnect Pro installer practices

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; ---- General ----
!define PRODUCT_NAME "Project Nimbus"
!define PRODUCT_EXE "Project-Nimbus.exe"
!define PRODUCT_PUBLISHER "Owen Kent"
!define PRODUCT_VERSION "1.2.0"
!define PRODUCT_GUID "project-nimbus-virtual-controller"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_GUID}"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\dist\Project-Nimbus-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$LOCALAPPDATA\${PRODUCT_NAME}"
InstallDirRegKey HKCU "${PRODUCT_UNINST_KEY}" "InstallLocation"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "${PRODUCT_NAME} v${PRODUCT_VERSION}"

; ---- MUI Settings ----
!define MUI_ICON "Project-Nimbus.ico"
!define MUI_UNICON "Project-Nimbus.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${PRODUCT_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${PRODUCT_NAME} v${PRODUCT_VERSION} on your computer.$\r$\n$\r$\n${PRODUCT_NAME} is a virtual controller interface for accessibility.$\r$\n$\r$\nNote: VJoy driver must be installed separately.$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${PRODUCT_NAME}"

; ---- Pages ----
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ---- Init: check if already running ----
Function .onInit
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

    ; Check for previous installation in a different directory
    ReadRegStr $0 HKCU "${PRODUCT_UNINST_KEY}" "UninstallString"
    ReadRegStr $2 HKCU "${PRODUCT_UNINST_KEY}" "InstallLocation"
    ${If} $0 != ""
    ${AndIf} $2 != ""
    ${AndIf} $2 != "$INSTDIR"
    ${AndIf} $2 != "$INSTDIR\"
        ReadRegStr $1 HKCU "${PRODUCT_UNINST_KEY}" "DisplayVersion"
        MessageBox MB_YESNO|MB_ICONQUESTION "A previous version of ${PRODUCT_NAME} (v$1) was found at:$\r$\n$2$\r$\n$\r$\nWould you like to remove it?$\r$\n(Recommended: Yes)" IDYES removePrev IDNO skipPrev
        removePrev:
            ExecWait '"$0" /S'
            Sleep 2000
        skipPrev:
    ${EndIf}
FunctionEnd

; ---- Install Section ----
Section "Install"
    SetOutPath "$INSTDIR"

    ; Install main executable
    File "..\dist\${PRODUCT_EXE}"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry entries for Add/Remove Programs
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

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0
SectionEnd

; ---- Uninstall Section ----
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\${PRODUCT_EXE}"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\controller_config.json"
    RMDir /r "$INSTDIR\profiles"
    RMDir "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

    ; Remove registry entries
    DeleteRegKey HKCU "${PRODUCT_UNINST_KEY}"
SectionEnd
