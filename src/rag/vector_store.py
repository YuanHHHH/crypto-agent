import chromadb
import uuid
from src.rag.chunk import chunk_text
from src.rag.embed import embed,batch_embed
from src.utils.config import VECTOR_DB_DIR

class VectorStore:
    def __init__(self,persist_dir=VECTOR_DB_DIR, collection_name="crypto_docs"):
        self.client = chromadb.PersistentClient(persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)

    def add(self,texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
        if not texts:
            return
        if metadatas is None:
            metadatas = [{} for _ in texts]
        if len(metadatas) != len(texts):
            raise ValueError("metadatas 的长度必须和 texts 一致")

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        if len(ids) != len(texts):
            raise ValueError("ids 的长度必须和 texts 一致")

        embed_chunks = batch_embed(texts)

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embed_chunks,
            metadatas=metadatas,
        )


    def search(self,query:str,top_k:int=5):
        query_embed = embed(query)
        res = self.collection.query(
            query_embeddings=[query_embed],
            n_results=top_k,
            include=["documents","metadatas","distances"],
        )

        output = []
        documents = res["documents"][0]
        metadatas = res["metadatas"][0]
        distances = res["distances"][0]

        for text, metadata,distance in zip(documents,metadatas,distances):
            output.append({
                "text":text,
                "metadata":metadata,
                "distance":distance,
            })
        return output

    def count(self):
        return self.collection.count()

    def reset(self):
        all_data = self.collection.get()
        ids = all_data.get("ids",[])
        if ids:
            self.collection.delete(ids=ids)



