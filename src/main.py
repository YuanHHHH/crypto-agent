from src.tools.price import get_crypto_price,get_multiple_prices
from src.utils.config import SUPPORTED_COINS

result = get_crypto_price('bitcoin')
print(result)

results = get_multiple_prices(["bitcoin", "ethereum", "solana"])
for r in results:
    print(r)