from src.tools.price import get_crypto_price
from src.utils.config import SUPPORTED_COINS

for coin in SUPPORTED_COINS:
    result = get_crypto_price(coin)
    print(result)