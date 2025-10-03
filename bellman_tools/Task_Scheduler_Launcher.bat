@ECHO OFF

ECHO %~dp0
ECHO %1
ECHO %2

call %3 %4

REM S:
REM cd %~dp0
cd %2
python %1

REM PAUSE