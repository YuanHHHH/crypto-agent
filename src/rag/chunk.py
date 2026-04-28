from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text,chunk_size=500,chunk_overlap=50):
    text_splitter =RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(text)
    return chunks

if __name__ == "__main__":
    file_path = "/Users/haoyuanhuang/PycharmProjects/crypto-agent/data/docs/bitcoin.md"
    with open(file_path,"r") as f:
        full_text = f.read()


    chunks = chunk_text(full_text)
    print(chunks)