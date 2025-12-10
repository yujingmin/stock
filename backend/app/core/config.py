"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 项目信息
    PROJECT_NAME: str = "量化投资平台"
    VERSION: str = "1.0.0"

    # 数据库配置
    DATABASE_URL: str = "postgresql://quant_user:quant_password_dev@localhost:5432/quant_platform"
    MONGODB_URL: str = "mongodb://quant_user:quant_password_dev@localhost:27017/quant_platform"
    REDIS_URL: str = "redis://:quant_password_dev@localhost:6379/0"

    # InfluxDB 配置
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "quant_influxdb_token_dev"
    INFLUXDB_ORG: str = "quant_platform"
    INFLUXDB_BUCKET: str = "market_data"

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7

    # AES 加密密钥 (用于策略代码加密，必须是32字节)
    AES_ENCRYPTION_KEY: str = "change-this-key-32-bytes-long!!"

    # CORS 配置
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # 阿里云短信配置
    ALIYUN_SMS_ACCESS_KEY_ID: str = ""
    ALIYUN_SMS_ACCESS_KEY_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = ""
    ALIYUN_SMS_TEMPLATE_CODE: str = ""

    # 微信小程序配置
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # Redis 会话配置
    SESSION_EXPIRE_MINUTES: int = 30

    # API 限流配置
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
