"""
Create test account for web testing
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def create_test_account():
    """Create a test account"""
    phone = "13900139999"
    username = "testuser"
    password = "test123456"

    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)

        print("="*50)
        print("Creating test account...")
        print("="*50)

        # Send code
        print("\nStep 1: Sending verification code...")
        success, message = await auth_service.send_verification_code(
            phone=phone,
            purpose="register"
        )

        if success:
            code = message.split(":")[-1].strip().rstrip(")")
            print(f"Verification code: {code}")

            # Register
            print("\nStep 2: Registering user...")
            try:
                success, msg, user = await auth_service.register(
                    username=username,
                    phone=phone,
                    password=password,
                    verification_code=code
                )
                if success:
                    print(f"SUCCESS! User registered with ID: {user.id}")
                else:
                    print(f"Failed: {msg}")
            except Exception as e:
                if "exist" in str(e).lower():
                    print("User already exists, that's OK!")
                else:
                    print(f"Error: {e}")

            # Test login
            print("\nStep 3: Testing login...")
            success, msg, token_data = await auth_service.login_with_password(
                phone=phone,
                password=password
            )
            if success:
                print(f"Login SUCCESS!")
                print(f"Token: {token_data['access_token'][:50]}...")

        print("\n" + "="*50)
        print("TEST ACCOUNT INFO:")
        print("="*50)
        print(f"Phone: {phone}")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print("\nYou can now login at:")
        print("http://localhost:3001")
        print("="*50)


if __name__ == "__main__":
    asyncio.run(create_test_account())
