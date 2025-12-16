"""
Market Data Services 初始化文件

提供统一的市场数据接口:
- akshare_client: 纯 akshare 数据 (部分接口不稳定)
- mock_data_service: 纯模拟数据 (用于测试)
- hybrid_data_service: 混合数据服务 (推荐使用)
"""

from .akshare_client import akshare_client
from .mock_data_service import mock_data_service
from .hybrid_data_service import hybrid_data_service

# 默认导出混合服务 (根据接口稳定性自动选择数据源)
__all__ = [
    'hybrid_data_service',  # 推荐使用
    'akshare_client',       # 仅在需要强制使用 akshare 时使用
    'mock_data_service',    # 仅在测试时使用
]
