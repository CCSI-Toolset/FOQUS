$wshell = New-Object -ComObject wscript.shell;
# Example 1
Write-Output "Please open a new session of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
Read-Host -Prompt "Press Enter to continue"
$wshell.AppActivate('FOQUS')
Sleep 1
$wshell.SendKeys("{TAB}")
$wshell.SendKeys("{DOWN}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN 3}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN 3}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN 3}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN 3}")
$wshell.SendKeys("{TAB 6}")
$wshell.SendKeys("{DOWN 4}")
$wshell.SendKeys("{TAB 3}")
$wshell.SendKeys("{DOWN 4}")
$wshell.SendKeys("{TAB 3}")
$wshell.SendKeys("{DOWN 4}")
$wshell.SendKeys("{TAB 3}")
$wshell.SendKeys("{DOWN 4}")

