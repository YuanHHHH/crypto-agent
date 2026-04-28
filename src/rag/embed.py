"""
新建 src/rag/embed.py。暴露两个函数：

embed(text: str) -> list[float]：单条文本转向量
batch_embed(texts: list[str]) -> list[list[float]]：批量转向量
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.rag.chunk import chunk_text

@lru_cache(maxsize=1)
def get_embed_model():
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return model

def embed(text):
    model = get_embed_model()
    return model.encode(text).tolist()

def batch_embed(texts):
    model = get_embed_model()
    return model.encode(texts).tolist()

if __name__ == "__main__":
    vec1 = embed("BTC")
    vec2 = embed("bitcoin")
    vec3 = embed("比特币")
    vec4 = embed("Python programming")

    print(cosine_similarity([vec1],[vec2]))
    print(cosine_similarity([vec3],[vec2]))
    print(cosine_similarity([vec1],[vec3]))
    print(cosine_similarity([vec2],[vec4]))