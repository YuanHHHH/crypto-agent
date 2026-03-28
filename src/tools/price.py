import requests
import os
import json
import datetime
from dotenv import load_dotenv
from src.utils.exceptions import APIError, InvalidCoinError
from src.utils.decorators import retry
from src.utils.config import HISTORY_FILE
load_dotenv()


@retry
def get_crypto_price(symbol: str) -> dict:
    """
    :param symbol:
    :return:
    """
    api_key = os.environ.get("CG_API")
    cg_base_url = os.environ.get("CG_BASE_URL")
    url = f"{cg_base_url}/simple/price"
    params = {
        "ids": symbol,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    headers = {
        "x-cg-demo-api-key": api_key,
    }
    coin_price = requests.get(url, params=params, headers=headers)

    if coin_price.status_code != 200:
        raise APIError(coin_price.status_code)

    data = coin_price.json()

    if symbol not in data:
        raise InvalidCoinError(symbol)

    coin_data = data[symbol]
    res = {
        "symbol":symbol,
        "price": coin_data.get("usd",0),
        "change_24h": coin_data.get("usd_24h_change",0)
    }

    save_to_history(HISTORY_FILE, res)
    return res

@retry
def get_multiple_prices(coin_list) -> dict:
    """
    :param coin_list:
    :return:
    """
    api_key = os.environ.get("CG_API")
    cg_base_url = os.environ.get("CG_BASE_URL")
    url = f"{cg_base_url}/simple/price"
    ids_list = ",".join(coin_list)
    params = {
        "ids": ids_list,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    headers = {
        "x-cg-demo-api-key": api_key,
    }
    coin_price = requests.get(url, params=params, headers=headers)

    data = coin_price.json()
    res = []

    for coin in coin_list:
        if coin in data:
            coin_data = data[coin]
            para = {
                    "symbol": coin,
                    "price": coin_data.get("usd",0),
                    "change_24h": coin_data.get("usd_24h_change",0)
                }
            res.append(para)
            save_to_history(HISTORY_FILE,para)
    return res

def save_to_history(file,record):
    """
    :param file:
    :param record:
    :return:
    """
    record["time"] = str(datetime.datetime.now())
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "a") as f:
        f.write(json.dumps(record) + "\n")
        print("loaded successfully")

def load_price_history(file) -> list:
    """
    :param file:
    :return:
    """
    try:
        with open(file, "r") as f:
            records = [json.loads(line) for line in f if line.strip()]
            return records
    except Exception as e:
        print(e)
        return []

def analyze_history(file,coin) -> tuple:
    """
    :param file:
    :param coin:
    :return:
    """
    records = load_price_history(file)
    max_price = float('-inf')
    min_price = float('inf')
    for record in records:
        if record["symbol"] == coin:
            max_price = max(record["price"], max_price)
            min_price = min(record["price"], min_price)
    return max_price, min_price