@echo off
REM 自动化测试运行脚本 (Windows)

echo ==================================
echo 运行认证功能自动化测试
echo ==================================

REM 运行完整测试
"d:\code\stock\backend\venv\Scripts\python.exe" tests\auth\test_all_auth.py

echo.
echo ==================================
echo 测试完成
echo ==================================
pause
