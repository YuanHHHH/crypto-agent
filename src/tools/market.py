import os
import requests
from dotenv import load_dotenv
from src.utils.decorators import retry

load_dotenv()

@retry
def get_market_overview() -> dict:
    """
    :return:
    """
    cg_base_url = os.environ.get("CG_BASE_URL")
    url = f"{cg_base_url}/global"
    api_key = os.environ.get("CG_API")
    headers = {
        "x-cg-demo-api-key": api_key,
    }
    global_data = requests.get(url, headers=headers).json()

    data = global_data["data"]
    res = {
        "total_market_cap_usd": data["total_market_cap"]["usd"],
        "total_volume_usd": data["total_volume"]["usd"],
        "btc_dominance": data["market_cap_percentage"]["btc"],
        "eth_dominance": data["market_cap_percentage"]["eth"],
        "market_cap_change_24h": data["market_cap_change_percentage_24h_usd"],
        "active_cryptocurrencies": data["active_cryptocurrencies"],
    }
    return res

@retry
def get_coin_market(coin_id: str) -> dict:
    """查询单个币种的详细市场数据"""
    cg_base_url = os.environ.get("CG_BASE_URL")
    url = f"{cg_base_url}/coins/markets"
    api_key = os.environ.get("CG_API")
    headers = {"x-cg-demo-api-key": api_key}
    params = {
        "vs_currency": "usd",
        "ids": coin_id,
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()[0]
    res = {
        "symbol": data["symbol"],
        "market_cap": data["market_cap"],
        "total_volume": data["total_volume"],
        "high_24h": data["high_24h"],
        "low_24h": data["low_24h"],
        "price_change_24h": data["price_change_24h"],
        "ath": data["ath"],
    }
    return res