from src.rag.vector_store import VectorStore

_vs = VectorStore()

def search_knowledge_base(query:str) -> dict:

    output = _vs.search(query,3)
    results = []
    for i, item in enumerate(output):
        results.append({
            "content":item['text'][:500],
            "metadata":item['metadata']['source_file'],
        })
    return {
        "original_query":query,
        "results":results
    }

if __name__ == "__main__":
    print(search_knowledge_base("what is bitcoin"))
