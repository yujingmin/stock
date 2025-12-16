"""
测试已注册用户的登录流程
"""
import requests
import json
import re

BASE_URL = "http://localhost:8000/api/v1"

def test_password_login():
    """测试密码登录"""
    print("\n=== 测试密码登录 ===")
    url = f"{BASE_URL}/auth/login"
    data = {
        "phone": "13800138000",
        "password": "test123456"
    }

    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\n[OK] 密码登录成功！")
        return token
    else:
        print(f"\n[ERROR] 密码登录失败")
        return None

def test_code_login():
    """测试验证码登录"""
    print("\n=== 测试验证码登录 ===")

    # 1. 发送验证码
    send_url = f"{BASE_URL}/auth/send-code"
    send_data = {
        "phone": "13800138000",
        "purpose": "login"
    }

    print("发送验证码...")
    send_response = requests.post(send_url, json=send_data)
    print(f"状态码: {send_response.status_code}")

    # 提取验证码
    verification_code = None
    if send_response.status_code == 200:
        result = send_response.json()
        msg = result.get("message", "")
        match = re.search(r'(\d{6})', msg)
        if match:
            verification_code = match.group(1)
            print(f"提取到验证码: {verification_code}")

    if not verification_code:
        print("[ERROR] 无法获取验证码")
        return None

    # 2. 使用验证码登录
    print("\n使用验证码登录...")
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "phone": "13800138000",
        "verification_code": verification_code
    }

    response = requests.post(login_url, json=login_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\n[OK] 验证码登录成功！")
        return token
    else:
        print(f"\n[ERROR] 验证码登录失败")
        return None

def test_get_user_info(token):
    """测试获取用户信息"""
    print("\n=== 测试获取用户信息 ===")
    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    return response.status_code == 200

def test_logout(token):
    """测试登出"""
    print("\n=== 测试登出 ===")
    url = f"{BASE_URL}/auth/logout"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    return response.status_code == 200

def main():
    print("=" * 60)
    print("测试已注册用户的登录流程")
    print("测试账号: 13800138000 / test123456")
    print("=" * 60)

    # 1. 测试密码登录
    token1 = test_password_login()
    if token1:
        print("\n[OK] 密码登录测试通过")
        test_get_user_info(token1)
        test_logout(token1)
    else:
        print("\n[ERROR] 密码登录测试失败")

    # 2. 测试验证码登录
    token2 = test_code_login()
    if token2:
        print("\n[OK] 验证码登录测试通过")
        test_get_user_info(token2)
        test_logout(token2)
    else:
        print("\n[ERROR] 验证码登录测试失败")

    print("\n" + "=" * 60)
    print("[OK] 登录流程测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
