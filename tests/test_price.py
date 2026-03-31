from src.tools.price import get_crypto_price,get_multiple_prices
import pytest
from src.utils.exceptions import InvalidCoinError
# 测试函数不接收参数，且要用assert断言来验证结果
def test_get_crypto_price_valid():
    res = get_crypto_price("bitcoin")
    assert res is not None
    assert "symbol" in res
    assert "price" in res
    assert "change_24h" in res
    assert res["symbol"] == "bitcoin"
    assert res["price"] >0

def test_get_crypto_price_invalid():
    with pytest.raises(InvalidCoinError):
        get_crypto_price("fakecooooin")

def test_get_multiple_crypto_price():
    res = get_multiple_prices(["bitcoin", "ethereum"])
    assert res is not None
    assert len(res) == 2