@echo off
chcp 65001 > nul
echo ========================================
echo   量化平台 - 前端启动脚本
echo ========================================
echo.

cd /d "%~dp0..\frontend"

echo [1/3] 检查 Node.js...
node --version > nul 2>&1
if errorlevel 1 (
    echo 错误: Node.js 未安装或不在 PATH 中
    echo 请从 https://nodejs.org/ 下载安装
    pause
    exit /b 1
)

echo [2/3] 安装/更新依赖...
if not exist "node_modules" (
    echo 首次安装依赖，可能需要几分钟...
    npm install --registry=https://registry.npmmirror.com
) else (
    echo 依赖已安装，跳过...
)

echo [3/3] 启动前端服务...
echo.
echo 前端服务启动中...
echo 访问地址: http://localhost:3000
echo.
npm run dev
