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

