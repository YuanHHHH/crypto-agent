from src.tools.price import get_crypto_price,get_multiple_prices
from src.tools.market import get_market_overview,get_coin_market
from src.tools.analyzer import analyze_coin
from src.tools.llm_client import llm_client

choice = input("What would you like to do?\n 1. get price \n 2. get overview\n 3. AI Analyze \n")

while True:
    if choice == "1":
        coin = input("输入币种名称 (如 bitcoin): \n")
        result = get_crypto_price(coin)
        print(result)

    elif choice == "2":
        overview = get_market_overview()
        print(overview)

    elif choice == "3":
        coin = input("AI分析代币，请输入币种名称 (如 bitcoin): ")
        prompt = analyze_coin(coin)
        llm_client(prompt)

    elif choice == "4":
        print("退出")
        break

    else:
        print("Please enter a valid choice")
    choice = input("What would you like to do?\n 1. get price \n 2. get overview\n 3. AI Analyze\n")