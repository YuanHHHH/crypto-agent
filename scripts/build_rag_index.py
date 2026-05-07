from pathlib import Path
from src.rag.chunk import chunk_text
from src.rag.vector_store import VectorStore
from src.utils.config import DOCS_DIR

vs = VectorStore()
root_dir = Path(DOCS_DIR)
allowed_suffixes = {".md"}
file_count = 0
chunk_count = 0
store_count = 0
vs.reset()
for file_path in root_dir.rglob("*"):
    if file_path.is_file() and file_path.suffix in allowed_suffixes:
        file_count +=1
        with open(file_path) as f:
            text = f.read()
            chunks = chunk_text(text)
            chunk_count += len(chunks)
            metadatas = [{"source_file":file_path.name,"chunk_index":idx} for idx in range(len(chunks))]
            vs.add(chunks,metadatas)
store_count = vs.count()
print(f"读了多少文件: {file_count}")
print(f"切了多少chunk: {chunk_count}")
print(f"入库后 count 多少: {store_count}")


