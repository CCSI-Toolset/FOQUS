@echo off
REM foqus make.bat
echo foqus build
echo

echo *********************
echo Setup Local Variables
echo *********************

set "mdefault=C:\Windows\Microsoft.NET\Framework\v4.0.30319"
set "jdefault=C:\Program Files\Java\jdk1.8.0_121"
set "adefault=C:\Program Files\apache-ant-1.9.6"
set "pdefault=C:\Python27"
set "cdefault=C:\Jenkins\workspace\foqus\pyDRMTraining\pyDRMTraining\lib\coin\win32"
  
if "%MSNET_HOME%" equ "" (
  set "MSNET_HOME="
  set /P MSNET_HOME="Enter MSNET_HOME(%mdefault%): "
  if "%MSNET_HOME%" equ "" set "MSNET_HOME=%mdefault%"
)
  
if "%JAVA_HOME%" equ "" (
  set "JAVA_HOME="
  set /P JAVA_HOME="Enter JAVA_HOME(%jdefault%): "
  if "%JAVA_HOME%" equ "" set "JAVA_HOME=%jdefault%"
)

if "%ANT_HOME%" equ "" (
  set "ANT_HOME="
  set /P ANT_HOME="Enter ANT_HOME(%adefault%): "
  if "%ANT_HOME%" equ "" set "ANT_HOME=%adefault%"
)

if "%PYTHON_DIR%" equ "" (
  set "PYTHON_DIR="
  set /P PYTHON_DIR="Enter PYTHON_DIR(%pdefault%): "
  if "%PYTHON_DIR%" equ "" set "PYTHON_DIR=%pdefault%"
)

if "%COIN_LIB_DIR%" equ "" (
  set "COIN_LIB_DIR="
  set /P COIN_LIB_DIR="Enter COIN_LIB_DIR(%cdefault%): "
  if "%COIN_LIB_DIR%" equ "" set "COIN_LIB_DIR=%cdefault%"
)


echo MSNET_HOME=%MSNET_HOME%
echo JAVA_HOME=%JAVA_HOME%
echo ANT_HOME=%ANT_HOME%
echo PYTHON_DIR=%PYTHON_DIR%
echo COIN_LIB_DIR=%COIN_LIB_DIR%


set PATH=%PATH%;%ANT_HOME%\bin;%JAVA_HOME%\bin;%MSNET_HOME%

echo ************************
echo Build FOQUS User Manaual
echo ************************
set NAME=FOQUS_User_Manual
call tlmgr install ulem  || goto :error
call tlmgr install tex4ht || goto :error
cd manual
pdflatex %NAME%  || goto :homedir
bibtex %NAME%  || goto :homedir
pdflatex %NAME% || goto :homedir
pdflatex %NAME%  || goto :homedir
copy %NAME%.pdf ..\docs\%NAME%.pdf  || goto :homedir
cd ..

echo **************************
echo Copy iReveal Documentation
echo **************************
copy "foqus_lib\framework\surrogate\iREVEAL\docs\iREVEAL User Manual.pdf" docs\iREVEAL_User_Manual.pdf  || goto :error

echo **************************
echo Build DMF Library with Ant
echo **************************
call ant -f dmf_lib\java\build.xml  || goto :error

echo *****************************
echo Clean and Build pyDRMSampling
echo *****************************
MSBuild.exe /p:Configuration=Release /p:PythonDir=%PYTHON_DIR% /t:Clean pyDRMSampling\pyDRMSampling.sln  || goto :error
MSBuild.exe /p:Configuration=Release /p:PythonDir=%PYTHON_DIR% pyDRMSampling\pyDRMSampling.sln  || goto :error

echo *****************************
echo Clean and Build pyDRMTraining
echo *****************************
MSBuild.exe /p:Configuration=Release /p:PythonDir=%PYTHON_DIR% /t:Clean pyDRMTraining\pyDRMTraining.sln  || goto :error
MSBuild.exe /p:Configuration=Release /p:CoinLibDir=%COIN_LIB_DIR% /p:PythonDir=%PYTHON_DIR% pyDRMTraining\pyDRMTraining.sln  || goto :error

echo *********************
echo Build foqus installer
echo *********************
python setup\setup_dep.py  || goto :error
python setup.py wix  || goto :error
goto :EOF

:homedir
cd ..
goto :error
	
:error
echo Failed with error #%errorlevel%.
exit /b %errorlevel%