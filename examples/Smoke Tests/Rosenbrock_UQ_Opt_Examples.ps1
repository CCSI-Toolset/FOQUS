$wshell = New-Object -ComObject wscript.shell;

Write-Output "Please open a new window of FOQUS and open 'Rosenbrock_no_vectors.foqus'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Navigate to the 'Uncertainty' tab"
Read-Host -Prompt "Press Enter to continue"

<#
#This code can be used to simulate creating a brand new simulation ensemble with one fixed value

Write-Output "Click 'Add New'"
Read-Host -Prompt "Press Enter to continue"

$wshell.AppActivate('FOQUS - ')
Sleep 1
$wshell.SendKeys("{ENTER}")
Sleep 1
$wshell.SendKeys("{TAB 10}")
$wshell.SendKeys("{DOWN}")
$wshell.SendKeys("{TAB 11}")
$wshell.SendKeys("{RIGHT}")
$wshell.SendKeys("{TAB 3}")
$wshell.SendKeys("{DOWN 2}")
$wshell.SendKeys("{TAB 2}")
$wshell.SendKeys("{ENTER}")
Sleep 2
$wshell.SendKeys("{TAB}")
$wshell.SendKeys("{ENTER}")

#>

Write-Output "Click the 'Launch' box to begin the runs"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Click the 'Analyze' box then change the mode from Wizard to Expert by clicking the top button"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Select 'Rosenbrock.f' as the output to analyze and click 'Compute input importance'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Switch to a different parameter selection method and click 'Compute input importance'. Repeat until all methods have been tested"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Under 'Ensemble Data Analysis' select two inputs to visualize, and click 'Visualize'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Under 'Ensemble Data Analysis' click 'Analyze', change 'Uncertainty Quantification' to 'Correlation Analysis' and click 'Analyze'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Under 'Ensemble Data Analysis' click 'Analyze', change 'Correlation Analysis' to 'Sensitivity Analysis' and click 'Analyze'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Change 'First-Order' to 'Second-Order' and click 'Analyze'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Under 'Response Surface' click 'Validate'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Change the RS and sub-RS to every combintation (excluding regression) clicking 'Validate' after each change"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Select three inputs under 'Visualize RS' and click 'Visualize'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Under 'Choose UQ Analysis' click 'Analyze' and repeat for all combinations of UQ. Make sure to change types and PDFs in the table for different combinations"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Click 'Infer...', select the observed box for 'Rosenbrock.f', and select the 'Input Name' column"
Read-Host -Prompt "Press Enter to continue"

$wshell.AppActivate('Bayesian Inference of Ensemble UQ_Ensemble')
Sleep 1
$wshell.SendKeys("{TAB 11}")
$wshell.SendKeys("{DOWN}")
$wshell.SendKeys("{TAB 4}")
$wshell.SendKeys("{DOWN 3}")


#insert automated method to change all PDFs to different types with the corresponding parameters

Write-Output "Click 'Save Posterior Input Samples to File', 'Use Discrepancy', and 'Save Discrepancy Input Samples to File' selecting locations to save the files outside the github folder"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Click 'Infer'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Navigate to the 'Optimization' tab"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Navigate to the 'Run' tab and click the start button"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Navigate to the 'Solver' tab, change the solver, navigate to the 'Run' tab, and click the start button. Repeat for all the different solvers"
Read-Host -Prompt "Press Enter to continue"



Write-Output "Navigate to the 'Objective/Constraints' tab, click the '+' button in the 'Inequality Constraints' section, and click the expression box for the newly-created constraint"
Read-Host -Prompt "Press Enter to continue"

$wshell.AppActivate('FOQUS - ')
Sleep 1
$wshell.SendKeys("x['Rosenbrock']['x1'][0] - x['Rosenbrock']['x4'][0]")
$wshell.SendKeys("{TAB}")
$wshell.SendKeys("100")
$wshell.SendKeys("{ENTER}")

Write-Output "Navigate to the 'Run' tab and click the start button"
Read-Host -Prompt "Press Enter to continue"

