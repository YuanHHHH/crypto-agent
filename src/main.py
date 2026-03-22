from src.tools.price import get_crypto_price,get_multiple_prices
from src.tools.market import get_market_overview

choice = input("What would you like to do?\n 1. get price \n 2. get overview")

while True:
    if choice == "1":
        coin = input("输入币种名称 (如 bitcoin): ")
        result = get_crypto_price(coin)
        print(result)

        # results = get_multiple_prices(["bitcoin", "ethereum", "solana"])
        # for r in results:
        #     print(r)

    elif choice == "2":
        overview = get_market_overview()
        print(overview)

    elif choice == "3":
        print("退出")
        break

    else:
        print("Please enter a valid choice")