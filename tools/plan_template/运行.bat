@echo off
chcp 65001 >nul
cd /d %~dp0
python plan_template.py params.json
echo.
pause
