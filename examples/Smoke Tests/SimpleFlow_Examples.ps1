Write-Output "Please open a new window of FOQUS and open 'Simple_flow.foqus'"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Select the Flowsheet tab and click the green play button (Start Single Flowsheet Evaluation)"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Select the Uncertainty tab, click 'Clone Selected', and click 'Launch' on the second ensemble"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Select the Flowsheet tab and click the table button (Results and Filtering)"
Read-Host -Prompt "Press Enter to continue"

Write-Output "For 'Current Filter' select all, then Results, then ResultsAndError, then Operation, and then return to all"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Select Menu > Export > Copy Data to Clipboard"
Read-Host -Prompt "Press Enter to continue"

Start-Process Excel
Sleep 10
Write-Output "Please paste the data into Excel and then close Excel"
Read-Host -Prompt "Press Enter to continue"

Write-Output "Select Menu > Export > Export to CSV File..."
Read-Host -Prompt "Press Enter to continue"

Write-Output "Open the CSV file and ensure the data saved successfully"
Read-Host -Prompt "Press Enter to continue"