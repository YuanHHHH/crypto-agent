from src.tools.price import get_crypto_price
from src.tools.market import get_market_overview,get_coin_market

class ToolRegistry():
    def __init__(self):
        self.tools = {}

    def register(self,name,func,description,parameters):
        if name not in self.tools:
            self.tools[name]={
                "function": func,
                "description":description,
                "parameters":parameters,
            }
        else:
            print(f"工具{name}已存在")

    def call(self,name,**kwargs):
        if name not in self.tools:
            print("工具不存在")
            raise Exception
        use_tool = self.tools[name]["function"]
        return use_tool(**kwargs)

    def get_tool_descriptions(self):
        descriptions = []
        for name, info in self.tools.items():
            desc = info["description"]
            params = info["parameters"]
            descriptions.append(f"{name}: {desc}，参数: {params}")
        return descriptions


if __name__=="__main__":
    tool_registry = ToolRegistry()
    tool_registry.register("get_price",get_crypto_price,"获得指定代币的价格数据",{"symbol": "要查询的代币，如 bitcoin、ethereum"})
    tool_registry.register("get_market",get_market_overview,"获得整个市场的相关重要数据",{})
    tool_registry.register("get_coin_detail",get_coin_market,"获得指定代币的相关market数",{"coin_id": "要查询的代币，如 bitcoin、ethereum"})
    print(tool_registry.get_tool_descriptions())
    print(tool_registry.call("get_price",symbol="bitcoin"))
