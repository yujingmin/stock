"""
数据库连接管理模块
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from app.core.config import settings

# PostgreSQL 异步引擎
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
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
mongodb_client: AsyncIOMotorClient = None
mongodb_db = None

# Redis 客户端
redis_client: Redis = None

# InfluxDB 客户端
influxdb_client: InfluxDBClientAsync = None


async def init_db():
    """初始化所有数据库连接"""
    global mongodb_client, mongodb_db, redis_client, influxdb_client

    # 初始化 MongoDB
    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb_db = mongodb_client.get_default_database()

    # 初始化 Redis
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    # 初始化 InfluxDB
    influxdb_client = InfluxDBClientAsync(
        url=settings.INFLUXDB_URL,
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG,
    )


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
