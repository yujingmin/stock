@echo off
echo 检查 Docker 镜像源配置...
docker info | findstr "Registry Mirrors"
echo.
echo 如果看到镜像源地址，说明配置成功
pause
