"""
InfluxDB 时序数据存储服务
用于存储和查询历史 K 线数据
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app.core.database import get_influxdb
from app.core.config import settings

logger = logging.getLogger(__name__)


class InfluxDBService:
    """InfluxDB 时序数据服务"""

    def __init__(self):
        self.bucket = settings.INFLUXDB_BUCKET
        self.org = settings.INFLUXDB_ORG

    async def write_kline_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        period: str = "daily"
    ) -> bool:
        """
        写入 K 线数据到 InfluxDB

        Args:
            symbol: 股票代码
            df: K线数据 DataFrame，必须包含 date, open, high, low, close, volume 列
            period: 周期（daily, weekly, monthly, 1min, 5min 等）

        Returns:
            是否成功
        """
        try:
            client = get_influxdb()
            write_api = client.write_api(write_options=SYNCHRONOUS)

            points = []
            for _, row in df.iterrows():
                # 转换日期为时间戳
                if isinstance(row['date'], str):
                    timestamp = datetime.strptime(row['date'], "%Y-%m-%d")
                else:
                    timestamp = row['date']

                point = (
                    Point("kline")
                    .tag("symbol", symbol)
                    .tag("period", period)
                    .field("open", float(row.get('open', 0)))
                    .field("high", float(row.get('high', 0)))
                    .field("low", float(row.get('low', 0)))
                    .field("close", float(row.get('close', 0)))
                    .field("volume", float(row.get('volume', 0)))
                    .field("amount", float(row.get('amount', 0)))
                    .field("change_percent", float(row.get('change_percent', 0)))
                    .time(timestamp)
                )
                points.append(point)

            write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.info(f"成功写入 {len(points)} 条 K 线数据: {symbol} ({period})")
            return True

        except Exception as e:
            logger.error(f"写入 K 线数据失败: {str(e)}")
            return False

    async def query_kline_data(
        self,
        symbol: str,
        period: str = "daily",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        查询 K 线数据

        Args:
            symbol: 股票代码
            period: 周期
            start_time: 开始时间
            end_time: 结束时间
            limit: 最大返回条数

        Returns:
            K 线数据 DataFrame
        """
        try:
            client = get_influxdb()
            query_api = client.query_api()

            # 构建查询
            time_filter = ""
            if start_time:
                time_filter += f' and r._time >= {start_time.isoformat()}Z'
            if end_time:
                time_filter += f' and r._time <= {end_time.isoformat()}Z'

            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -10y)
                |> filter(fn: (r) => r._measurement == "kline")
                |> filter(fn: (r) => r.symbol == "{symbol}")
                |> filter(fn: (r) => r.period == "{period}")
                {time_filter}
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> limit(n: {limit})
                |> sort(columns: ["_time"], desc: false)
            '''

            tables = query_api.query(query, org=self.org)

            # 转换为 DataFrame
            records = []
            for table in tables:
                for record in table.records:
                    records.append({
                        "date": record.get_time(),
                        "symbol": record.values.get("symbol"),
                        "period": record.values.get("period"),
                        "open": record.values.get("open"),
                        "high": record.values.get("high"),
                        "low": record.values.get("low"),
                        "close": record.values.get("close"),
                        "volume": record.values.get("volume"),
                        "amount": record.values.get("amount"),
                        "change_percent": record.values.get("change_percent"),
                    })

            df = pd.DataFrame(records)
            logger.info(f"查询到 {len(df)} 条 K 线数据: {symbol} ({period})")
            return df

        except Exception as e:
            logger.error(f"查询 K 线数据失败: {str(e)}")
            return pd.DataFrame()

    async def delete_kline_data(
        self,
        symbol: str,
        period: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> bool:
        """
        删除 K 线数据

        Args:
            symbol: 股票代码
            period: 周期，如果为 None 则删除所有周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            是否成功
        """
        try:
            client = get_influxdb()
            delete_api = client.delete_api()

            # 构建删除条件
            predicate = f'symbol="{symbol}"'
            if period:
                predicate += f' AND period="{period}"'

            # 设置时间范围
            if not start_time:
                start_time = datetime(1970, 1, 1)
            if not end_time:
                end_time = datetime.now()

            delete_api.delete(
                start_time,
                end_time,
                predicate,
                bucket=self.bucket,
                org=self.org
            )

            logger.info(f"删除 K 线数据: {symbol} ({period})")
            return True

        except Exception as e:
            logger.error(f"删除 K 线数据失败: {str(e)}")
            return False


# 全局服务实例
influx_service = InfluxDBService()
