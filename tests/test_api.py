from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Crypto Agent API is running"}

def test_price():
    response = client.get("/price/bitcoin")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "bitcoin"

def test_prices():
    response = client.get("/prices",params={"coins":"bitcoin,ethereum"})
    assert response.status_code == 200
    data = response.json()
    assert len(data)==2
    assert data[0]["symbol"] == "bitcoin"
    assert data[1]["symbol"] == "ethereum"

def test_market():
    responses = client.get("/market")
    assert responses.status_code == 200

def test_history():
    response = client.get("/history",params ={"coin":"bitcoin"})
    assert response.status_code == 200

def test_price_invalid_coin():
    response = client.get("/price/fakecoin123")
    assert response.status_code == 404

def test_coin_market():
    response = client.get("/coin_market", params={"coin": "bitcoin"})
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "btc"
    assert data["market_cap"] > 0

def test_analysis():
    response = client.get("/analyze/bitcoin")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "bitcoin"
    assert len(data["content"]) > 0