from src.tools.analyzer import analyze_coin

def test_analyze_coin():
    coin = "bitcoin"
    result = analyze_coin(coin)
    assert result is not None
