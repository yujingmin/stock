"""
用户认证相关的 Pydantic schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    verification_code: Optional[str] = Field(None, description="短信验证码（可选）")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    phone: str = Field(..., description="手机号")
    password: Optional[str] = Field(None, description="密码")
    verification_code: Optional[str] = Field(None, description="短信验证码")

    @model_validator(mode='after')
    def validate_login(self):
        # 密码和验证码至少提供一个
        if not self.password and not self.verification_code:
            raise ValueError('密码和验证码至少提供一个')
        return self


class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    purpose: str = Field(..., description="用途: register/login/reset_password")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    verification_code: str = Field(..., description="短信验证码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class ChangePasswordRequest(BaseModel):
    """修改密码请求（已登录）"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    phone: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    vip_level: int
    vip_expire_at: Optional[datetime] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """用户信息更新请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    avatar_url: Optional[str] = Field(None, description="头像URL")


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True
