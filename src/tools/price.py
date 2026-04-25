import requests
import os
import json
import datetime
from dotenv import load_dotenv
from src.utils.exceptions import APIError, InvalidCoinError
from src.utils.decorators import retry
from src.utils.config import HISTORY_FILE
import streamlit as st
load_dotenv()


@retry
def get_crypto_price(symbol: str) -> dict:
    """查询单个加密货币价格
    :param symbol:
    :return: 包含symbol, price, change_24h的dict
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
    print(f"[DEBUG] status={coin_price.status_code}")
    print(f"[DEBUG] headers={dict(coin_price.headers)}")
    print(f"[DEBUG] body={coin_price.text[:500]}")

    if coin_price.status_code != 200:
        raise APIError(coin_price.status_code)

    data = coin_price.json()
    print(f"[DEBUG] symbol={symbol}, data={data}")  # ← 加这一行

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
    """查询多个加密货币的价格
    :param coin_list:
    :return: 返回多个加密货币的列表，里面包含各代币的symbol, price, change_24h的dict
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
    """将记录追加到文件，并加入时间戳
    :param file:
    :param record:
    :return:None
    """
    record["time"] = str(datetime.datetime.now())
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "a") as f:
        f.write(json.dumps(record) + "\n")
        print("loaded successfully")

@st.cache_data(ttl=30)
def load_price_history(file) -> list:
    """加载某个代币的历史记录
    :param file:
    :return:返回查询到的某个代币的所有记录
    """
    try:
        with open(file, "r") as f:
            records = [json.loads(line) for line in f if line.strip()]
            return records
    except Exception as e:
        print(e)
        return []

def analyze_history(file,coin) -> tuple:
    """查询某代币记录里的最小最大值
    :param file:
    :param coin:
    :return: 返回记录中的最小值最大值
    """
    records = load_price_history(file)
    max_price = float('-inf')
    min_price = float('inf')
    for record in records:
        if record["symbol"] == coin:
            max_price = max(record["price"], max_price)
            min_price = min(record["price"], min_price)
    return max_price, min_price