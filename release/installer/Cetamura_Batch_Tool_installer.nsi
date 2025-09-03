; NSIS installer script for Cetamura_Batch_Tool
; Created automatically by automation

Name "Cetamura Batch Tool"
OutFile "Cetamura_Batch_Tool_Installer.exe"
InstallDir "$PROGRAMFILES\\Cetamura Batch Tool"
RequestExecutionLevel user

!include "MUI2.nsh"

; Pages
!insertmacro MUI_PAGE_LICENSE ""
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Language
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  ; Copy all files from the built one-folder directory
  ; Adjust the path if your dist directory is different
  File /r "..\\..\\dist\\Cetamura_Batch_Tool\\*"

  ; Create shortcuts
  CreateShortCut "$SMPROGRAMS\\Cetamura Batch Tool.lnk" "$INSTDIR\\Cetamura_Batch_Tool.exe"

  ; Write uninstall info
  WriteUninstaller "$INSTDIR\\uninstall.exe"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Cetamura Batch Tool" "DisplayName" "Cetamura Batch Tool"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Cetamura Batch Tool" "UninstallString" "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\\Cetamura_Batch_Tool.exe"
  Delete "$SMPROGRAMS\\Cetamura Batch Tool.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Cetamura Batch Tool"
SectionEnd
