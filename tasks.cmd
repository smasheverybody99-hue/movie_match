@echo off
rem Wrapper for tasks.ps1.
rem
rem PowerShell refuses to run .ps1 files under the default Restricted execution
rem policy. A .cmd file is not subject to that policy, so this launches the
rem script with a per-invocation bypass. Nothing about the machine's policy
rem changes: the bypass applies only to this one process.
rem
rem Usage:  tasks install | dev-api | dev-web | lint | test | migrate

setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tasks.ps1" %*
exit /b %ERRORLEVEL%
