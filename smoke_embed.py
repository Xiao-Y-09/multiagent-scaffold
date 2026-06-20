from langchain_ollama import OllamaEmbeddings

emb = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://127.0.0.1:11434",  # Windows 关键:别用 localhost(会走 IPv6 报 10049)
)
v = emb.embed_query("把这句话变成向量")
print("维度:", len(v))      # nomic-embed-text 通常是 768
print("前 5 个数:", v[:5])