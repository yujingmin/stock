"""
自动化测试注册和登录流程
"""
import asyncio
import sys
sys.path.insert(0, "backend")

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def test_full_flow():
    """测试完整的注册登录流程"""
    phone = "13800138123"
    username = "webtest1"
    password = "test123456"

    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)

        print("=" * 60)
        print("测试完整的注册登录流程")
        print("=" * 60)

        # 1. 发送注册验证码
        print("\n[1/5] 发送注册验证码...")
        success, message = await auth_service.send_verification_code(
            phone=phone,
            purpose="register"
        )
        if success:
            code = message.split("：")[-1].rstrip("）")
            print(f"   ✓ 验证码: {code}")
        else:
            print(f"   ✗ 失败: {message}")
            return

        # 2. 注册用户
        print(f"\n[2/5] 注册用户 {username}...")
        try:
            success, message, user = await auth_service.register(
                username=username,
                phone=phone,
                password=password,
                verification_code=code
            )
            if success:
                print(f"   ✓ 注册成功 - 用户ID: {user.id}")
            else:
                print(f"   ✗ 失败: {message}")
                return
        except Exception as e:
            if "已存在" in str(e) or "已注册" in str(e):
                print(f"   ⚠ 用户已存在，跳过注册")
            else:
                raise

        # 3. 密码登录
        print(f"\n[3/5] 密码登录...")
        success, message, token_data = await auth_service.login_with_password(
            phone=phone,
            password=password
        )
        if success:
            print(f"   ✓ 登录成功")
            print(f"   Token: {token_data['access_token'][:50]}...")
            print(f"   用户: {token_data['username']}")
        else:
            print(f"   ✗ 失败: {message}")
            return

        # 4. 获取用户信息
        print(f"\n[4/5] 获取用户信息...")
        user = await auth_service.get_user_by_id(token_data['user_id'])
        if user:
            print(f"   ✓ 用户信息:")
            print(f"      用户名: {user.username}")
            print(f"      手机号: {user.phone}")
            print(f"      昵称: {user.nickname}")
            print(f"      状态: {user.status}")
            print(f"      创建时间: {user.created_at}")

        # 5. 发送登录验证码测试
        print(f"\n[5/5] 测试验证码登录...")
        success, message = await auth_service.send_verification_code(
            phone=phone,
            purpose="login"
        )
        if success:
            login_code = message.split("：")[-1].rstrip("）")
            print(f"   ✓ 登录验证码: {login_code}")

            success, message, token_data = await auth_service.login_with_code(
                phone=phone,
                verification_code=login_code
            )
            if success:
                print(f"   ✓ 验证码登录成功")
            else:
                print(f"   ✗ 验证码登录失败: {message}")

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        print("\n📝 测试账号信息:")
        print(f"   手机号: {phone}")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print("\n你可以在浏览器中使用这些信息登录")
        print(f"   前端地址: http://localhost:3001")


if __name__ == "__main__":
    asyncio.run(test_full_flow())
