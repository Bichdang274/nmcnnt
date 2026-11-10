@echo off
setlocal
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0chay_demo_1_click.ps1" -ToiUuCuaSo %*
exit /b %errorlevel%
