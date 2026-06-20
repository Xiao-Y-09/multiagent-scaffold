# embeddings.py —— 全项目统一的 embedding 入口
from langchain_ollama import OllamaEmbeddings

def get_embeddings(model: str = "nomic-embed-text"):
    """返回一个 embedding 实例。
    ingest(灌库)和 retrieval(检索)都从这里拿,保证用的是同一个模型。
    """
    return OllamaEmbeddings(
        model=model,
        base_url="http://127.0.0.1:11434",  # Windows 必须显式写,避免 IPv6 → WinError 10049
    )