"""
测试用户认证流程
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_send_verification_code():
    """测试发送验证码"""
    print("\n=== 测试发送验证码 ===")
    url = f"{BASE_URL}/auth/send-code"
    data = {
        "phone": "13800138000",
        "purpose": "register"
    }

    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # 从消息中提取验证码（格式：验证码已发送，请查收！xxxxxx）
    if response.status_code == 200 and "message" in result:
        msg = result["message"]
        import re
        match = re.search(r'(\d{6})', msg)
        if match:
            code = match.group(1)
            print(f"提取到验证码: {code}")
            return code
    return None

def test_register(verification_code):
    """测试用户注册"""
    print("\n=== 测试用户注册 ===")
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "testuser_" + str(int(time.time())),
        "phone": "13800138000",
        "password": "test123456",
        "verification_code": verification_code
    }

    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\n[OK] 注册成功！Token: {token[:50]}...")
        return token
    else:
        print(f"\n[ERROR] 注册失败")
        return None

def test_login_with_password(phone, password):
    """测试密码登录"""
    print("\n=== 测试密码登录 ===")
    url = f"{BASE_URL}/auth/login"
    data = {
        "phone": phone,
        "password": password
    }

    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\n[OK] 登录成功！Token: {token[:50]}...")
        return token
    else:
        print(f"\n[ERROR] 登录失败")
        return None

def test_login_with_code(phone):
    """测试验证码登录"""
    print("\n=== 测试验证码登录 ===")

    # 先发送验证码
    send_code_url = f"{BASE_URL}/auth/send-code"
    send_code_data = {
        "phone": phone,
        "purpose": "login"
    }
    send_response = requests.post(send_code_url, json=send_code_data)
    print(f"发送验证码状态: {send_response.status_code}")

    # 提取验证码
    import re
    verification_code = None
    if send_response.status_code == 200:
        result = send_response.json()
        msg = result.get("message", "")
        match = re.search(r'(\d{6})', msg)
        if match:
            verification_code = match.group(1)
            print(f"提取到验证码: {verification_code}")

    if not verification_code:
        print("[WARNING] 未能提取验证码，使用默认值")
        verification_code = "123456"

    # 使用验证码登录
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "phone": phone,
        "verification_code": verification_code
    }

    response = requests.post(login_url, json=login_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\n[OK] 验证码登录成功！Token: {token[:50]}...")
        return token
    else:
        print(f"\n[ERROR] 验证码登录失败")
        return None

def test_get_current_user(token):
    """测试获取当前用户信息"""
    print("\n=== 测试获取当前用户信息 ===")
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
    """运行完整的认证流程测试"""
    print("=" * 60)
    print("开始测试用户认证流程")
    print("=" * 60)

    # 1. 测试发送验证码
    verification_code = test_send_verification_code()
    if not verification_code:
        print("\n[WARNING] 发送验证码失败，但继续测试...")
        verification_code = "123456"  # 使用默认值

    # 2. 测试注册
    token = test_register(verification_code)
    if not token:
        print("\n测试终止：注册失败")
        return

    # 3. 测试获取用户信息
    if test_get_current_user(token):
        print("\n[OK] 获取用户信息成功")

    # 4. 测试登出
    if test_logout(token):
        print("\n[OK] 登出成功")

    # 5. 测试密码登录
    token = test_login_with_password("13800138000", "test123456")
    if token:
        print("\n[OK] 密码登录测试通过")
        test_get_current_user(token)

    # 6. 测试验证码登录
    token = test_login_with_code("13800138000")
    if token:
        print("\n[OK] 验证码登录测试通过")
        test_get_current_user(token)

    print("\n" + "=" * 60)
    print("[OK] 所有认证流程测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
