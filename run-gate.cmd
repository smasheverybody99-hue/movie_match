@echo off
rem ============================================================
rem  Movie Match - one-click gate run
rem
rem  Double-click this file. It runs the tool check, installs
rem  dependencies, then runs the phase gate, and writes EVERYTHING
rem  it prints into gate-output.txt next to this file.
rem
rem  Nothing is typed by hand and nothing is hidden: the log file is
rem  the full transcript, including failures.
rem ============================================================

setlocal
set "ROOT=%~dp0"
set "LOG=%ROOT%gate-output.txt"
set "PS=powershell -NoProfile -ExecutionPolicy Bypass -File"

echo Movie Match gate run> "%LOG%"
echo Started: %DATE% %TIME%>> "%LOG%"
echo Folder: %ROOT%>> "%LOG%"
echo.>> "%LOG%"

echo.
echo ============================================
echo  Movie Match - gate run
echo  Everything is logged to gate-output.txt
echo ============================================
echo.

echo [1/3] Checking tools...
echo ######## STEP 1: doctor ########>> "%LOG%"
%PS% "%ROOT%tasks.ps1" doctor>> "%LOG%" 2>&1
set "RC1=%ERRORLEVEL%"
echo ---- doctor exit code: %RC1% ---->> "%LOG%"
echo.>> "%LOG%"
if not "%RC1%"=="0" (
  echo   A required tool is missing. Stopping here.
  echo   Open gate-output.txt to see which one.
  echo ######## STOPPED: missing tools ########>> "%LOG%"
  goto :done
)
echo   OK.

echo [2/3] Installing dependencies. This takes a few minutes...
echo ######## STEP 2: install ########>> "%LOG%"
%PS% "%ROOT%tasks.ps1" install>> "%LOG%" 2>&1
set "RC2=%ERRORLEVEL%"
echo ---- install exit code: %RC2% ---->> "%LOG%"
echo.>> "%LOG%"
if not "%RC2%"=="0" (
  echo   Install failed. Stopping here.
  echo   Open gate-output.txt to see the error.
  echo ######## STOPPED: install failed ########>> "%LOG%"
  goto :done
)
echo   OK.

echo [3/3] Running the gate: lint, typecheck, build, tests...
echo ######## STEP 3: gate ########>> "%LOG%"
%PS% "%ROOT%tasks.ps1" test>> "%LOG%" 2>&1
set "RC3=%ERRORLEVEL%"
echo ---- gate exit code: %RC3% ---->> "%LOG%"
echo.>> "%LOG%"
if "%RC3%"=="0" (
  echo.
  echo   GATE PASSED.
  echo ######## RESULT: GATE PASSED ########>> "%LOG%"
) else (
  echo.
  echo   GATE FAILED - see gate-output.txt
  echo ######## RESULT: GATE FAILED ########>> "%LOG%"
)

:done
echo Finished: %DATE% %TIME%>> "%LOG%"
echo.
echo Done. The full transcript is in:
echo   %LOG%
echo.
echo Tell Claude it has finished - it will read the log itself.
echo.
pause
