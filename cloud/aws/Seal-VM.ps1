#
# Seal-VM.ps1:  Run script before creating an AMI
#

Stop-Service -DisplayName 'FOQUS Cloud Service'
Stop-Service -DisplayName  'Turbine Web API Service'

Remove-Item -Recurse -Path C:\ProgramData\foqus_service -ErrorAction SilentlyContinue
Remove-Item -Path 'C:\Program Files (x86)\Turbine\Lite\Data\TurbineCompactDatabase.sdf' -ErrorAction SilentlyContinue
Remove-Item -Path 'C:\Program Files (x86)\Turbine\Lite\Logs\*.log' -Recurse -ErrorAction SilentlyContinue
Clear-RecycleBin -Force

#Start-Service -DisplayName  'Turbine Web API Service'
#Start-Service -DisplayName 'FOQUS Cloud Service'