from decimal import MIN_EMIN, MAX_EMAX

import requests
import os
import json
import datetime

def retry(func):
    def wrapper(*args, **kwargs):
        max_times = 3
        for i in range(max_times):
            try:
                res = func(*args, **kwargs)
                return res
            except Exception as e:
                print(f"第{i+1}次失败：{e}")
    return wrapper

@retry
def get_crypto_price(symbol: str) -> dict:
    api_key = os.environ.get("CG_API","CG-PT7xKULi3XkZ5z3ung8Yho3K")
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    headers = {
        "x-cg-demo-api-key": api_key,
    }
    coin_price = requests.get(url, params=params, headers=headers)

    data = coin_price.json()
    if symbol in data:
        coin_data = data[symbol]
        res = {
            "symbol":symbol,
            "price": coin_data.get("usd",0),
            "change_24h": coin_data.get("usd_24h_change",0)
        }
        save_to_history("/Users/haoyuanhuang/PycharmProjects/crypto-agent/data/price_history.jsonl", res)
        return res
    else:
        return None

@retry
def get_multiple_prices(coin_list) -> dict:
    api_key = os.environ.get("CG_API", "CG-PT7xKULi3XkZ5z3ung8Yho3K")
    url = "https://api.coingecko.com/api/v3/simple/price"
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
            save_to_history("/Users/haoyuanhuang/PycharmProjects/crypto-agent/data/price_history.jsonl",para)
    return res

def save_to_history(file,record):
    record["time"] = str(datetime.datetime.now())
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "a") as f:
        f.write(json.dumps(record) + "\n")
        print("loaded successfully")

def load_price_history(file):
    try:
        with open(file, "r") as f:
            records = [json.loads(line) for line in f if line.strip()]
            return records
    except Exception as e:
        print(e)
        return []

def analyze_history(file,coin):
    records = load_price_history(file)
    max_price = float('-inf')
    min_price = float('inf')
    for record in records:
        if record["symbol"] == coin:
            max_price = max(record["price"], max_price)
            min_price = min(record["price"], min_price)
    return max_price, min_price