@echo off

set "SEGENV=.\segtool"
set LOGFILE=script.log

REM GIT Stuff
set "RESTCALL=http://mgegit.miltenyibiotec.de:7990/rest/api/latest/projects/~ANDREG/repos/"
set "REFS=archive?at=refs%%2Fheads%%2F"
set "FORMAT=^&format=zip"

set "DFREP=%RESTCALL%dataframework/%REFS%master%FORMAT%"
set "STREP=%RESTCALL%segtool/%REFS%devel%FORMAT%"


REM Venv stuff
set "ACTIVATECMD=%SEGENV%\Scripts\activate.bat"

REM Proxy stuff
set "http_proxy=mgewebgateway02.miltenyibiotec.de:8080"
set "https_proxy=mgewebgateway02.miltenyibiotec.de:8080"

IF NOT EXIST %SEGENV% (
    call :install
	EXIT /B %ERRORCODE%
)

IF "%~1" == "install" (
	call :install
	EXIT /B %ERRORCODE%
)

IF "%~1" == "upgrade" (
	echo 'Updating...' > %LOGFILE%
	call :activate
	call :pipupgrade
	
	IF "%~2" == "segtool" (
		call :upgradeST
		EXIT /B %ERRORCODE%
	)
	IF "%~2" == "dataframework" (
		call :upgradeDF
		EXIT /B %ERRORCODE%
	)
	IF "%~2" == "all" (
		call :upgradeDF
		call :upgradeST
	EXIT /B %ERRORCODE%
	)
	echo Updat options are 'segtool', 'dataframework' or 'all'
	EXIT /B -1
)

IF EXIST %SEGENV% (
    call :run %*
    EXIT /B %ERRORCODE%
)

echo invalid parameter: %1
echo valid arguments are 'update', 'install' or ''
EXIT /B -1

:activate
echo --- >> %LOGFILE%
echo Activating virtual environment
echo ACTIVATION >> %LOGFILE%
call %ACTIVATECMD% >> %LOGFILE% 2>&1
EXIT /B 0

:info
echo --- >> %1
echo Gather some info
echo PYTHONINFO >> %1
python -VV >> %1 2>&1
echo PIPINFO >> %1
pip --version >> %1 2>&1
echo PIPLIST >> %1
pip list >> %1 2>&1
EXIT /B 0

:pipupgrade
echo --- >> %LOGFILE%
echo Upgrading pip
echo PIPUPGRADE >> %LOGFILE%
python -m pip install pip --upgrade >> %LOGFILE% 2>&1
EXIT /B 0

:installDF
echo --- >> %LOGFILE%
echo Installing dataframework
echo INSTALL DF >> %LOGFILE%
pip install %DFREP% >> %LOGFILE% 2>&1
EXIT /B 0

:installST
echo --- >> %LOGFILE%
echo Installing segtool
echo INSTALL ST >> %LOGFILE%
pip install %STREP% >> %LOGFILE% 2>&1
EXIT /B 0

:uninstallST
echo --- >> %LOGFILE%
echo Uninstalling segtool
echo UNINSTALL ST >> %LOGFILE%
pip uninstall -y segtool >> %LOGFILE% 2>&1
EXIT /B 0

:uninstallDF
echo --- >> %LOGFILE%
echo Uninstalling dataframework
echo UNINSTALL DF >> %LOGFILE%
pip uninstall -y dataframework >> %LOGFILE% 2>&1
EXIT /B 0

:mkvenv
echo --- >> %LOGFILE%
echo Installing virtual environment
echo VIRTENV >> %LOGFILE%
call %SYSPYTHON% -m venv --clear %SEGENV% >> %LOGFILE% 2>&1
EXIT /B 0

:run
set LOGFILE=run.log 
echo 'Starting...' > %LOGFILE%
call :activate
REM call :info %LOGFILE%
set "CMD=python -m segtool %*"
echo 'Using %CMD%' > %LOGFILE%
%CMD%
EXIT /B 0

:upgradeST
echo --- >> %LOGFILE%
echo Upgrading segtool
echo UPGRADE ST >> %LOGFILE%
pip install %STREP% --upgrade>> %LOGFILE% 2>&1
echo Segtool version now:
python -c "import segtool as st; print(st.__version__)"
EXIT /B 0

:upgradeDF
echo --- >> %LOGFILE%
echo Upgrading dataframework
echo UPGRADE DF >> %LOGFILE%
pip install %DFREP% --upgrade>> %LOGFILE% 2>&1
echo Dataframework version now:
python -c "import dataframework as df; print(df.__version__)"
EXIT /B 0

:install
set LOGFILE=install.log 
set SYSPYTHON=python
echo 'Installing...' > %LOGFILE%
call :mkvenv
call :activate
call :pipupgrade
call :info %LOGFILE%
call :installDF
call :installST
echo done
pause
EXIT /B 0
