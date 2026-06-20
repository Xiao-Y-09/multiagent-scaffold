from langchain_chroma import Chroma
from embeddings import get_embeddings

PERSIST_DIR = "chroma_db"   # 库落盘的文件夹
COLLECTION = "knowledge_base"           # 一个 collection 相当于一张"表"

def get_vectorstore():
    """造/打开向量库;带 persist_directory 会自动持久化。"""
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIR,
    )