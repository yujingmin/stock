"""
用户认证服务层
"""
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserSession, VerificationCode
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings


def utcnow():
    """返回时区感知的 UTC 当前时间"""
    return datetime.now(timezone.utc)


class AuthService:
    """用户认证服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        username: str,
        phone: str,
        password: str,
        verification_code: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """
        用户注册

        Returns:
            (success, message, user)
        """
        # 检查用户名是否已存在
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            return False, "用户名已存在", None

        # 检查手机号是否已注册
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        if result.scalar_one_or_none():
            return False, "手机号已注册", None

        # 如果提供了验证码，验证验证码
        if verification_code:
            is_valid = await self._verify_code(phone, verification_code, "register")
            if not is_valid:
                return False, "验证码无效或已过期", None

        # 创建用户
        user = User(
            username=username,
            phone=phone,
            password_hash=get_password_hash(password),
            nickname=username,
            status="active",
            vip_level=0,
            created_at=utcnow(),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return True, "注册成功", user

    async def login_with_password(
        self,
        phone: str,
        password: str,
        device_info: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        密码登录

        Returns:
            (success, message, token_data)
        """
        # 查找用户
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "手机号未注册", None

        # 验证密码
        if not verify_password(password, user.password_hash):
            return False, "密码错误", None

        # 检查用户状态
        if user.status != "active":
            return False, f"账号状态异常: {user.status}", None

        # 更新最后登录时间
        user.last_login_at = utcnow()
        user.last_login_ip = device_info or "unknown"
        await self.db.commit()

        # 创建会话
        token_data = await self._create_session(user, device_info)

        return True, "登录成功", token_data

    async def login_with_code(
        self,
        phone: str,
        verification_code: str,
        device_info: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        验证码登录

        Returns:
            (success, message, token_data)
        """
        # 验证验证码
        is_valid = await self._verify_code(phone, verification_code, "login")
        if not is_valid:
            return False, "验证码无效或已过期", None

        # 查找用户
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "手机号未注册", None

        # 检查用户状态
        if user.status != "active":
            return False, f"账号状态异常: {user.status}", None

        # 更新最后登录时间
        user.last_login_at = utcnow()
        user.last_login_ip = device_info or "unknown"
        await self.db.commit()

        # 创建会话
        token_data = await self._create_session(user, device_info)

        return True, "登录成功", token_data

    async def send_verification_code(
        self,
        phone: str,
        purpose: str
    ) -> Tuple[bool, str]:
        """
        发送验证码

        Args:
            phone: 手机号
            purpose: 用途 (register/login/reset_password)

        Returns:
            (success, message)
        """
        # 生成6位随机验证码
        code = str(random.randint(100000, 999999))

        # 检查是否有未过期的验证码
        result = await self.db.execute(
            select(VerificationCode).where(
                VerificationCode.phone == phone,
                VerificationCode.purpose == purpose,
                VerificationCode.is_used == False,
                VerificationCode.expire_at > utcnow()
            )
        )
        existing_code = result.scalar_one_or_none()

        if existing_code:
            # 检查是否在1分钟内重复发送
            if (utcnow() - existing_code.created_at).seconds < 60:
                return False, "请勿频繁发送验证码，请稍后再试"

        # 保存验证码到数据库
        verification_code = VerificationCode(
            phone=phone,
            code=code,
            purpose=purpose,
            expire_at=utcnow() + timedelta(minutes=5),
            created_at=utcnow(),
        )
        self.db.add(verification_code)
        await self.db.commit()

        # TODO: 实际发送短信（集成阿里云短信服务）
        # 开发环境直接打印验证码
        print(f"[SMS] Verification code sent - Phone: {phone}, Code: {code}, Purpose: {purpose}")

        return True, f"验证码已发送（开发环境：{code}）"

    async def reset_password(
        self,
        phone: str,
        verification_code: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        重置密码

        Returns:
            (success, message)
        """
        # 验证验证码
        is_valid = await self._verify_code(phone, verification_code, "reset_password")
        if not is_valid:
            return False, "验证码无效或已过期"

        # 查找用户
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "手机号未注册"

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()

        return True, "密码重置成功"

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        修改密码（已登录用户）

        Returns:
            (success, message)
        """
        # 查找用户
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "用户不存在"

        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            return False, "旧密码错误"

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()

        return True, "密码修改成功"

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_profile(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """
        更新用户信息

        Returns:
            (success, message, user)
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False, "用户不存在", None

        if nickname:
            user.nickname = nickname
        if email:
            user.email = email
        if avatar_url:
            user.avatar_url = avatar_url

        await self.db.commit()
        await self.db.refresh(user)

        return True, "信息更新成功", user

    async def logout(self, token: str) -> Tuple[bool, str]:
        """
        登出（使会话失效）

        Returns:
            (success, message)
        """
        result = await self.db.execute(
            select(UserSession).where(UserSession.token == token)
        )
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            await self.db.commit()

        return True, "登出成功"

    # 私有方法

    async def _verify_code(
        self,
        phone: str,
        code: str,
        purpose: str
    ) -> bool:
        """验证验证码"""
        result = await self.db.execute(
            select(VerificationCode).where(
                VerificationCode.phone == phone,
                VerificationCode.code == code,
                VerificationCode.purpose == purpose,
                VerificationCode.is_used == False,
                VerificationCode.expire_at > utcnow()
            )
        )
        verification_code = result.scalar_one_or_none()

        if not verification_code:
            return False

        # 标记为已使用
        verification_code.is_used = True
        await self.db.commit()

        return True

    async def _create_session(
        self,
        user: User,
        device_info: Optional[str] = None
    ) -> dict:
        """创建会话并返回 token 数据"""
        # 生成 JWT token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "phone": user.phone,
        }
        expires_delta = timedelta(days=settings.JWT_EXPIRATION_DAYS)
        access_token = create_access_token(token_data, expires_delta)

        # 保存会话到数据库
        session = UserSession(
            user_id=user.id,
            token=access_token,
            device_info=device_info or "unknown",
            ip_address=user.last_login_ip,
            expire_at=utcnow() + expires_delta,
            created_at=utcnow(),
        )
        self.db.add(session)
        await self.db.commit()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(expires_delta.total_seconds()),
            "user_id": user.id,
            "username": user.username,
        }
