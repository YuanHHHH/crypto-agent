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