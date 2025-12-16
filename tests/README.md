# 测试目录

本目录包含所有自动化测试脚本。

## 目录结构

```
tests/
├── auth/              # 认证相关测试
│   ├── test_all_auth.py      # 完整的自动化认证测试
│   ├── test_auth.py          # 基础认证测试
│   ├── test_login.py         # 登录功能测试
│   ├── test_register.py      # 注册功能测试
│   ├── test_profile.py       # 用户资料测试
│   └── test_full_flow.py     # 完整流程测试
└── utils/             # 测试工具
    ├── create_test_account.py  # 创建测试账号
    └── get_code.py             # 获取验证码工具
```

## 运行测试

### 认证功能完整测试

```bash
cd d:\code\stock
python tests/auth/test_all_auth.py
```

### 创建测试账号

```bash
python tests/utils/create_test_account.py
```

### 获取验证码

```bash
python tests/utils/get_code.py <phone> [purpose]
# 示例：python tests/utils/get_code.py 13800138456 register
```

## 测试账号信息

**默认测试账号**（由test_all_auth.py创建）：
- 手机号：13800138456
- 用户名：autotest456
- 密码：test123456

## 前端测试

前端运行地址：http://localhost:3001

可以使用上述测试账号在浏览器中测试登录、注册等功能。

## 注意事项

1. 运行测试前确保后端服务已启动（端口8000）
2. 确保数据库连接正常
3. 测试脚本会自动清理过期的验证码
4. 某些测试可能会修改数据库，建议在开发环境运行

## 添加新测试

创建新的测试文件时：
1. 将文件放在对应的子目录（auth/、utils/ 等）
2. 按照现有测试的格式编写
3. 更新本 README 文档
