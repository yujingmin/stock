#!/bin/bash
# 自动化测试运行脚本

echo "=================================="
echo "运行认证功能自动化测试"
echo "=================================="

# 设置Python路径
PYTHON="d:/code/stock/backend/venv/Scripts/python.exe"

# 运行完整测试
$PYTHON tests/auth/test_all_auth.py

echo ""
echo "=================================="
echo "测试完成"
echo "=================================="
