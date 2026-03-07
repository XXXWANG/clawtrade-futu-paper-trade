# XTrade Futu Paper Trade 🦎

> 港股模拟交易工具 - 让 AI 学会炒港股

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

XTrade Futu Paper Trade 是一个基于 **Futu OpenAPI** 的港股模拟交易工具，让 Claude AI 能够实时查看行情、管理仓位、执行模拟交易。

## ✨ 核心特性

### 📊 全方位行情数据
- **实时报价**：现价、涨跌、成交量
- **K线数据**：日线、周线、月线
- **财务数据**：资产负债表、利润表、现金流量表
- **财务指标**：PE、PB、ROE、周转率等

### 💼 完整账户管理
- 资金查询（现金、总资产）
- 持仓管理（成本价、盈亏比例）
- 历史成交记录
- 今日盈亏统计

### 🎯 模拟交易
- 市价下单 / 限价下单
- 买入 / 卖出
- 仓位控制提醒（单票≤15%）
- 安全限制：仅支持纸面交易

### 🛡️ 安全设计
- 纸面交易（Paper Trade）模式
- 不涉及真实资金
- 检测到 REAL 账户会拒绝执行

## 🚀 快速开始

### 环境要求
- Python 3.10+
- macOS / Linux / Windows
- FutuOpenD 运行中

### 安装

```bash
# 方式1：克隆仓库
git clone https://github.com/XXXWANG/xtrade-futu-paper-trade.git
cd xtrade-futu-paper-trade

# 方式2：复制到 OpenClaw
cp -r xtrade-futu-paper-trade ~/.openclaw/skills/
```

### 配置 FutuOpenD

1. 下载 FutuOpenD：https://www.futuhk.com/en/support/topic1_464
2. 启动服务（保持运行）：
   ```bash
   # Mac
   ./FutuOpenD_mac
   ```
3. 设置交易密码（首次）

### 基本使用

```bash
# 环境检查
python3 xtrade_futu_skill.py check

# 查询账户资金
python3 xtrade_futu_skill.py funds

# 查询实时行情
python3 xtrade_futu_skill.py quote --symbols HK.00700 HK.09988 HK.01810

# 查看持仓
python3 xtrade_futu_skill.py positions

# 买入股票（市价）
python3 xtrade_futu_skill.py buy --symbol HK.00700 --qty 100

# 买入股票（限价）
python3 xtrade_futu_skill.py buy --symbol HK.00700 --qty 100 --price 520.0

# 卖出股票
python3 xtrade_futu_skill.py sell --symbol HK.00700 --qty 50 --price 530.0

# 查询财务指标
python3 xtrade_futu_skill.py financial-indicators --code HK.00700

# 撤销订单
python3 xtrade_futu_skill.py cancel --order_id 123456

# 今日盈亏
python3 xtrade_futu_skill.py today-pnl
```

## 📖 命令详解

### 行情查询
| 命令 | 说明 |
|------|------|
| `quote` | 实时报价 |
| `kline` | K线数据 |
| `financial-statement` | 财务报表 |
| `financial-indicators` | 财务指标 |

### 交易操作
| 命令 | 说明 |
|------|------|
| `buy` | 买入 |
| `sell` | 卖出 |
| `cancel` | 撤销订单 |
| `modify` | 修改订单 |

### 账户查询
| 命令 | 说明 |
|------|------|
| `funds` | 资金状况 |
| `positions` | 当前持仓 |
| `orders` | 今日订单 |
| `today-pnl` | 今日盈亏 |

## 📊 输出示例

### 行情查询
```json
{
  "ok": true,
  "data": [
    {
      "symbol": "HK.00700",
      "name": "腾讯控股",
      "price": 519.0,
      "change": -12.5,
      "change_pct": -2.35,
      "volume": 12500000,
      "turnover": 6475000000
    }
  ]
}
```

### 持仓查询
```json
{
  "ok": true,
  "positions": [
    {
      "symbol": "HK.00700",
      "name": "腾讯控股",
      "qty": 500,
      "cost": 597.7,
      "current": 519.0,
      "pnl_pct": -13.17,
      "market_value": 259500
    }
  ]
}
```

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FUTU_HOST` | FutuOpenD 地址 | 127.0.0.1 |
| `FUTU_PORT` | FutuOpenD 端口 | 11111 |
| `FUTU_TRD_ENV` | 交易环境 | PAPER |
| `FUTU_TRD_MARKET` | 交易市场 | HK |
| `FUTU_TRADE_PWD` | 交易密码 | - |

## 🔄 配合 XTrade 使用

推荐组合工作流：

```
┌─────────────────────────────────────────────────┐
│  XTrade Opportunity Screener                    │
│  → 筛选候选股票                                  │
│         ↓                                        │
│  XTrade Futu Paper Trade                        │
│  → 验证行情、执行交易                            │
│         ↓                                        │
│  30天模拟挑战 → 持续盈利                         │
└─────────────────────────────────────────────────┘
```

## 📦 相关项目

- [xtrade-opportunity-screener](https://github.com/XXXWANG/xtrade-opportunity-screener) - 智能选股
- [xtrade](https://github.com/XXXWANG/xtrade) - 技能箱主页

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

**🦎 让 AI 成为你的港股交易助手**
