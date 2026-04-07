from src.tools.price import get_crypto_price
from src.tools.market import get_coin_market
from src.tools.llm_client import llm_client
def analyze_coin(symbol):
    coin_price = get_crypto_price(symbol)
    coin_market = get_coin_market(symbol)
    prompt = (
        f"你是一个专业的加密货币数据分析师。请分析 {symbol} 的当前行情。\n\n"
        f"价格数据：\n"
        f"- 当前价格: ${coin_price['price']}\n"
        f"- 24h涨跌幅: {coin_price['change_24h']:.2f}%\n\n"
        f"市场数据：\n"
        f"- 市值: ${coin_market['market_cap']:,.0f}\n"
        f"- 24h成交量: ${coin_market['total_volume']:,.0f}\n"
        f"- 24h最高价: ${coin_market['high_24h']}\n"
        f"- 24h最低价: ${coin_market['low_24h']}\n"
        f"- 历史最高价(ATH): ${coin_market['ath']}\n"
    )
    analysis = llm_client(prompt)
    return analysis