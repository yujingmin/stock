## ADDED Requirements

### Requirement: 多市场实时行情数据接入
The system MUST provide real-time market data from multiple markets (stocks, futures, forex) with latency ≤50ms, synchronized with exchanges. 系统必须提供股票、期货、外汇等多市场的实时行情数据，延迟不超过50毫秒，数据与交易所保持同步一致。

#### Scenario: 获取A股实时行情
- **WHEN** 用户请求查询A股某只股票的实时行情数据
- **THEN** 系统应返回该股票的最新价格、涨跌幅、成交量、买卖五档等信息
- **AND** 数据延迟不超过50毫秒
- **AND** 数据与交易所实时数据保持一致

#### Scenario: 订阅多市场行情推送
- **WHEN** 用户订阅股票、期货、外汇等多个市场的行情推送
- **THEN** 系统应实时推送各市场的价格变动信息
- **AND** 推送延迟不超过50毫秒

### Requirement: 基础数据管理
The system MUST provide financial statements (quarterly/annual), earnings forecasts, and macroeconomic indicators (GDP/CPI), with update frequency synchronized with official sources and data traceability. 系统必须提供上市公司财务报表（季度/年度）、业绩预告、宏观经济指标（GDP/CPI等），数据更新频率与官方同步，并提供数据溯源功能。

#### Scenario: 获取财务报表数据
- **WHEN** 用户查询某上市公司的季度或年度财务报表
- **THEN** 系统应返回该公司的资产负债表、利润表、现金流量表
- **AND** 数据更新频率与官方发布同步
- **AND** 提供数据来源溯源信息

#### Scenario: 查询宏观经济指标
- **WHEN** 用户查询GDP、CPI等宏观经济指标
- **THEN** 系统应返回最新的宏观经济数据
- **AND** 标注数据发布时间与来源机构

### Requirement: 量化因子数据库
The system MUST include built-in quantitative factors (MACD/KDJ), financial factors (P/E ratio/dividend yield), alternative factors (sentiment/capital flow), and SHALL support custom factor uploads. 系统必须内置量价因子（MACD/KDJ等）、财务因子（市盈率/股息率等）、另类因子（舆情/资金流向），并支持用户自定义因子上传。

#### Scenario: 获取内置量价因子
- **WHEN** 用户请求计算某股票的MACD或KDJ指标
- **THEN** 系统应基于历史行情数据计算并返回对应因子值
- **AND** 因子计算逻辑准确无误

#### Scenario: 上传自定义因子
- **WHEN** 用户上传自定义因子的计算代码（Python）
- **THEN** 系统应保存该因子并支持在策略开发中调用
- **AND** 提供因子计算结果验证功能

### Requirement: 历史数据查询与导出
The system MUST provide at least 10 years of daily/minute-level historical data, support export by market and time range, with formats compatible with Excel/Python dataframes. 系统必须提供至少10年的日度/分钟级历史数据，支持按市场、时间区间导出，格式兼容Excel/Python数据框架。

#### Scenario: 查询历史K线数据
- **WHEN** 用户查询某股票近10年的日K线数据
- **THEN** 系统应返回该股票的开盘价、收盘价、最高价、最低价、成交量等历史数据
- **AND** 数据完整无缺失

#### Scenario: 导出历史数据
- **WHEN** 用户选择时间区间并导出历史数据
- **THEN** 系统应生成Excel或CSV格式文件供下载
- **AND** 数据格式兼容Pandas等Python数据框架

### Requirement: 数据可视化
The system MUST support visualization of K-line charts, factor distribution heatmaps, and return curves, with customizable indicator overlays and period switching. 系统必须支持K线图、因子分布热力图、收益曲线等图表展示，可自定义指标叠加与周期切换。

#### Scenario: 展示K线图
- **WHEN** 用户查看某股票的K线图
- **THEN** 系统应展示包含价格、成交量的K线图表
- **AND** 支持叠加MACD、均线等技术指标
- **AND** 支持切换日K、周K、分钟K等周期

#### Scenario: 查看因子热力图
- **WHEN** 用户查看某因子在不同股票上的分布
- **THEN** 系统应展示因子值的热力图
- **AND** 颜色深浅反映因子数值大小

### Requirement: 数据筛选功能
The system MUST provide conditional screening功能 (e.g., "P/E<20 AND dividend yield>3%") for quick stock pool generation, and SHALL support saving screening rules. 系统必须提供条件筛选功能，如"市盈率<20且股息率>3%"的股票池快速生成，支持保存筛选规则。

#### Scenario: 根据条件筛选股票
- **WHEN** 用户设置筛选条件"市盈率<20且股息率>3%"
- **THEN** 系统应返回符合条件的所有股票列表
- **AND** 支持保存该筛选规则以便后续复用

### Requirement: 第三方数据源接入
The system MUST provide open API interfaces to support user integration of proprietary data sources or third-party data providers (e.g., Wind). 系统必须开放API接口，支持用户接入自有数据源或第三方数据服务商（如Wind）的数据。

#### Scenario: 接入第三方数据API
- **WHEN** 用户配置第三方数据源的API密钥
- **THEN** 系统应成功连接该数据源并获取数据
- **AND** 数据与本地数据源格式统一
