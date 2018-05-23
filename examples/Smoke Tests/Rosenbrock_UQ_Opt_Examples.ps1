$wshell = New-Object -ComObject wscript.shell;

Write-Output "Please open a new window of FOQUS and open 'Rosenbrock_no_vectors.foqus'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Navigate to the 'Uncertainty' tab"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Click the 'Launch' box to begin the runs"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Click the 'Analyze' box then "
Read-Host -Prompt "Press Enter to continue"

$wshell.AppActivate('FOQUS')
Sleep 1
$wshell.SendKeys("x['Rosenbrock']['x1'][0] - x['Rosenbrock']['x4'][0]")