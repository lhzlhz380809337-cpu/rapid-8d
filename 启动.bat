@echo off
chcp 65001 >nul
title Rapid 8D Local Preview
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-preview.ps1"
pause
