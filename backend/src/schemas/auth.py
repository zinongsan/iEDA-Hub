"""Auth 相关 Pydantic Schema"""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    sms_code: str = Field(..., min_length=6, max_length=6, description="手机验证码")
    agree_terms: bool = Field(..., description="是否同意用户协议")


class LoginRequest(BaseModel):
    """登录请求 - 支持用 邮箱 或 用户名 登录

    - account: 邮箱或用户名（推荐字段）
    - email:   旧字段，为兼容旧前端保留，作用同 account
    """
    account: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=1, max_length=120)
    password: str
    captcha_id: str | None = Field(default=None, description="验证码ID（失败3次后需要）")
    captcha_code: str | None = Field(default=None, description="验证码（失败3次后需要）")

    @property
    def identifier(self) -> str:
        return (self.account or self.email or "").strip()


class RefreshRequest(BaseModel):
    # 浏览器走 HttpOnly cookie 时可不传；API 客户端仍可放 body
    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str
