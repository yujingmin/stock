@echo off
chcp 65001 > nul
echo ========================================
echo   量化平台 - 数据库启动检查
echo ========================================
echo.

echo 检查 PostgreSQL 服务...
sc query postgresql-x64-15 > nul 2>&1
if errorlevel 1 (
    echo [×] PostgreSQL 服务未安装
    echo     请从 https://www.postgresql.org/download/windows/ 下载安装
) else (
    sc query postgresql-x64-15 | findstr "RUNNING" > nul
    if errorlevel 1 (
        echo [×] PostgreSQL 服务未运行
        echo     尝试启动服务...
        net start postgresql-x64-15
    ) else (
        echo [√] PostgreSQL 服务运行中
    )
)
echo.

echo 检查 MongoDB 服务...
sc query MongoDB > nul 2>&1
if errorlevel 1 (
    echo [×] MongoDB 服务未安装
    echo     请从 https://www.mongodb.com/try/download/community 下载安装
) else (
    sc query MongoDB | findstr "RUNNING" > nul
    if errorlevel 1 (
        echo [×] MongoDB 服务未运行
        echo     尝试启动服务...
        net start MongoDB
    ) else (
        echo [√] MongoDB 服务运行中
    )
)
echo.

echo 检查 Redis 服务...
sc query Redis > nul 2>&1
if errorlevel 1 (
    echo [×] Redis 服务未安装
    echo     请从 https://github.com/tporadowski/redis/releases 下载安装
) else (
    sc query Redis | findstr "RUNNING" > nul
    if errorlevel 1 (
        echo [×] Redis 服务未运行
        echo     尝试启动服务...
        net start Redis
    ) else (
        echo [√] Redis 服务运行中
    )
)
echo.
echo ========================================
echo 检查完成
echo ========================================
pause
