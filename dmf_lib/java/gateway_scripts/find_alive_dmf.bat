@set count=0
@for /f "skip=1" %%a in ('@wmic process where "caption='DMF_Browser.exe' or caption='foqus_console.exe'" get processid ^| findstr /r /v "^$"') do @set /a count+=1
@echo %count%
