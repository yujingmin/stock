@echo off
chcp 65001 > nul
echo ========================================
echo   量化平台 - 后端启动脚本
echo ========================================
echo.

cd /d "%~dp0..\backend"

echo [1/4] 检查 Python 虚拟环境...
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: Python 未安装或不在 PATH 中
        pause
        exit /b 1
    )
)

echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/4] 安装/更新依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo [4/4] 启动后端服务...
echo.
echo 后端服务启动中...
echo API 文档: http://localhost:8000/api/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
