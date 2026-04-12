from src.tools.price import get_crypto_price as _get_crypto_price
from src.tools.market import get_market_overview as _get_market_overview
from src.tools.market import get_coin_market as _get_coin_market
from src.tools.analyzer import analyze_coin as _analyze_coin
from langchain_core.tools import tool

import json


def _sanitize(raw: str) -> str:
    """清洗 LLM 输出的参数。

    LLM 可能输出三种形式：
    1. 纯字符串: bitcoin
    2. JSON 对象字符串: {"symbol": "bitcoin"}
    3. 污染字符串: bitcoin\n```\n[TOOL_CALL]...
    这个函数统一清洗成纯字符串。
    """
    if not isinstance(raw, str):
        return raw

    # 先取第一行，去掉污染
    cleaned = raw.split('\n')[0].strip().strip('`').strip()

    # 尝试解析 JSON 对象
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                # 取 dict 的第一个值
                return str(list(parsed.values())[0]).strip()
        except json.JSONDecodeError:
            pass

    # 去掉首尾引号
    return cleaned.strip('"').strip("'").strip()

@tool
def get_price(symbol: str) -> dict:
    """获得指定代币的实时价格数据。symbol 参数是币种英文名，如 bitcoin、ethereum、solana。"""
    return _get_crypto_price(_sanitize(symbol))


@tool
def get_market() -> dict:
    """获得整个加密货币市场的全局数据。"""
    return _get_market_overview()


@tool
def get_coin_detail(coin_id: str) -> dict:
    """获得指定代币的详细市场数据，coin_id 参数是币种英文名，如 bitcoin、ethereum。"""
    return _get_coin_market(_sanitize(coin_id))


@tool
def analyze_coin(symbol: str) -> dict:
    """对指定币种进行深度行情分析，symbol 参数是币种英文名，如 bitcoin、ethereum。"""
    return _analyze_coin(_sanitize(symbol))