@for /f "skip=1" %%a in ('@wmic process where "caption='javaw.exe' and commandline like '%%dmf_client%%'" get processid ^| findstr /r /v "^$"') do @taskkill /F /PID %%a
