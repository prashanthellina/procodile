; Procodile (NSIS Installer Script)
;
; This script will install procodile into a directory that the user
;   selects
 
;Var InstallerFiles ;"C:\Users\dexter\Desktop\procodile_installer\*"
;Var InstallerOutput ;"procodile_setup.exe"

Name    "Procodile"       ; The name of the installation
OutFile "${InstallerOutput}"   ; The name of the unistaller file to write
InstallDir "C:\Program Files\Procodile" ; installation directory

LicenseText "Please read the license carefully"
LicenseData "license.txt"

Page license
Page directory
Page instfiles

; Set prompt text for select directory window
DirText "Choose the directory to install to"
  
; Define steps to install procodile 
Section "procodile"
 
  SetOutPath $INSTDIR      ; Set output path to the installation directory
  File /r "${InstallerFiles}\*"  ; Get all files

  ExecWait '"$INSTDIR\vcredist_x86.exe" /q:a /c:"VCREDI~1.EXE /q:a /c:""msiexec /i vcredist.msi /qb!"" "'
 
  ; Write the installation path and uninstall keys into the registry
  WriteRegStr HKLM Software\InstSample "Install_Dir" $INSTDIR
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procodile" \
			"DisplayName" "Procodile (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procodile" \
			"UninstallString" '"$INSTDIR\procodile_uninstall.exe"'
 
  WriteUninstaller "procodile_uninstall.exe"   ; build uninstall program
 
SectionEnd
 
; Define steps to install shortcuts (if selected during installation)
Section "Start Menu Shortcuts"
  CreateDirectory "$SMPROGRAMS\Procodile"
  SetOutPath "$INSTDIR\python"
  CreateShortCut "$SMPROGRAMS\Procodile\PIDE.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\scripts\pide\pide.pyc"'
  SetOutPath "$INSTDIR"
  CreateShortCut "$SMPROGRAMS\Procodile\Uninstall.lnk" "$INSTDIR\procodile_uninstall.exe" \
			"" "$INSTDIR\procodile_uninstall.exe" 0
SectionEnd
 
; Set prompt text for uninstall window
UninstallText "This will uninstall Procodile. Press 'Uninstall' to continue."
 
; Define steps to unistall everything installed.
Section "Uninstall"
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procodile"
  DeleteRegKey HKLM SOFTWARE\Procodile
 
  ; remove files and directories
  RMDIR /r "$INSTDIR\*"
  Delete $INSTDIR\Procodile_uninstall.exe  ; MUST REMOVE UNINSTALLER, too
  Delete "$SMPROGRAMS\Procodile\*.*"       ; remove shortcuts, if any
  RMDir "$SMPROGRAMS\Procodile"            ; remove shortcut directory
SectionEnd
 
; eof

