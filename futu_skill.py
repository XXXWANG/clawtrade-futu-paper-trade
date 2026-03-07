import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_python_version(python_cmd):
    try:
        output = subprocess.check_output(
            [python_cmd, "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
            text=True,
        ).strip()
    except Exception:
        return None
    parts = output.split(".")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def is_compatible_python(version_tuple):
    if not version_tuple:
        return False
    major, minor = version_tuple
    return major == 3 and minor in {10, 11, 12}


def select_python():
    current = (sys.version_info[0], sys.version_info[1])
    if is_compatible_python(current):
        return sys.executable
    candidates = ["python3.12", "python3.11", "python3.10", "python3", "python"]
    for candidate in candidates:
        version = get_python_version(candidate)
        if is_compatible_python(version):
            return candidate
    json_out(
        {
            "ok": False,
            "error": "未找到兼容 futu-api 的 Python 版本",
            "next_steps": [
                "请安装 Python 3.10/3.11/3.12",
                "安装后重新运行本技能",
            ],
        },
        1,
    )


def ensure_venv():
    if os.environ.get("FUTU_SKILL_VENV") == "1":
        return
    base_dir = Path(__file__).resolve().parent
    venv_dir = base_dir / ".venv"
    python_path = venv_dir / "bin" / "python"
    pip_path = venv_dir / "bin" / "pip"
    if sys.platform.startswith("win"):
        python_path = venv_dir / "Scripts" / "python.exe"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    python_cmd = select_python()
    if python_path.exists():
        venv_version = get_python_version(str(python_path))
        if not is_compatible_python(venv_version):
            shutil.rmtree(venv_dir, ignore_errors=True)
    if not python_path.exists():
        subprocess.check_call([python_cmd, "-m", "venv", str(venv_dir)])
    if not pip_path.exists():
        raise RuntimeError("虚拟环境创建失败")
    requirements = base_dir / "requirements.txt"
    subprocess.check_call([str(pip_path), "install", "-r", str(requirements)])
    env = os.environ.copy()
    env["FUTU_SKILL_VENV"] = "1"
    subprocess.check_call([str(python_path), str(Path(__file__).resolve()), *sys.argv[1:]], env=env)
    sys.exit(0)


def load_futu():
    from futu import (
        OpenQuoteContext,
        OpenTradeContext,
        TrdEnv,
        TrdMarket,
        TrdSide,
        OrderType,
        OrderStatus,
        ModifyOrderOp,
    )

    return (
        OpenQuoteContext,
        OpenTradeContext,
        TrdEnv,
        TrdMarket,
        TrdSide,
        OrderType,
        OrderStatus,
        ModifyOrderOp,
    )


def get_env(name, default=None):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


def parse_trd_env(trd_env):
    _, _, TrdEnv, _, _, _, _, _ = load_futu()
    env = trd_env.upper()
    if env == "REAL":
        json_out({"ok": False, "error": "本技能仅支持纸面交易，不允许 REAL"}, 1)
    if env in {"PAPER", "SIMULATE"}:
        return TrdEnv.SIMULATE
    return TrdEnv.SIMULATE


def parse_trd_market(trd_market):
    _, _, _, TrdMarket, _, _, _, _ = load_futu()
    mapping = {
        "HK": TrdMarket.HK,
        "US": TrdMarket.US,
        "CN": TrdMarket.CN,
        "HKCC": TrdMarket.HKCC,
        "USCC": TrdMarket.USCC,
    }
    return mapping.get(trd_market.upper(), TrdMarket.HK)


def json_out(payload, exit_code=0):
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(exit_code)


def open_contexts(host, port):
    OpenQuoteContext, OpenTradeContext, _, _, _, _, _, _ = load_futu()
    quote_ctx = OpenQuoteContext(host=host, port=port)
    trade_ctx = OpenTradeContext(host=host, port=port)
    return quote_ctx, trade_ctx


def close_contexts(quote_ctx, trade_ctx):
    try:
        quote_ctx.close()
    finally:
        trade_ctx.close()


def cmd_quote(args):
    host = get_env("FUTU_HOST", "127.0.0.1")
    port = int(get_env("FUTU_PORT", "11111"))
    symbols = args.symbols
    quote_ctx, trade_ctx = open_contexts(host, port)
    try:
        ret, data = quote_ctx.get_stock_quote(symbols)
        if ret != 0:
            json_out({"ok": False, "error": str(data)}, 1)
        json_out({"ok": True, "data": data.to_dict("records")})
    finally:
        close_contexts(quote_ctx, trade_ctx)


def cmd_positions(args):
    host = get_env("FUTU_HOST", "127.0.0.1")
    port = int(get_env("FUTU_PORT", "11111"))
    trd_env = parse_trd_env(get_env("FUTU_TRD_ENV", "SIMULATE"))
    trd_market = parse_trd_market(get_env("FUTU_TRD_MARKET", "HK"))
    quote_ctx, trade_ctx = open_contexts(host, port)
    try:
        ret, data = trade_ctx.position_list(trd_env=trd_env, trd_market=trd_market)
        if ret != 0:
            json_out({"ok": False, "error": str(data)}, 1)
        json_out({"ok": True, "data": data.to_dict("records")})
    finally:
        close_contexts(quote_ctx, trade_ctx)


def unlock_trade(trade_ctx):
    _, _, _, _, _, _, _, _ = load_futu()
    password = get_env("FUTU_TRADE_PWD", get_env("FUTU_PASSWORD", ""))
    if not password:
        json_out({"ok": False, "error": "缺少 FUTU_TRADE_PWD"}, 1)
    ret, data = trade_ctx.unlock_trade(password)
    if ret != 0:
        json_out({"ok": False, "error": str(data)}, 1)


def cmd_order(args, side):
    host = get_env("FUTU_HOST", "127.0.0.1")
    port = int(get_env("FUTU_PORT", "11111"))
    trd_env = parse_trd_env(get_env("FUTU_TRD_ENV", "SIMULATE"))
    trd_market = parse_trd_market(get_env("FUTU_TRD_MARKET", "HK"))
    symbol = args.symbol
    price = float(args.price)
    qty = int(args.qty)
    order_type = args.order_type.lower()
    _, _, _, _, TrdSide, OrderType, _, _ = load_futu()
    quote_ctx, trade_ctx = open_contexts(host, port)
    try:
        unlock_trade(trade_ctx)
        if order_type == "market":
            order_type_value = OrderType.MARKET
        else:
            order_type_value = OrderType.NORMAL
        ret, data = trade_ctx.place_order(
            price=price,
            qty=qty,
            code=symbol,
            trd_side=TrdSide.BUY if side == "buy" else TrdSide.SELL,
            order_type=order_type_value,
            trd_env=trd_env,
            trd_market=trd_market,
        )
        if ret != 0:
            json_out({"ok": False, "error": str(data)}, 1)
        json_out({"ok": True, "data": data.to_dict("records")})
    finally:
        close_contexts(quote_ctx, trade_ctx)


def parse_status_filter(status):
    _, _, _, _, _, _, OrderStatus, _ = load_futu()
    if status.lower() in {"all", "any"}:
        return []
    name = status.upper()
    if hasattr(OrderStatus, name):
        return [getattr(OrderStatus, name)]
    return None


def cmd_orders(args):
    host = get_env("FUTU_HOST", "127.0.0.1")
    port = int(get_env("FUTU_PORT", "11111"))
    trd_env = parse_trd_env(get_env("FUTU_TRD_ENV", "SIMULATE"))
    trd_market = parse_trd_market(get_env("FUTU_TRD_MARKET", "HK"))
    status_filter = parse_status_filter(args.status)
    if status_filter is None:
        json_out({"ok": False, "error": "无效的订单状态"}, 1)
    quote_ctx, trade_ctx = open_contexts(host, port)
    try:
        ret, data = trade_ctx.order_list_query(
            order_id=args.order_id or "",
            order_market=trd_market,
            status_filter_list=status_filter,
            code=args.symbol or "",
            start=args.start or "",
            end=args.end or "",
            trd_env=trd_env,
            refresh_cache=args.refresh_cache,
        )
        if ret != 0:
            json_out({"ok": False, "error": str(data)}, 1)
        json_out({"ok": True, "data": data.to_dict("records")})
    finally:
        close_contexts(quote_ctx, trade_ctx)


def cmd_cancel(args):
    host = get_env("FUTU_HOST", "127.0.0.1")
    port = int(get_env("FUTU_PORT", "11111"))
    trd_env = parse_trd_env(get_env("FUTU_TRD_ENV", "SIMULATE"))
    _, _, _, _, _, _, _, ModifyOrderOp = load_futu()
    quote_ctx, trade_ctx = open_contexts(host, port)
    try:
        unlock_trade(trade_ctx)
        ret, data = trade_ctx.modify_order(
            ModifyOrderOp.CANCEL,
            args.order_id,
            0,
            0,
            trd_env=trd_env,
        )
        if ret != 0:
            json_out({"ok": False, "error": str(data)}, 1)
        json_out({"ok": True, "data": data.to_dict("records")})
    finally:
        close_contexts(quote_ctx, trade_ctx)


def cmd_fills(args):
    host = get_env("FUTU_HOST", "127.0.0.1")
    port = int(get_env("FUTU_PORT", "11111"))
    trd_env = parse_trd_env(get_env("FUTU_TRD_ENV", "SIMULATE"))
    trd_market = parse_trd_market(get_env("FUTU_TRD_MARKET", "HK"))
    days = int(args.days)
    _, _, TrdEnv, _, _, _, _, _ = load_futu()
    quote_ctx, trade_ctx = open_contexts(host, port)
    try:
        if days <= 1:
            ret, data = trade_ctx.deal_list_query(
                code=args.symbol or "",
                deal_market=trd_market,
                trd_env=trd_env,
                refresh_cache=args.refresh_cache,
            )
        else:
            if trd_env == TrdEnv.SIMULATE:
                json_out({"ok": False, "error": "纸面交易环境不支持历史成交查询"}, 1)
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days - 1)
            ret, data = trade_ctx.history_deal_list_query(
                code=args.symbol or "",
                deal_market=trd_market,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                trd_env=trd_env,
            )
        if ret != 0:
            json_out({"ok": False, "error": str(data)}, 1)
        json_out({"ok": True, "data": data.to_dict("records")})
    finally:
        close_contexts(quote_ctx, trade_ctx)


def cmd_check(args):
    host = get_env("FUTU_HOST", "127.0.0.1")
    port = int(get_env("FUTU_PORT", "11111"))
    download_url = "https://www.futuhk.com/en/support/topic1_464"
    quote_ctx, trade_ctx = open_contexts(host, port)
    try:
        ret, data = quote_ctx.get_global_state()
        if ret != 0:
            json_out(
                {
                    "ok": False,
                    "error": str(data),
                    "next_steps": [
                        "请确认 FutuOpenD 已启动并保持运行",
                        "下载入口: " + download_url,
                        "命令行登录示例: ./FutuOpenD -login_account=YOUR_ID -login_pwd=YOUR_PASSWORD",
                        "避免使用 XML 保存密码",
                    ],
                },
                1,
            )
        json_out({"ok": True, "data": data.to_dict("records")})
    except Exception as exc:
        json_out(
            {
                "ok": False,
                "error": str(exc),
                "next_steps": [
                    "请确认 FutuOpenD 已启动并保持运行",
                    "下载入口: " + download_url,
                    "命令行登录示例: ./FutuOpenD -login_account=YOUR_ID -login_pwd=YOUR_PASSWORD",
                    "避免使用 XML 保存密码",
                ],
            },
            1,
        )
    finally:
        close_contexts(quote_ctx, trade_ctx)


def build_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    quote = sub.add_parser("quote")
    quote.add_argument("--symbols", nargs="+", required=True)
    quote.set_defaults(func=cmd_quote)

    positions = sub.add_parser("positions")
    positions.set_defaults(func=cmd_positions)

    buy = sub.add_parser("buy")
    buy.add_argument("--symbol", required=True)
    buy.add_argument("--qty", required=True)
    buy.add_argument("--price", required=True)
    buy.add_argument("--order-type", default="limit")
    buy.set_defaults(func=lambda args: cmd_order(args, "buy"))

    sell = sub.add_parser("sell")
    sell.add_argument("--symbol", required=True)
    sell.add_argument("--qty", required=True)
    sell.add_argument("--price", required=True)
    sell.add_argument("--order-type", default="limit")
    sell.set_defaults(func=lambda args: cmd_order(args, "sell"))

    orders = sub.add_parser("orders")
    orders.add_argument("--status", default="all")
    orders.add_argument("--symbol")
    orders.add_argument("--order-id")
    orders.add_argument("--start")
    orders.add_argument("--end")
    orders.add_argument("--refresh-cache", action="store_true")
    orders.set_defaults(func=cmd_orders)

    cancel = sub.add_parser("cancel")
    cancel.add_argument("--order-id", required=True)
    cancel.set_defaults(func=cmd_cancel)

    fills = sub.add_parser("fills")
    fills.add_argument("--days", default="1")
    fills.add_argument("--symbol")
    fills.add_argument("--refresh-cache", action="store_true")
    fills.set_defaults(func=cmd_fills)

    check = sub.add_parser("check")
    check.set_defaults(func=cmd_check)
    return parser


def main():
    ensure_venv()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        json_out({"ok": False, "error": str(exc)}, 1)
