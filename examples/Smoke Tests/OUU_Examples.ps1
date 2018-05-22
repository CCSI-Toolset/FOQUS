$wshell = New-Object -ComObject wscript.shell;
# Example 1
Write-Output "Please open a new window of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
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

Write-Output "Please navigate to the 'UQ Setup' tab, select 'Browse...', select x3sample.smp, and click 'Open'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please navigate to the 'Launch/Progress' tab and click 'Run OUU'"
Read-Host -Prompt "Press Enter to continue"

# Example 2
Write-Output "Please open a new window of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
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
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")

Write-Output "Please navigate to the 'UQ Setup' tab and change the Sample Size to 200"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please navigate to the 'Launch/Progress' tab and click 'Run OUU'"
Read-Host -Prompt "Press Enter to continue"

# Example 3
Write-Output "Please open a new window of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
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
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")

Write-Output "Please navigate to the 'UQ Setup' tab, change the Sample Size to 200, and check the box for 'Use Response Surface'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please navigate to the 'Launch/Progress' tab and click 'Run OUU'"
Read-Host -Prompt "Press Enter to continue"

# Example 4
Write-Output "Please open a new window of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
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
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")

Write-Output "Please navigate to the 'UQ Setup' tab, select 'Browse...', select x3sample4.smp, click 'Open', and change the Sample Size to 100"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please navigate to the 'Launch/Progress' tab and click 'Run OUU'"
Read-Host -Prompt "Press Enter to continue"

# Example 5
Write-Output "Please open a new window of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
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
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")

Write-Output "Please navigate to the 'UQ Setup' tab, select 'Browse...', select x3sample4.smp, click 'Open', change the Sample Size to 100, and check the box for 'Use Response Surface'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please navigate to the 'Launch/Progress' tab and click 'Run OUU'"
Read-Host -Prompt "Press Enter to continue"

# Example 6
Write-Output "Please open a new window of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
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
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")

Write-Output "Please navigate to the 'UQ Setup' tab, select 'Browse...', and select x3sample4.smp, click 'Open'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please select the 'Load existing sample for Z4' button, select 'Browse...', and select x4sample4.smp, click 'Open'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please navigate to the 'Launch/Progress' tab and click 'Run OUU'"
Read-Host -Prompt "Press Enter to continue"

# Example 7
Write-Output "Please open a new window of FOQUS, navigate to OUU, load ouu_optdriver.in, and select the column labeled 'Select'"
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
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")
$wshell.SendKeys("{TAB 5}")
$wshell.SendKeys("{DOWN 5}")

Write-Output "Please navigate to the 'UQ Setup' tab, select the 'Load existing sample for Z4' button, select 'Browse...', and select x4sampleLarge.smp, click 'Open'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Check the box for 'Use Response Surface' and specify the 'Response Surface Sample Size' at 100"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Please navigate to the 'Launch/Progress' tab and click 'Run OUU'"
Read-Host -Prompt "Press Enter to continue"