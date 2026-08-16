!macro NSIS_HOOK_POSTINSTALL
  CreateShortcut "$DESKTOP\JARVIS 2.0.lnk" "$INSTDIR\jarvis.exe"
!macroend
