from src.rag.vector_store import VectorStore

if __name__ == "__main__":
    vs = VectorStore()
    while True:
        userinput = input("请输入要查询的query：")
        if userinput == "exit":
            print("exit\n\n")
            break
        else:
            output = vs.search(userinput)
            for i, item in enumerate(output):
                print(f"\n--- 结果 {i + 1} ---")
                print(f"来源: {item['metadata'].get('source_file', '未知')}")
                print(f"距离: {item['distance']:.4f}")
                print(f"内容: {item['text'][:150]}...")