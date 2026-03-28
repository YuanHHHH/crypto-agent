from src.tools.price import get_crypto_price
from src.tools.market import get_coin_market
def analyze_coin(symbol):
    coin_price = get_crypto_price(symbol)
    coin_market = get_coin_market(symbol)
    prompt = f"请分析 {symbol} 的当前行情。价格数据：{coin_price}，市场数据：{coin_market}"
    return prompt