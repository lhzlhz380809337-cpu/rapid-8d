@echo off
setlocal
chcp 65001 >nul
title Rapid 8D Port Cleanup

for %%P in (18080 18723) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
    echo Stopping process %%A on port %%P...
    taskkill /PID %%A /T /F >nul 2>&1
  )
)

set "REMAINING="
for %%P in (18080 18723) do (
  netstat -ano | findstr /R /C:":%%P .*LISTENING" >nul
  if not errorlevel 1 set "REMAINING=1"
)
if defined REMAINING (
  echo One or more preview ports are still in use. Run this file as administrator.
) else (
  echo Rapid 8D preview ports are clear.
)
pause
