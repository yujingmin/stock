@echo off
chcp 65001 > nul
echo ========================================
echo   量化平台 - PostgreSQL 数据库初始化
echo ========================================
echo.

echo 请确保 PostgreSQL 已安装并正在运行
echo.
echo 默认配置：
echo   数据库名: quant_platform
echo   用户名: quant_user
echo   密码: quant_password_dev
echo.
pause

echo.
echo [1/2] 创建数据库和用户...
echo.

psql -U postgres -c "CREATE DATABASE quant_platform;" 2>nul
if errorlevel 1 (
    echo 数据库可能已存在，继续...
) else (
    echo ✓ 数据库创建成功
)

psql -U postgres -c "CREATE USER quant_user WITH PASSWORD 'quant_password_dev';" 2>nul
if errorlevel 1 (
    echo 用户可能已存在，继续...
) else (
    echo ✓ 用户创建成功
)

psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE quant_platform TO quant_user;" 2>nul
echo ✓ 权限授予成功

echo.
echo [2/2] 验证数据库连接...
psql -U quant_user -d quant_platform -c "SELECT version();" 2>nul
if errorlevel 1 (
    echo ✗ 连接失败，请检查配置
) else (
    echo ✓ 数据库配置完成！
)

echo.
echo ========================================
echo 初始化完成
echo ========================================
pause
