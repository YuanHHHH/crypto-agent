from src.tools.price import get_crypto_price as _get_crypto_price
from src.tools.market import get_market_overview as _get_market_overview
from src.tools.market import get_coin_market as _get_coin_market
from src.tools.analyzer import analyze_coin as _analyze_coin
from langchain_core.tools import tool


@tool
def get_price(symbol: str) -> dict:
    """获得指定代币的实时价格数据。symbol 参数是币种英文名，如 bitcoin、ethereum、solana。"""
    return _get_crypto_price(symbol)


@tool
def get_market() -> dict:
    """获得整个加密货币市场的全局数据，包括总市值、BTC 占比、ETH 占比、24h 变化等。"""
    return _get_market_overview()


@tool
def get_coin_detail(coin_id: str) -> dict:
    """获得指定代币的详细市场数据，包括市值、成交量、24h 最高最低价、ATH。coin_id 参数是币种英文名，如 bitcoin、ethereum。"""
    return _get_coin_market(coin_id)


@tool
def analyze_coin(symbol: str) -> dict:
    """对指定币种进行深度行情分析，返回 AI 生成的完整分析报告。symbol 参数是币种英文名，如 bitcoin、ethereum。"""
    return _analyze_coin(symbol)


if __name__ == "__main__":
    print(get_price.invoke({"symbol": "bitcoin"}))
    print(get_market.invoke({}))
    print(get_coin_detail.invoke({"coin_id": "ethereum"}))
    print(analyze_coin.invoke({"symbol": "solana"}))