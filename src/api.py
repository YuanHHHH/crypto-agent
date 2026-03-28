from fastapi import FastAPI
from src.tools.analyzer import analyze_coin
from src.tools.llm_client import llm_client
from src.models import PriceHistory, CoinPrice, MarketOverview, Analysis,CoinMarket
from src.tools.price import get_crypto_price,load_price_history,get_multiple_prices
from src.tools.market import get_market_overview, get_coin_market
import os
from dotenv import load_dotenv
from src.exception_handler import register_exception_handlers
from src.utils.config import HISTORY_FILE
load_dotenv()
app = FastAPI()
register_exception_handlers(app)

@app.get("/")
def root():
    return {"message": "Crypto Agent API is running"}

@app.get("/price/{coin}",response_model=CoinPrice)
def price_endpoint(coin:str):
    result = get_crypto_price(coin)
    return result

@app.get("/prices",response_model=list[CoinPrice])
def prices_endpoint(coins: str):
    coin_list = coins.split(",")
    result = get_multiple_prices(coin_list)
    return result

@app.get("/market",response_model=MarketOverview)
def get_market():
    result = get_market_overview()
    return result

@app.get("/history",response_model=list[PriceHistory])
def get_coins_history(coin:str = None, limit:int = 20):
    result = load_price_history(HISTORY_FILE)
    if not coin and not limit:
        return result
    elif coin:
        res = []
        for i in result:
            if i["symbol"] == coin:
                res.append(i)
        return res[:limit] if limit else res
    else:
        return result[:limit] if limit else result

@app.get("/coin_market",response_model=CoinMarket)
def coin_market(coin:str):
    result = get_coin_market(coin)
    return result

@app.get("/analyze/{coin}",response_model=Analysis)
def analyze_endpoint(coin: str):
    prompt = analyze_coin(coin)
    res = llm_client(prompt)
    return {
        "symbol": coin,
        "content": res
    }