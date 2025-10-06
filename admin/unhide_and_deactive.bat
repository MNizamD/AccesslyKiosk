:: Show on login screen again
reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList" /v Administrator /f

:: Disable account again
net user Administrator /active:no
