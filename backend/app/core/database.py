"""
数据库连接管理模块
"""
from typing import Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# 条件导入可选数据库驱动
try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    AsyncIOMotorClient = None

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None

try:
    from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
except ImportError:
    InfluxDBClientAsync = None

# PostgreSQL 异步引擎
# 尝试使用 asyncpg，如果没有则使用 psycopg
db_url = settings.DATABASE_URL
if "postgresql://" in db_url and "+asyncpg" not in db_url and "+psycopg" not in db_url:
    # 尝试 asyncpg
    try:
        import asyncpg
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    except ImportError:
        # 使用 psycopg
        try:
            import psycopg
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
        except ImportError:
            raise ImportError("需要安装 asyncpg 或 psycopg 作为 PostgreSQL 驱动")

engine = create_async_engine(
    db_url,
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# MongoDB 客户端
mongodb_client: Optional[Any] = None
mongodb_db: Optional[Any] = None

# Redis 客户端
redis_client: Optional[Any] = None

# InfluxDB 客户端
influxdb_client: Optional[Any] = None


async def init_db():
    """初始化所有数据库连接"""
    global mongodb_client, mongodb_db, redis_client, influxdb_client

    # 初始化 MongoDB（可选）
    if settings.MONGODB_ENABLED:
        if AsyncIOMotorClient is None:
            print("[ERROR] MongoDB 驱动未安装，请执行: pip install motor")
        else:
            try:
                mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
                mongodb_db = mongodb_client.get_default_database()
                print("[OK] MongoDB 连接成功")
            except Exception as e:
                print(f"[ERROR] MongoDB 连接失败: {e}")
    else:
        print("[DISABLED] MongoDB 已禁用")

    # 初始化 Redis（可选）
    if settings.REDIS_ENABLED:
        if Redis is None:
            print("[ERROR] Redis 驱动未安装，请执行: pip install redis")
        else:
            try:
                redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await redis_client.ping()
                print("[OK] Redis 连接成功")
            except Exception as e:
                print(f"[ERROR] Redis 连接失败: {e}")
    else:
        print("[DISABLED] Redis 已禁用")

    # 初始化 InfluxDB（可选）
    if settings.INFLUXDB_ENABLED:
        if InfluxDBClientAsync is None:
            print("[ERROR] InfluxDB 驱动未安装，请执行: pip install influxdb-client")
        else:
            try:
                influxdb_client = InfluxDBClientAsync(
                    url=settings.INFLUXDB_URL,
                    token=settings.INFLUXDB_TOKEN,
                    org=settings.INFLUXDB_ORG,
                )
                print("[OK] InfluxDB 连接成功")
            except Exception as e:
                print(f"[ERROR] InfluxDB 连接失败: {e}")
    else:
        print("[DISABLED] InfluxDB 已禁用")


async def get_db() -> AsyncSession:
    """获取 PostgreSQL 数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_mongodb():
    """获取 MongoDB 数据库"""
    return mongodb_db


def get_redis():
    """获取 Redis 客户端"""
    return redis_client


def get_influxdb():
    """获取 InfluxDB 客户端"""
    return influxdb_client
