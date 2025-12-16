"""
用户认证 API 端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth import AuthService
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    SendVerificationCodeRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
    UserProfileUpdateRequest,
    MessageResponse,
)
from app.core.security import decode_access_token

router = APIRouter()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """从 JWT token 中获取当前用户ID"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌格式错误",
        )

    return int(user_id)


@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册

    - **username**: 用户名 (3-50字符，仅字母数字下划线)
    - **phone**: 手机号 (11位中国大陆手机号)
    - **password**: 密码 (6-50字符)
    - **verification_code**: 短信验证码 (可选)
    """
    success, message, user = await auth_service.register(
        username=request.username,
        phone=request.phone,
        password=request.password,
        verification_code=request.verification_code,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # 注册成功后自动登录
    success, message, token_data = await auth_service.login_with_password(
        phone=request.phone,
        password=request.password,
    )

    if not success:
        raise HTTPException(status_code=500, detail="注册成功但登录失败")

    return TokenResponse(**token_data)


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录（支持密码登录和验证码登录）

    - **phone**: 手机号
    - **password**: 密码 (密码登录时必填)
    - **verification_code**: 短信验证码 (验证码登录时必填)

    密码和验证码至少提供一个
    """
    # 密码登录
    if request.password:
        success, message, token_data = await auth_service.login_with_password(
            phone=request.phone,
            password=request.password,
        )
    # 验证码登录
    elif request.verification_code:
        success, message, token_data = await auth_service.login_with_code(
            phone=request.phone,
            verification_code=request.verification_code,
        )
    else:
        raise HTTPException(status_code=400, detail="密码和验证码至少提供一个")

    if not success:
        raise HTTPException(status_code=401, detail=message)

    return TokenResponse(**token_data)


@router.post("/send-code", response_model=MessageResponse, summary="发送验证码")
async def send_verification_code(
    request: SendVerificationCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    发送短信验证码

    - **phone**: 手机号
    - **purpose**: 用途
      - register: 注册
      - login: 登录
      - reset_password: 重置密码
    """
    success, message = await auth_service.send_verification_code(
        phone=request.phone,
        purpose=request.purpose,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return MessageResponse(message=message, success=True)


@router.post("/reset-password", response_model=MessageResponse, summary="重置密码")
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    重置密码（忘记密码时使用）

    - **phone**: 手机号
    - **verification_code**: 短信验证码
    - **new_password**: 新密码 (6-50字符)
    """
    success, message = await auth_service.reset_password(
        phone=request.phone,
        verification_code=request.verification_code,
        new_password=request.new_password,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return MessageResponse(message=message, success=True)


@router.post("/change-password", response_model=MessageResponse, summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    修改密码（已登录用户）

    需要提供 Authorization Header: Bearer {token}

    - **old_password**: 旧密码
    - **new_password**: 新密码 (6-50字符)
    """
    success, message = await auth_service.change_password(
        user_id=user_id,
        old_password=request.old_password,
        new_password=request.new_password,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return MessageResponse(message=message, success=True)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    获取当前登录用户信息

    需要提供 Authorization Header: Bearer {token}
    """
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse, summary="更新用户信息")
async def update_user_profile(
    request: UserProfileUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    更新当前用户信息

    需要提供 Authorization Header: Bearer {token}

    - **nickname**: 昵称 (可选)
    - **email**: 邮箱 (可选)
    - **avatar_url**: 头像URL (可选)
    """
    success, message, user = await auth_service.update_user_profile(
        user_id=user_id,
        nickname=request.nickname,
        email=request.email,
        avatar_url=request.avatar_url,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return UserResponse.model_validate(user)


@router.post("/logout", response_model=MessageResponse, summary="登出")
async def logout(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登出（使当前会话失效）

    需要提供 Authorization Header: Bearer {token}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    token = authorization.replace("Bearer ", "")
    success, message = await auth_service.logout(token)

    return MessageResponse(message=message, success=True)
